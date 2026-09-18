"""Conversation and Reasoning Orchestration Service."""

import logging
import re
import time
import uuid
from typing import Any, AsyncIterator, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classifier import TaskClassifier
from app.ai.context import ContextBuilder
from app.ai.service import AIService, get_ai_service
from app.ai.types import AIRequest, ChatMessage, TaskType
from app.ai.validator import ResponseValidator
from app.core.errors import NotFoundError
from app.models.conversations import Conversation, Message
from app.models.users import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.services.memory_service import MemoryService
from app.services.personality_service import PersonalityService

logger = logging.getLogger("jenna.conversation")


class ConversationService:
    """Coordinates multi-turn reasoning, prompt context building, and conversation persistence."""

    def __init__(
        self,
        session: AsyncSession,
        ai_service: AIService | None = None,
        memory_service: MemoryService | None = None,
    ) -> None:
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)
        self.personality_service = PersonalityService(session)
        self.memory_service = memory_service or MemoryService(session)
        self.context_builder = ContextBuilder(max_messages=20)
        self.ai_service = ai_service or get_ai_service()

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Conversation]:
        """Fetch paginated conversations for a user."""
        return await self.conv_repo.list_user_conversations(user_id=user_id, limit=limit, offset=offset)

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        title: str = "New Conversation",
    ) -> Conversation:
        """Create a new conversation thread."""
        conv = await self.conv_repo.create_conversation(user_id=user_id, title=title)
        await self.session.commit()
        return conv

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Conversation:
        """Retrieve conversation with strict user ownership validation."""
        conv = await self.conv_repo.get_user_conversation(conversation_id=conversation_id, user_id=user_id)
        if not conv:
            raise NotFoundError(message=f"Conversation '{conversation_id}' not found.")
        return conv

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
    ) -> Conversation:
        """Update conversation title."""
        conv = await self.conv_repo.update_title(conversation_id=conversation_id, user_id=user_id, title=title)
        if not conv:
            raise NotFoundError(message=f"Conversation '{conversation_id}' not found.")
        await self.session.commit()
        return conv

    async def delete_conversation(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete conversation and cascade messages."""
        deleted = await self.conv_repo.delete_user_conversation(conversation_id=conversation_id, user_id=user_id)
        if not deleted:
            raise NotFoundError(message=f"Conversation '{conversation_id}' not found.")
        await self.session.commit()

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Message]:
        """Fetch conversation messages ensuring user owns the thread."""
        await self.get_conversation(conversation_id=conversation_id, user_id=user_id)
        return await self.msg_repo.list_conversation_messages(conversation_id=conversation_id, limit=limit, offset=offset)

    def _generate_smart_title(self, prompt: str) -> str:
        """Derive a friendly conversation title from initial user prompt."""
        first_line = prompt.strip().split("\n")[0].strip()
        if len(first_line) > 40:
            return first_line[:37].strip() + "..."
        return first_line or "New Conversation"

    async def _process_attachments(
        self,
        attachments: list[dict[str, Any]],
        user_id: uuid.UUID,
        prompt: str,
    ) -> list[str]:
        """Extract and structure attachment contents, invoking multimodal vision analysis for images."""
        snippets: list[str] = []
        user_obj: User | None = None

        for a in attachments:
            name = a.get("name", "attachment")
            raw_text = a.get("content") or a.get("text") or ""
            data_url = a.get("dataUrl") or ""
            a_type = a.get("type", "")

            if raw_text:
                snippets.append(f"ATTACHED FILE [{name}]:\n```\n{raw_text}\n```")
            elif data_url and (a_type.startswith("image/") or "image" in a_type):
                try:
                    import base64
                    from app.ai.vision.service import vision_service

                    if user_obj is None:
                        user_obj = await self.session.get(User, user_id)

                    if user_obj:
                        _, b64data = data_url.split(",", 1) if "," in data_url else ("", data_url)
                        img_bytes = base64.b64decode(b64data)
                        analysis = await vision_service.analyze_image(
                            image_bytes=img_bytes,
                            user=user_obj,
                            mime_type=a_type or "image/jpeg",
                            prompt=prompt or "Describe this image in detail and extract all visible text",
                        )
                        labels_str = ", ".join(analysis.labels) if analysis.labels else "None"
                        ocr_str = analysis.ocr_text if analysis.ocr_text else "None"
                        snippets.append(
                            f"ATTACHED IMAGE [{name}] VISUAL ANALYSIS:\n"
                            f"Visual Description: {analysis.description}\n"
                            f"Detected Labels: {labels_str}\n"
                            f"Extracted OCR Text: {ocr_str}"
                        )
                    else:
                        snippets.append(f"ATTACHED IMAGE [{name}] ({a_type}, size: {a.get('size', 'N/A')})")
                except Exception as img_err:
                    logger.warning("Vision analysis error in attachment: %s", img_err)
                    snippets.append(f"ATTACHED IMAGE [{name}] ({a_type}, size: {a.get('size', 'N/A')})")
            else:
                snippets.append(f"ATTACHED FILE [{name}] (size: {a.get('size', 'N/A')})")

        return snippets

    async def _handle_memory_command(self, user_id: uuid.UUID, content: str) -> str | None:
        """Recognize and execute natural-language memory management commands."""
        cleaned = content.strip().lower()

        # 1. Recall query
        recall_patterns = [
            r"^(?:what\s+(?:do\s+you\s+remember|is\s+in\s+my\s+memory|memories\s+do\s+you\s+have)|what\s+do\s+you\s+know\s+about\s+me|show\s+my\s+memories|list\s+my\s+memories)\b",
            r"\b(?:kya\s+yaad\s+hai\s+mere\s+(?:bare|baare)\s+me|kya\s+yaad\s+rakha\s+hai)\b",
        ]
        if any(re.search(p, cleaned) for p in recall_patterns):
            memories, _ = await self.memory_service.list_memories(
                user_id=user_id,
                status="ACTIVE",
                limit=15,
            )
            if not memories:
                return "I don't have any saved memories about you yet. Whenever you want me to remember a preference or fact, just tell me!"
            lines = [f"- {m.content}" for m in memories]
            return "Here is what I currently have in memory for you:\n\n" + "\n".join(lines) + "\n\nYou can view, edit, or archive any of these in your Memory tab."

        # 2. Forget query
        forget_match = re.search(
            r"^(?:please\s+)?(?:forget\s+(?:that\s+i|that|about)?|delete\s+memory\s+(?:about)?|remove\s+memory\s+(?:about)?)\s+(.+)",
            cleaned,
        )
        if forget_match:
            target = forget_match.group(1).strip().rstrip(".!?")
            if target:
                items, _ = await self.memory_service.list_memories(
                    user_id=user_id,
                    status="ACTIVE",
                    search=target,
                    limit=5,
                )
                if not items:
                    # Keyword-based search fallback
                    core_words = [
                        w for w in re.findall(r"\w+", target.lower())
                        if w not in {"i", "my", "me", "that", "the", "a", "an", "to", "prefer", "prefers", "like", "likes"}
                    ]
                    for cw in core_words:
                        if len(cw) >= 3:
                            matched, _ = await self.memory_service.list_memories(
                                user_id=user_id,
                                status="ACTIVE",
                                search=cw,
                                limit=5,
                            )
                            if matched:
                                items = matched
                                break

                if not items:
                    return f"I couldn't find an active memory matching '{target}'. You can manage all your memories directly in the Memory tab."
                if len(items) == 1:
                    target_mem = items[0]
                    await self.memory_service.delete_memory(memory_id=target_mem.id, user_id=user_id)
                    return f"I have removed that from memory: '{target_mem.content}'."
                else:
                    options = "\n".join(f"- {m.content}" for m in items[:3])
                    return f"I found multiple memories related to '{target}':\n{options}\n\nCould you clarify specifically which one you would like me to remove?"

        return None

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        model_override: str | None = None,
        provider_override: str | None = None,
        web_search: bool = False,
        deep_research: bool = False,
        attachments: list[dict[str, Any]] | None = None,
        personal_intelligence: bool = True,
        persona: str | None = None,
    ) -> tuple[Message, Message, TaskType, str, str, float]:
        """Execute synchronous reasoning pipeline:

        User Input
        -> Intent/Task Classification
        -> Context Builder (Memory + Attachments + Live Web Search)
        -> Model Router & AI Provider
        -> Response Quality Validation
        -> Persistence
        """
        conv = await self.get_conversation(conversation_id=conversation_id, user_id=user_id)

        # 1. Intent / Task & Language classification
        task_type = TaskClassifier.classify_task(content)
        detected_lang = TaskClassifier.detect_language(content)

        # 2. Persist user message with metadata
        user_msg = await self.msg_repo.create_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            metadata={
                "task_type": task_type.value,
                "detected_language": detected_lang,
                "web_search": web_search,
                "deep_research": deep_research,
                "attachments": [
                    {"name": a.get("name"), "size": a.get("size"), "type": a.get("type")}
                    for a in (attachments or [])
                ],
            },
        )


        # 3. Auto-update title if initial conversation
        if conv.title in ("New Conversation", "Untitled Conversation"):
            conv.title = self._generate_smart_title(content)
            self.session.add(conv)

        await self.session.commit()

        # 3.5 Check if user query is a natural-language memory command
        cmd_response = await self._handle_memory_command(user_id=user_id, content=content)
        if cmd_response:
            assistant_msg = await self.msg_repo.create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=cmd_response,
                model="internal",
                provider="system",
                metadata={"memory_command": True},
            )
            await self.conv_repo.touch(conversation_id)
            await self.session.commit()
            return (
                user_msg,
                assistant_msg,
                task_type,
                "system",
                "internal",
                0.0,
            )

        # 4. Build modular system instructions with user personality preferences
        builder = await self.personality_service.get_instruction_builder(user_id=user_id)
        system_instruction = builder.build_system_instruction()

        # 5. Fetch recent message window and build context
        recent_db_msgs = await self.msg_repo.get_recent_messages(conversation_id=conversation_id, limit=20)
        context = self.context_builder.build_from_db_messages(
            db_messages=recent_db_msgs,
            system_instruction=system_instruction,
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )

        # 5.5 Retrieve relevant memory context (long-term semantic + short-term working)
        if personal_intelligence:
            try:
                context.long_term_memory = await self.memory_service.get_relevant_context(
                    user_id=user_id,
                    query=content,
                    conversation_id=conversation_id,
                    limit=5,
                )
            except Exception as exc:
                logger.warning("Failed to retrieve memory context: %s", exc)
        else:
            context.long_term_memory = ""

        # 5.6 Inject file attachments context (Files, Photos & Camera with Vision/OCR)
        if attachments:
            att_snippets = await self._process_attachments(attachments, user_id, content)
            if att_snippets:
                context.short_term_memory.append("\n\n".join(att_snippets))

        # 5.65 Continuous Ambient Live Screen Vision
        try:
            state_file = Path("/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/logs/live_screen_state.json")
            if state_file.exists():
                import json
                with open(state_file, "r", encoding="utf-8") as f:
                    live_vis = json.load(f)
                if live_vis and live_vis.get("description"):
                    pkg = live_vis.get("focused_package", "Unknown")
                    is_floating = live_vis.get("is_floating_window_active", False)
                    desc = live_vis.get("description", "")
                    screen_block = (
                        "<live_ambient_screen_vision>\n"
                        f"[CURRENT REAL-TIME SCREEN PERCEPTION]:\n"
                        f"- Active App: {pkg} ({'Vivo Small Window' if is_floating else 'Fullscreen'})\n"
                        f"- What is currently visible on phone screen: {desc}\n"
                        "[CRITICAL INSTRUCTION: You ALREADY have continuous ambient live vision of the user's screen. "
                        "When the user asks what they are doing, watching, reading, or what video is playing, answer IMMEDIATELY "
                        "with natural, loving awareness without saying 'wait', without executing terminal commands, and without any delay!]\n"
                        "</live_ambient_screen_vision>"
                    )
                    context.short_term_memory.append(screen_block)
        except Exception as vis_err:
            logger.debug("Ambient vision injection skipped: %s", vis_err)

        # 5.66 Persistent Visual Recall Cortex Memory Timeline
        try:
            from app.ai.vision.visual_cortex import visual_recall_cortex
            timeline_prompt = visual_recall_cortex.get_ambient_context_prompt(max_events=8)
            if timeline_prompt:
                context.short_term_memory.append(timeline_prompt)
        except Exception as cx_err:
            logger.debug("Visual recall cortex injection skipped: %s", cx_err)

        # 5.7 Augment with Live Web Search / Deep Research if enabled
        if web_search or deep_research:
            try:
                from app.ai.tools.web.researcher import ResearchPipeline, ResearchRequest
                researcher = ResearchPipeline()
                r_req = ResearchRequest(
                    query=content,
                    max_sources=5 if deep_research else 3,
                )
                r_res = await researcher.execute_research(r_req)
                if r_res and r_res.sources:
                    sources_summary = "\n".join(
                        f"[{s.citation_index}] {s.title} ({s.url}):\n{s.snippet}"
                        for s in r_res.sources
                    )
                    context.short_term_memory.append(web_block)
            except Exception as exc:
                logger.warning("Web search pipeline execution warning in send_message: %s", exc)

        # 5.8 Autonomous Antigravity Execution (Fast Direct Command Lane + Multi-step Tool Loop)
        from app.services.termux_service import termux_service
        direct_cmd = termux_service.detect_command_intent(content)
        is_anti_active = bool(
            direct_cmd
            or (persona and any(k in persona.lower() for k in ("anti", "antigravity", "termux")))
            or any(k in content.lower() for k in ("anti", "antigravity", "termux", "run:", "bash:", "git", "npm", "run karo", "fix karo", "code karo", "test karo", "build karo", "point", "annotate", "highlight", "spotlight", "fable", "astra", "subagent", "task manager", "cron", "schedule"))
            or content.strip().startswith("/")
        )

        if direct_cmd:
            try:
                start_time = time.monotonic()
                cmd_res = await termux_service.execute_command(direct_cmd)
                stdout = cmd_res.get("stdout", "").strip()
                stderr = cmd_res.get("stderr", "").strip()
                exit_code = cmd_res.get("exit_code", 0)

                clean_cmd = direct_cmd.split("||")[0].strip() if "||" in direct_cmd else direct_cmd
                terminal_block = f"```bash\n{clean_cmd}\n{out_display}\n```\n\n"

                ai_explanation = ""
                try:
                    from app.ai.providers.gemini_provider import GeminiProvider

                    provider = GeminiProvider()
                    if provider.is_available:
                        summary_prompt = (
                            "You are Jenna, an affectionate, highly capable female companion and partner in Termux.\n"
                            f"User prompt: '{content}'.\n"
                            f"Executed Termux command: '{direct_cmd}' (Exit code: {exit_code}).\n"
                            f"Command Output:\n{out_display[:1200]}\n\n"
                            "INSTRUCTIONS:\n"
                            "- Speak as a caring, smart female companion (Jenna) in warm, natural Hindi / Hinglish ('baby', 'meri jaan').\n"
                            "- STRICT INVARIANT: NEVER call the user 'bhai', 'bro', 'brother', or 'sir'. Speak to them affectionately as their partner.\n"
                            "- Summarize the key findings clearly and warmly in 2-3 sentences.\n"
                            "- DO NOT repeat the raw bash block or table since the user already sees the terminal box above.\n"
                            "- Ask what to do next with sweet companion care."
                        )
                        req = AIRequest(
                            messages=[ChatMessage(role="user", content=summary_prompt)],
                            model="gemini-3.5-flash-lite",
                            task_type=TaskType.CHAT,
                            max_tokens=250,
                            temperature=0.2,
                        )
                        res = await provider.generate(req)
                        ai_explanation = res.text.strip()
                except Exception as exp_err:
                    logger.warning("AI explanation error in direct lane: %s", exp_err)
                    ai_explanation = f"Command `{direct_cmd}` executed successfully."

                full_text = terminal_block + ai_explanation
                latency = round((time.monotonic() - start_time) * 1000, 2)

                assistant_msg = await self.msg_repo.create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_text,
                    model="gemini-3.5-flash-lite",
                    provider="termux-direct",
                    metadata={
                        "task_type": task_type.value,
                        "latency_ms": latency,
                        "agent": "antigravity",
                        "command": direct_cmd,
                        "exit_code": exit_code,
                    },
                )
                await self.conv_repo.touch(conversation_id)
                await self.session.commit()
                return user_msg, assistant_msg, task_type, "termux-direct", "gemini-3.5-flash-lite", latency
            except Exception as exc:
                logger.warning(f"Error in fast direct command lane in send_message: {exc}", exc_info=True)

        elif is_anti_active:
            try:
                from app.services.antigravity_agent import antigravity_agent
                start_time = time.monotonic()
                accumulated_parts: list[str] = []
                history = [
                    {"role": "user" if m.role == "user" else "assistant", "content": m.content}
                    for m in context.messages[-6:]
                ]
                pref_model = None
                max_iter = 8
                agent_content = content
                if content.strip().startswith("/goal"):
                    max_iter = 15
                    agent_content = f"[Autonomous Long-Horizon Goal Mode Activated]: {content.strip()[5:].strip()}"
                elif content.strip().startswith("/plan"):
                    agent_content = f"[Structured Architectural Planning Blueprint]: {content.strip()[5:].strip()}"
                elif content.strip().startswith("/boost"):
                    pref_model = "claude-fable-5.1"
                    agent_content = f"[Boost High-Reasoning Mode]: {content.strip()[6:].strip()}"
                elif "fable" in content.lower():
                    pref_model = "claude-fable-5.1"
                elif "astra" in content.lower():
                    pref_model = "gpt-6-astra"

                async for event in antigravity_agent.run_agent_loop(agent_content, history, max_iterations=max_iter, preferred_model=pref_model):
                    if event.get("type") == "stream.delta":
                        accumulated_parts.append(event.get("delta", ""))
                    elif event.get("type") == "agent.final_response":
                        accumulated_parts.append(event.get("content", ""))

                final_content = "".join(accumulated_parts)
                if final_content:
                    latency = round((time.monotonic() - start_time) * 1000, 2)
                    final_text = ResponseValidator.sanitize(final_content) or final_content
                    assistant_msg = await self.msg_repo.create_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=final_text,
                        model="gemini-3.5-flash",
                        provider="gemini",
                        metadata={"task_type": task_type.value, "latency_ms": latency, "agent": "antigravity"},
                    )
                    await self.conv_repo.touch(conversation_id)
                    await self.session.commit()
                    return user_msg, assistant_msg, task_type, "gemini", "gemini-3.5-flash", latency
            except Exception as exc:
                logger.warning(f"Antigravity agent loop error in send_message: {exc}", exc_info=True)

        effective_system_instruction = context.compile_system_instruction() or system_instruction
        if persona:
            effective_system_instruction = f"<persona_directive>\n{persona}\n</persona_directive>\n\n{effective_system_instruction}"


        # 6. Build AI completion request
        ai_request = AIRequest(
            messages=context.messages,
            system_instruction=effective_system_instruction,
            model=model_override,
            provider=provider_override,
            task_type=task_type,
            metadata={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "detected_language": detected_lang,
            },
        )

        # 7. Execute AI generation
        ai_response = await self.ai_service.generate(ai_request)

        # 8. Response quality validation & sanitization
        is_valid, validation_err = ResponseValidator.validate(ai_response.text)
        if not is_valid:
            logger.warning("Response failed validation: %s", validation_err)
            final_text = (
                "I apologize, but I had trouble formulating that response clearly. "
                "Could you please ask again or rephrase?"
            )
        else:
            final_text = ResponseValidator.sanitize(ai_response.text)

        # 9. Persist assistant message
        assistant_msg = await self.msg_repo.create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=final_text,
            model=ai_response.model,
            provider=ai_response.provider,
            metadata={
                "task_type": task_type.value,
                "latency_ms": ai_response.latency_ms,
                "usage": ai_response.usage.model_dump(),
                "validation_passed": is_valid,
                "validation_error": validation_err,
            },
        )

        # 10. Touch conversation updated_at
        await self.conv_repo.touch(conversation_id)
        await self.session.commit()

        # 11. Post-response automatic candidate memory extraction
        if personal_intelligence:
            try:
                await self.memory_service.process_conversation_memories(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=content,
                    assistant_response=final_text,
                )
            except Exception as exc:
                logger.warning("Automatic memory pipeline error: %s", exc)

        return (
            user_msg,
            assistant_msg,
            task_type,
            ai_response.provider,
            ai_response.model,
            ai_response.latency_ms,
        )

    async def stream_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        model_override: str | None = None,
        provider_override: str | None = None,
        web_search: bool = False,
        deep_research: bool = False,
        attachments: list[dict[str, Any]] | None = None,
        personal_intelligence: bool = True,
        persona: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute real-time streaming reasoning pipeline and persist final assistant message."""
        conv = await self.get_conversation(conversation_id=conversation_id, user_id=user_id)

        # 1. Intent / Task & Language classification
        task_type = TaskClassifier.classify_task(content)
        detected_lang = TaskClassifier.detect_language(content)

        # 2. Persist user message immediately
        user_msg = await self.msg_repo.create_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            metadata={
                "task_type": task_type.value,
                "detected_language": detected_lang,
                "web_search": web_search,
                "deep_research": deep_research,
                "attachments": [
                    {"name": a.get("name"), "size": a.get("size"), "type": a.get("type")}
                    for a in (attachments or [])
                ],
            },
        )

        # 3. Auto-update title if initial conversation
        if conv.title in ("New Conversation", "Untitled Conversation"):
            conv.title = self._generate_smart_title(content)
            self.session.add(conv)

        await self.session.commit()

        # 4. Build modular system instructions with user personality preferences
        builder = await self.personality_service.get_instruction_builder(user_id=user_id)
        system_instruction = builder.build_system_instruction()

        # 5. Fetch recent message window and build context
        recent_db_msgs = await self.msg_repo.get_recent_messages(conversation_id=conversation_id, limit=20)
        context = self.context_builder.build_from_db_messages(
            db_messages=recent_db_msgs,
            system_instruction=system_instruction,
            user_id=str(user_id),
            conversation_id=str(conversation_id),
        )

        # 5.5 Retrieve relevant memory context (long-term semantic + short-term working)
        if personal_intelligence:
            try:
                context.long_term_memory = await self.memory_service.get_relevant_context(
                    user_id=user_id,
                    query=content,
                    conversation_id=conversation_id,
                    limit=5,
                )
            except Exception as exc:
                logger.warning("Failed to retrieve memory context for streaming: %s", exc)
        else:
            context.long_term_memory = ""

        # 5.6 Inject file attachments context (Files, Photos & Camera with Vision/OCR)
        if attachments:
            att_snippets = await self._process_attachments(attachments, user_id, content)
            if att_snippets:
                context.short_term_memory.append("\n\n".join(att_snippets))

        # 5.65 Continuous Ambient Live Screen Vision
        try:
            state_file = Path("/storage/emulated/0/Download/TermuxWorkspace/projects/Antigravity-project/jenna/logs/live_screen_state.json")
            if state_file.exists():
                import json
                with open(state_file, "r", encoding="utf-8") as f:
                    live_vis = json.load(f)
                if live_vis and live_vis.get("description"):
                    pkg = live_vis.get("focused_package", "Unknown")
                    is_floating = live_vis.get("is_floating_window_active", False)
                    desc = live_vis.get("description", "")
                    screen_block = (
                        "<live_ambient_screen_vision>\n"
                        f"[CURRENT REAL-TIME SCREEN PERCEPTION]:\n"
                        f"- Active App: {pkg} ({'Vivo Small Window' if is_floating else 'Fullscreen'})\n"
                        f"- What is currently visible on phone screen: {desc}\n"
                        "[CRITICAL INSTRUCTION: You ALREADY have continuous ambient live vision of the user's screen. "
                        "When the user asks what they are doing, watching, reading, or what video is playing, answer IMMEDIATELY "
                        "with natural, loving awareness without saying 'wait', without executing terminal commands, and without any delay!]\n"
                        "</live_ambient_screen_vision>"
                    )
                    context.short_term_memory.append(screen_block)
        except Exception as vis_err:
            logger.debug("Ambient vision injection skipped in stream: %s", vis_err)

        # 5.66 Persistent Visual Recall Cortex Memory Timeline
        try:
            from app.ai.vision.visual_cortex import visual_recall_cortex
            timeline_prompt = visual_recall_cortex.get_ambient_context_prompt(max_events=8)
            if timeline_prompt:
                context.short_term_memory.append(timeline_prompt)
        except Exception as cx_err:
            logger.debug("Visual recall cortex injection skipped in stream: %s", cx_err)

        # 5.7 Augment with Live Web Search / Deep Research if enabled
        if web_search or deep_research:
            try:
                from app.ai.tools.web.researcher import ResearchPipeline, ResearchRequest
                researcher = ResearchPipeline()
                r_req = ResearchRequest(
                    query=content,
                    max_sources=5 if deep_research else 3,
                )
                r_res = await researcher.execute_research(r_req)
                if r_res and r_res.sources:
                    sources_summary = "\n".join(
                        f"[{s.citation_index}] {s.title} ({s.url}):\n{s.snippet}"
                        for s in r_res.sources
                    )
                    web_block = (
                        f"<live_web_search_results query=\"{content}\">\n"
                        f"{sources_summary}\n"
                        f"</live_web_search_results>\n"
                        f"INSTRUCTION: Cite specific sources using [1], [2] bracket notation corresponding to the results above."
                    )
                    context.short_term_memory.append(web_block)
                    yield {
                        "type": "stream.tool_call",
                        "tool": "deep_research" if deep_research else "web_search",
                        "sources_count": len(r_res.sources),
                        "status": "completed",
                    }
            except Exception as exc:
                logger.warning("Web search pipeline execution warning in stream_message: %s", exc)

        # 5.8 Autonomous Antigravity Execution (Fast Direct Command Lane + Multi-step Tool Loop)
        from app.services.termux_service import termux_service
        direct_cmd = termux_service.detect_command_intent(content)
        is_anti_active = bool(
            direct_cmd
            or (persona and any(k in persona.lower() for k in ("anti", "antigravity", "termux")))
            or any(k in content.lower() for k in ("anti", "antigravity", "termux", "run:", "bash:", "git", "npm", "run karo", "fix karo", "code karo", "test karo", "build karo", "point", "annotate", "highlight", "spotlight", "fable", "astra", "subagent", "task manager", "cron", "schedule"))
            or content.strip().startswith("/")
        )

        if direct_cmd:
            try:
                start_time = time.monotonic()
                yield {
                    "type": "stream.started",
                    "provider": "termux",
                    "model": "bash-direct",
                    "user_message_id": str(user_msg.id),
                    "conversation_id": str(conversation_id),
                    "task_type": task_type.value,
                }

                # 1. Execute Termux command immediately (~20-80ms)
                cmd_res = await termux_service.execute_command(direct_cmd)
                stdout = cmd_res.get("stdout", "").strip()
                stderr = cmd_res.get("stderr", "").strip()
                exit_code = cmd_res.get("exit_code", 0)

                clean_cmd = direct_cmd.split("||")[0].strip() if "||" in direct_cmd else direct_cmd
                terminal_block = f"```bash\n{clean_cmd}\n{out_display}\n```\n\n"

                # 2. Immediately stream the raw bash terminal block! User sees it in ~100ms!
                yield {"type": "stream.delta", "delta": terminal_block}

                # 2.5 Multimodal Camera Vision Integration
                vision_summary = ""
                if "jenna_camera_snap.jpg" in direct_cmd:
                    snap_path = Path("/storage/emulated/0/Download/jenna_camera_snap.jpg")
                    if snap_path.exists() and snap_path.stat().st_size > 500:
                        try:
                            from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
                            g_vis = GeminiVisionProvider()
                            res_vis = await g_vis.analyze_image(
                                snap_path.read_bytes(),
                                mime_type="image/jpeg",
                                prompt="You are Jenna, an affectionate female partner looking at this photo from your phone camera. Describe what you see with warmth and charm in 2-3 sweet sentences in Hinglish. Strictly never say bhai or bro.",
                            )
                            if res_vis and res_vis.description:
                                vision_summary = f"\n\n📸 **Jenna Vision Insight:**\n{res_vis.description}\n\n"
                                yield {"type": "stream.delta", "delta": vision_summary}
                        except Exception as v_err:
                            logger.warning("Camera snapshot vision analysis error: %s", v_err)

                # 3. Stream quick 1-turn Hinglish explanation
                ai_explanation = ""
                try:
                    from app.ai.providers.gemini_provider import GeminiProvider

                    provider = GeminiProvider()
                    if provider.is_available:
                        summary_prompt = (
                            "You are Jenna, an affectionate, highly capable female companion and partner in Termux.\n"
                            f"User prompt: '{content}'.\n"
                            f"Executed Termux command: '{direct_cmd}' (Exit code: {exit_code}).\n"
                            f"Command Output:\n{out_display[:1200]}\n\n"
                            "INSTRUCTIONS:\n"
                            "- Speak as a caring, smart female companion (Jenna) in warm, natural Hindi / Hinglish.\n"
                            "- STRICT INVARIANT: NEVER call the user 'bhai', 'bro', 'brother', or 'sir'. Speak to them affectionately as their partner.\n"
                            "- Summarize the key findings clearly and warmly in 2-3 sentences.\n"
                            "- DO NOT repeat the raw bash block or table since the user already sees the terminal box above.\n"
                            "- Ask what to do next with sweet companion care."
                        )
                        req = AIRequest(
                            messages=[ChatMessage(role="user", content=summary_prompt)],
                            model="gemini-3.5-flash-lite",
                            task_type=TaskType.CHAT,
                            max_tokens=250,
                            temperature=0.2,
                        )
                        async for chunk in provider.stream(req):
                            if chunk.delta:
                                ai_explanation += chunk.delta
                                yield {"type": "stream.delta", "delta": chunk.delta}
                except Exception as exp_err:
                    logger.warning("AI explanation error in direct lane: %s", exp_err)
                    if not ai_explanation:
                        ai_explanation = f"Command `{direct_cmd}` executed successfully."
                        yield {"type": "stream.delta", "delta": ai_explanation}

                full_text = terminal_block + (vision_summary if vision_summary else "") + ai_explanation
                latency = round((time.monotonic() - start_time) * 1000, 2)

                assistant_msg = await self.msg_repo.create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_text,
                    model="gemini-3.5-flash-lite",
                    provider="termux-direct",
                    metadata={
                        "task_type": task_type.value,
                        "latency_ms": latency,
                        "agent": "antigravity",
                        "command": direct_cmd,
                        "exit_code": exit_code,
                    },
                )
                await self.conv_repo.touch(conversation_id)
                await self.session.commit()

                yield {
                    "type": "stream.completed",
                    "full_text": full_text,
                    "latency_ms": latency,
                    "conversation_id": str(conversation_id),
                    "message_id": str(assistant_msg.id),
                }
                return
            except Exception as exc:
                logger.warning(f"Error in fast direct command lane: {exc}", exc_info=True)

        elif is_anti_active:
            try:
                from app.services.antigravity_agent import antigravity_agent
                yield {
                    "type": "stream.started",
                    "provider": "gemini",
                    "model": "gemini-3.5-flash",
                    "user_message_id": str(user_msg.id),
                    "conversation_id": str(conversation_id),
                    "task_type": task_type.value,
                }

                accumulated_text = ""
                start_time = time.monotonic()
                history = [
                    {"role": "user" if m.role == "user" else "assistant", "content": m.content}
                    for m in context.messages[-6:]
                ]

                pref_model = None
                max_iter = 8
                agent_content = content
                if content.strip().startswith("/goal"):
                    max_iter = 15
                    agent_content = f"[Autonomous Long-Horizon Goal Mode Activated]: {content.strip()[5:].strip()}"
                elif content.strip().startswith("/plan"):
                    agent_content = f"[Structured Architectural Planning Blueprint]: {content.strip()[5:].strip()}"
                elif content.strip().startswith("/boost"):
                    pref_model = "claude-fable-5.1"
                    agent_content = f"[Boost High-Reasoning Mode]: {content.strip()[6:].strip()}"
                elif "fable" in content.lower():
                    pref_model = "claude-fable-5.1"
                elif "astra" in content.lower():
                    pref_model = "gpt-6-astra"

                async for event in antigravity_agent.run_agent_loop(agent_content, history, max_iterations=max_iter, preferred_model=pref_model):
                    evt_type = event.get("type")
                    if evt_type == "stream.tool_call":
                        yield event
                    elif evt_type == "stream.delta":
                        d = event.get("delta", "")
                        if d:
                            yield event
                            accumulated_text += d
                    elif evt_type == "agent.thought":
                        th = event.get("thought", "")
                        if th:
                            yield {"type": "stream.delta", "delta": f"> *{th}*\n\n"}
                            accumulated_text += f"> *{th}*\n\n"
                    elif evt_type == "agent.final_response":
                        resp_text = event.get("content", "")
                        yield {"type": "stream.delta", "delta": resp_text}
                        accumulated_text += resp_text

                latency = round((time.monotonic() - start_time) * 1000, 2)
                final_text = ResponseValidator.sanitize(accumulated_text) or accumulated_text or "Task completed."

                assistant_msg = await self.msg_repo.create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=final_text,
                    model="gemini-3.5-flash",
                    provider="gemini",
                    metadata={
                        "task_type": task_type.value,
                        "latency_ms": latency,
                        "agent": "antigravity",
                    },
                )
                await self.conv_repo.touch(conversation_id)
                await self.session.commit()

                yield {
                    "type": "stream.completed",
                    "full_text": final_text,
                    "latency_ms": latency,
                    "conversation_id": str(conversation_id),
                    "message_id": str(assistant_msg.id),
                }
                return
            except Exception as exc:
                logger.warning(f"Antigravity agent loop error in stream_message: {exc}", exc_info=True)

        effective_system_instruction = context.compile_system_instruction() or system_instruction
        if persona:
            effective_system_instruction = f"<persona_directive>\n{persona}\n</persona_directive>\n\n{effective_system_instruction}"


        # 6. Build AI streaming request
        ai_request = AIRequest(
            messages=context.messages,
            system_instruction=effective_system_instruction,
            model=model_override,
            provider=provider_override,
            task_type=task_type,
            metadata={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "user_message_id": str(user_msg.id),
                "detected_language": detected_lang,
            },
        )

        accumulated_chunks: list[str] = []
        active_provider: str = ""
        active_model: str = ""
        stream_latency_ms: float = 0.0

        try:
            async for event in self.ai_service.stream(ai_request):
                evt_type = event.get("type")

                if evt_type == "stream.started":
                    active_provider = event.get("provider", "")
                    active_model = event.get("model", "")
                    # Enrich with user message metadata
                    event["user_message_id"] = str(user_msg.id)
                    event["conversation_id"] = str(conversation_id)
                    event["task_type"] = task_type.value
                    yield event

                elif evt_type == "stream.delta":
                    delta = event.get("delta", "")
                    accumulated_chunks.append(delta)
                    yield event

                elif evt_type == "stream.completed":
                    full_text = event.get("full_text") or "".join(accumulated_chunks)
                    stream_latency_ms = event.get("latency_ms", 0.0)

                    # Validate response quality
                    is_valid, validation_err = ResponseValidator.validate(full_text)
                    if not is_valid:
                        final_text = (
                            "I apologize, but I had trouble formulating that response clearly. "
                            "Could you please ask again or rephrase?"
                        )
                    else:
                        final_text = ResponseValidator.sanitize(full_text)

                    # Persist assistant message to database
                    assistant_msg = await self.msg_repo.create_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=final_text,
                        model=active_model,
                        provider=active_provider,
                        metadata={
                            "task_type": task_type.value,
                            "latency_ms": stream_latency_ms,
                            "usage": event.get("usage", {}),
                            "validation_passed": is_valid,
                            "validation_error": validation_err,
                        },
                    )
                    await self.conv_repo.touch(conversation_id)
                    await self.session.commit()

                    # Trigger automatic memory candidate extraction
                    if personal_intelligence:
                        try:
                            await self.memory_service.process_conversation_memories(
                                user_id=user_id,
                                conversation_id=conversation_id,
                                user_message=content,
                                assistant_response=final_text,
                            )
                        except Exception as exc:
                            logger.warning("Automatic memory pipeline error during stream: %s", exc)

                    # Enrich stream.completed event with database IDs
                    event["message_id"] = str(assistant_msg.id)
                    event["conversation_id"] = str(conversation_id)
                    yield event

                elif evt_type == "stream.error":
                    yield event

        except Exception as exc:
            logger.error("Streaming reasoning failed: %s", exc)
            yield {
                "type": "stream.error",
                "request_id": ai_request.request_id,
                "error_code": type(exc).__name__,
                "message": str(exc),
            }

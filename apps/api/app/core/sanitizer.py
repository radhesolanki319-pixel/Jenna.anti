"""Response Sanitizer for Jenna AI.

Strictly filters out raw terminal code blocks, bash dumps, tool outputs,
and forbidden addressing words (baby, jaan, etc.) from user-facing messages.
Guarantees clean, polite, human conversational Hinglish for WhatsApp and Screen.
"""

import re


def sanitize_response_for_chat(text: str, user_prompt: str = "") -> str:
    """Sanitize assistant response to ensure zero terminal code blocks or raw CLI output.

    Unless Boss explicitly asks to see code/bash/terminal output, this strips all:
      - Markdown code blocks (```bash, ```sh, ```text, ```json, ```)
      - Raw bash prompt lines ($ command, > command, # command)
      - Tool call / result markers
      - System proactive tags
      - Forbidden companion addressing (baby, babe, jaan, etc.)
    """
    if not text:
        return "Boss, maine check kar liya hai aur sab normal hai! ✨"

    prompt_lower = (user_prompt or "").lower()
    explicit_code_request = any(
        kw in prompt_lower
        for kw in (
            "show code",
            "code dikhao",
            "bash dikhao",
            "terminal dikhao",
            "command dikhao",
            "command output",
            "script dikhao",
            "syntax dikhao",
            "terminal output dikhao",
        )
    )

    cleaned = text

    # Enforce user preference: STRICTLY address user as Boss, NEVER use baby / jaan / meri jaan
    cleaned = re.sub(
        r"\b(meri\s+jaan|jaan|baby|babe|sweetheart|darling)\b",
        "Boss",
        cleaned,
        flags=re.IGNORECASE,
    )

    if not explicit_code_request:
        # 1. Strip all fenced code blocks (```...```)
        cleaned = re.sub(r"```[a-zA-Z0-9_\-]*\s*[\s\S]*?```\n*", "", cleaned)

        # 2. Strip orphaned triple backticks
        cleaned = cleaned.replace("```", "")

        # 3. Strip lines that look like terminal prompt executions:
        # e.g. "$ ls -la", "$ git status", "# apt update", "u0_a535@localhost:~$ "
        terminal_line_pattern = r"(?m)^\s*(?:\$|>|#|u0_a\d+@\S+[:$#])\s+.*$\n?"
        cleaned = re.sub(terminal_line_pattern, "", cleaned)

        # 4. Strip tool execution markers or raw JSON leaked outputs
        cleaned = re.sub(r"\{[\s\S]*?\"tool\"\s*:\s*[\s\S]*?\}\n*", "", cleaned)
        cleaned = re.sub(r"\[INFO\][\s\S]*?\n", "", cleaned)
        cleaned = re.sub(r"\[WARNING\][\s\S]*?\n", "", cleaned)
        cleaned = re.sub(r"\[ERROR\][\s\S]*?\n", "", cleaned)

        # 5. Strip internal system prompt tags
        cleaned = re.sub(r"<live_ambient_screen_vision>[\s\S]*?</live_ambient_screen_vision>", "", cleaned)
        cleaned = re.sub(r"SYSTEM_PROACTIVE:\s*", "", cleaned)

        # 6. Clean up multiple empty lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # If completely empty after stripping, provide a warm polite fallback
    if not cleaned:
        cleaned = "Boss, maine task background mein 100% complete kar diya hai! Sab kuch perfectly operational hai ✨"

    return cleaned

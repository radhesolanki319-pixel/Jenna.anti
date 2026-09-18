"""Task Classification and Intent Detection Engine for user prompts."""

import re
from app.ai.types import TaskType


class TaskClassifier:
    """Classifies user queries into discrete TaskType categories for intelligent model routing."""

    # Heuristic regex patterns for task classification
    CODING_PATTERNS = re.compile(
        r"(\b(code|function|def |class |import |const |let |var |bug|error|stack trace|refactor|debug|compile|syntax|endpoint|api|python|javascript|typescript|sql|html|css|bash|repo|git)\b|"
        r"```|"
        r"mujhe ye code samjha|code likho|code fix|error aa raha hai)",
        re.IGNORECASE,
    )

    REASONING_PATTERNS = re.compile(
        r"(\b(reason|logic|puzzle|math|calculate|derive|prove|deduce|tradeoff|pros and cons|step by step|architecture design|why does|explain why)\b|"
        r"kya lagta hai|soch kar batao|kaise kaam karta hai)",
        re.IGNORECASE,
    )

    ANALYSIS_PATTERNS = re.compile(
        r"(\b(analyze|analysis|compare|contrast|benchmark|metrics|data points|breakdown|evaluate|audit|investigate)\b|"
        r"dono me kya antar hai|tulna karo|review karo)",
        re.IGNORECASE,
    )

    RESEARCH_PATTERNS = re.compile(
        r"(\b(research|look up|find information|search for|who was|history of|latest news|deep dive on)\b|"
        r"ke baare me batao|pata lagao)",
        re.IGNORECASE,
    )

    TOOL_REQUEST_PATTERNS = re.compile(
        r"(\b(remind me|set a reminder|schedule|timer|turn on|turn off|send email|send message|open the app|file check karo)\b|"
        r"kal mujhe yaad dilana|yaad dilana|alarm lagao|ye file check karo)",
        re.IGNORECASE,
    )

    # Language detection patterns
    HINDI_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
    HINGLISH_KEYWORDS = re.compile(
        r"\b(kya|kaise|kyun|kyu|hai|hain|ho|tha|the|thi|hoga|karo|batao|samjha|mujhe|mera|meri|mere|aap|tum|hum|kal|aaj|parso|accha|theek|sahi|nahi|nahin|bhi|aur|lekin|dost|bhai|yaar)\b",
        re.IGNORECASE,
    )

    @classmethod
    def classify_task(cls, text: str) -> TaskType:
        """Classify user prompt into optimal TaskType."""
        clean = text.strip()
        if not clean:
            return TaskType.CHAT

        # Check tool / action request first
        if cls.TOOL_REQUEST_PATTERNS.search(clean):
            return TaskType.TOOL_REQUEST

        # Check coding / technical queries
        if cls.CODING_PATTERNS.search(clean):
            return TaskType.CODING

        # Check research
        if cls.RESEARCH_PATTERNS.search(clean):
            return TaskType.RESEARCH

        # Check analysis
        if cls.ANALYSIS_PATTERNS.search(clean):
            return TaskType.ANALYSIS

        # Check deep reasoning
        if cls.REASONING_PATTERNS.search(clean):
            return TaskType.REASONING

        # Default conversational chat
        return TaskType.CHAT

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect dominant linguistic style: 'hi' (Devanagari), 'hinglish', or 'en'."""
        if cls.HINDI_DEVANAGARI.search(text):
            return "hi"

        hinglish_matches = len(cls.HINGLISH_KEYWORDS.findall(text))
        words = text.split()
        if words and (hinglish_matches >= 2 or (len(words) <= 4 and hinglish_matches >= 1)):
            return "hinglish"

        return "en"

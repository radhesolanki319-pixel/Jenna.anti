"""Zero-Amnesia Context Engine for Jenna AI.

Conforms to GPT-6 Astra specifications:
- Eliminates logic loops and repetitive failures during high-context sessions.
- Preserves codebase symbol maps, active files, and architectural decisions.
- Maintains execution continuity across deep multi-turn sessions.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any


@dataclass
class CodebaseDecision:
    """A durable architectural or implementation decision made during a session."""
    topic: str
    decision: str
    rationale: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SymbolTrackingRecord:
    """Tracks active classes, functions, or file paths in the active context."""
    file_path: str
    symbols: list[str] = field(default_factory=list)
    last_modified: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ZeroAmnesiaEngine:
    """Context preservation and anti-loop watchdog engine.

    Maintains active session memory of:
    - Active files and key symbols
    - Pinned architectural decisions
    - Recent output hashes to prevent cyclical reasoning loops
    """

    def __init__(self, max_history_hashes: int = 15) -> None:
        self.decisions: list[CodebaseDecision] = []
        self.symbols: dict[str, SymbolTrackingRecord] = {}
        self.recent_output_hashes: deque[str] = deque(maxlen=max_history_hashes)
        self.loop_count: int = 0

    def record_decision(self, topic: str, decision: str, rationale: str = "") -> None:
        """Record an architectural decision to avoid re-debating or forgetting."""
        self.decisions.append(
            CodebaseDecision(topic=topic, decision=decision, rationale=rationale)
        )

    def track_symbols(self, file_path: str, symbols: list[str]) -> None:
        """Register or update active symbols being modified in a file."""
        self.symbols[file_path] = SymbolTrackingRecord(file_path=file_path, symbols=symbols)

    def check_loop(self, output_snippet: str) -> bool:
        """Detect if the model is trapped in a repetitive reasoning or code generation loop."""
        norm = "".join(output_snippet.split()).lower()
        if len(norm) < 15:
            return False


        h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if h in self.recent_output_hashes:
            self.loop_count += 1
            return True

        self.recent_output_hashes.append(h)
        self.loop_count = max(0, self.loop_count - 1)
        return False

    def build_context_block(self) -> str | None:
        """Generate a compact Zero-Amnesia context block for prompt injection."""
        sections: list[str] = []

        if self.symbols:
            sym_lines = [
                f"  - `{path}`: {', '.join(record.symbols)}"
                for path, record in self.symbols.items()
            ]
            sections.append("ACTIVE CODEBASE SYMBOLS & FILES:\n" + "\n".join(sym_lines))

        if self.decisions:
            dec_lines = [
                f"  - [{d.topic}]: {d.decision} (Rationale: {d.rationale})"
                for d in self.decisions[-8:]
            ]
            sections.append("PINNED ARCHITECTURAL DECISIONS:\n" + "\n".join(dec_lines))

        if self.loop_count >= 1:
            sections.append(
                "CRITICAL ANTI-LOOP WATCHDOG DIRECTIVE:\n"
                "A potential repetitive logic pattern has been detected. Do NOT repeat previous code or "
                "rationale. Pivot to a simplified, first-principles alternative solution immediately."
            )

        if not sections:
            return None

        return "<zero_amnesia_engine>\n" + "\n\n".join(sections) + "\n</zero_amnesia_engine>"

    def reset_watchdog(self) -> None:
        """Reset the loop watchdog counter."""
        self.loop_count = 0
        self.recent_output_hashes.clear()

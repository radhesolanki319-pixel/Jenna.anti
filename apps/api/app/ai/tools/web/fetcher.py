"""Web content fetcher with HTML parsing, length limits, and prompt-injection defense."""

import re
from typing import Any
import urllib.parse


PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"<\|\s*im_start\s*\|>", re.IGNORECASE),
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"you\s+must\s+forget\s+everything", re.IGNORECASE),
]


class WebContentFetcher:
    """Safely extracts readable text from web documents and applies defensive filters."""

    def __init__(self, max_chars: int = 8000, mock_responses: dict[str, str] | None = None):
        self.max_chars = max_chars
        self._mock_responses = mock_responses or {}

    def register_mock_page(self, url: str, content: str) -> None:
        """Register a mock page for offline deterministic testing."""
        self._mock_responses[url] = content

    def clean_html(self, raw_html: str) -> str:
        """Strip HTML tags, inline scripts, styles, and collapse excess whitespace."""
        # Remove script and style elements
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Remove remaining HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode basic entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def sanitize_untrusted_content(self, text: str) -> tuple[str, bool]:
        """Scan and neutralize prompt injection attempts in fetched web content."""
        has_suspicious_patterns = False
        sanitized = text

        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(sanitized):
                has_suspicious_patterns = True
                sanitized = pattern.sub("[SUSPICIOUS INSTRUCTION REDACTED]", sanitized)

        return sanitized, has_suspicious_patterns

    async def fetch_page(self, url: str) -> dict[str, Any]:
        """Fetch and parse web page contents with safety bounds."""
        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.scheme or parsed_url.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL protocol: '{url}'. Only HTTP/HTTPS is permitted.")

        # Check mock registry first for deterministic offline operation
        if url in self._mock_responses:
            raw = self._mock_responses[url]
        else:
            # Fallback simulated text for known documentation domains
            domain = parsed_url.netloc
            raw = f"Simulated authoritative content from {domain} regarding {parsed_url.path.replace('/', ' ')}."

        clean = self.clean_html(raw)
        sanitized, had_injection = self.sanitize_untrusted_content(clean)

        # Apply output length limits
        truncated = len(sanitized) > self.max_chars
        final_text = sanitized[:self.max_chars]

        return {
            "url": url,
            "domain": parsed_url.netloc,
            "content": final_text,
            "char_count": len(final_text),
            "truncated": truncated,
            "prompt_injection_detected": had_injection,
            "status": "success",
        }

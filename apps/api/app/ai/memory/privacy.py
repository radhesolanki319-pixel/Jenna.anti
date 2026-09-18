"""Privacy and sensitive information protection filter for memory subsystem."""

import re
from typing import NamedTuple
from app.schemas.memory import SensitivityClassification


class PrivacyCheckResult(NamedTuple):
    """Outcome of sensitivity inspection."""

    is_sensitive: bool
    classification: SensitivityClassification
    reasons: list[str]
    detected_categories: list[str]


class PrivacyFilter:
    """Detects credentials, API keys, passwords, financial data, and private secrets.

    Security Rule: DEFAULT ACTION = DO NOT STORE.
    Sensitive content must never be persisted as long-term memory, logged, or placed in audit metadata.
    """

    # Compiled regex patterns for high-risk sensitive patterns
    PATTERNS = [
        # API Keys & Tokens
        (
            "openai_api_key",
            re.compile(r"\bsk-[a-zA-Z0-9_\-]{20,}\b", re.IGNORECASE),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "google_api_key",
            re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "aws_access_key",
            re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "github_token",
            re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "jwt_token",
            re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b"),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "bearer_token",
            re.compile(r"\bbearer\s+[a-zA-Z0-9_\-\.]{20,}\b", re.IGNORECASE),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "generic_api_key",
            re.compile(
                r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)[\s:=\"']+([a-zA-Z0-9_\-]{16,})",
                re.IGNORECASE,
            ),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        # Passwords & Secrets
        (
            "password_pattern",
            re.compile(
                r"\b(?:password|passwd|pwd|passphrase|secret)(?:\s+is|\s*[:=\"'])\s*[^\s,;\"']{3,}",
                re.IGNORECASE,
            ),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "private_key",
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        # Financial Data
        (
            "credit_card",
            re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b"),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "cvv",
            re.compile(r"\b(?:cvv|cvc|security code)[\s:=\"']+\d{3,4}\b", re.IGNORECASE),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        (
            "bank_account",
            re.compile(r"\b(?:iban|account number|routing number)[\s:=\"']+[a-zA-Z0-9]{8,34}\b", re.IGNORECASE),
            SensitivityClassification.SENSITIVE_CREDENTIAL,
        ),
        # Security Answers & Personal Credentials
        (
            "security_answer",
            re.compile(
                r"\b(?:security question|security answer|mother's maiden name|mothers maiden name)[\s:=\"']+.+",
                re.IGNORECASE,
            ),
            SensitivityClassification.SENSITIVE_PERSONAL,
        ),
    ]

    # Keyword triggers that signal sensitive credential intent
    SENSITIVE_KEYWORDS = {
        "password",
        "passphrase",
        "master password",
        "root password",
        "database password",
        "wifi password",
        "api key",
        "secret key",
        "private key",
        "seed phrase",
        "mnemonic phrase",
        "recovery phrase",
        "ssh key",
        "pin number",
        "ssn",
        "social security number",
        "credit card",
    }

    @classmethod
    def check_text(cls, text: str) -> PrivacyCheckResult:
        """Analyze text for sensitive information.

        Returns a PrivacyCheckResult detailing sensitivity and detected categories.
        """
        if not text or not text.strip():
            return PrivacyCheckResult(
                is_sensitive=False,
                classification=SensitivityClassification.SAFE,
                reasons=[],
                detected_categories=[],
            )

        detected_categories: list[str] = []
        reasons: list[str] = []
        highest_class = SensitivityClassification.SAFE

        # 1. Check regex patterns
        for cat_name, pattern, classification in cls.PATTERNS:
            if pattern.search(text):
                detected_categories.append(cat_name)
                reasons.append(f"Matched pattern for {cat_name}")
                if classification == SensitivityClassification.SENSITIVE_CREDENTIAL:
                    highest_class = SensitivityClassification.SENSITIVE_CREDENTIAL
                elif highest_class == SensitivityClassification.SAFE:
                    highest_class = classification

        # 2. Check keyword triggers
        lower_text = text.lower()
        for kw in cls.SENSITIVE_KEYWORDS:
            if kw in lower_text:
                detected_categories.append(f"keyword_{kw.replace(' ', '_')}")
                reasons.append(f"Contained sensitive keyword '{kw}'")
                highest_class = SensitivityClassification.SENSITIVE_CREDENTIAL

        is_sensitive = len(detected_categories) > 0
        return PrivacyCheckResult(
            is_sensitive=is_sensitive,
            classification=highest_class,
            reasons=reasons,
            detected_categories=detected_categories,
        )

    @classmethod
    def is_safe_to_store(cls, text: str) -> bool:
        """Convenience method returning True only if text is completely safe to persist."""
        result = cls.check_text(text)
        return not result.is_sensitive

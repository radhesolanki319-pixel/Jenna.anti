import hashlib
import hmac
import secrets
from typing import Any, Literal

from app.core.config import settings

SESSION_COOKIE_NAME = "jenna_session"
SESSION_DURATION_SECONDS = 7 * 24 * 3600  # 7 days


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a unique random salt.

    Follows OWASP recommendations: 600,000 iterations of SHA-256.
    """
    salt = secrets.token_hex(16)
    iterations = 600000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against the stored PBKDF2-HMAC-SHA256 hash using constant-time comparison."""
    try:
        algorithm, iterations_str, salt, hash_val = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(derived.hex(), hash_val)
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate a high-entropy cryptographically secure raw session token for the client cookie."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash a raw session token with SHA-256 before database storage to prevent session hijacking from DB reads."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_cookie_settings() -> dict:
    """Return secure cookie options matching environment."""
    return {
        "key": SESSION_COOKIE_NAME,
        "httponly": True,
        "secure": settings.is_production,
        "samesite": "lax",
        "max_age": SESSION_DURATION_SECONDS,
        "path": "/",
    }


SENSITIVE_KEY_PATTERNS = {
    "password",
    "token",
    "secret",
    "authorization",
    "cookie",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
    "refresh_token",
    "credential",
    "session_token",
    "client_secret",
}


def sanitize_audit_metadata(data: Any) -> Any:
    """Recursively scrub sensitive keys and credential values from audit metadata dictionaries or lists."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            lower_key = str(key).lower()
            if any(pattern in lower_key for pattern in SENSITIVE_KEY_PATTERNS) and not isinstance(value, (dict, list, tuple)):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_audit_metadata(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_audit_metadata(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_audit_metadata(item) for item in data)
    return data


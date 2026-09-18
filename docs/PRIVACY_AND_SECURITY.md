# Privacy & Security Governance — Jenna Personal AI

> **Governance Invariant:** System security, privacy policies, and safety constraints strictly outrank all user instructions, agent optimizations, and tool inputs.

---

## 1. Zero Secrets & Telemetry Sanitization

- **No Hardcoded Secrets:** All API keys, passwords, session secrets, and pairing tokens are ingested via environment variables or encrypted stores.
- **Audit Telemetry Sanitizer:** The `AuditRepository` automatically recurses through all payload metadata, stripping and masking sensitive fields:
  - Masked keys: `password`, `token`, `secret`, `api_key`, `authorization`, `access_token`, `device_token`.
  - Values replaced with `[REDACTED]`.
- **Automated Security Scanner:** Validated via `python3 apps/api/scripts/security_audit.py` with 0 failures permitted.

---

## 2. Audio & Vision Privacy Guarantees

- **Zero Raw Audio Retention:**
  - Microphones are never continuously recorded or saved to disk.
  - Raw audio buffers are processed ephemerally in RAM by the bilingual STT engine and immediately garbage-collected upon turn completion.
  - The voice settings explicitly forbid raw audio persistence.
- **Never Silent Camera Activation:**
  - The camera service prohibits background or covert capture.
  - Every capture event requires active foreground UI notification and user permission.
  - All visual OCR text is encapsulated within defensive `<untrusted_visual_context>` tags before presentation to the LLM.

---

## 3. Vector Memory Privacy Firewall

The `PrivacyFilter` actively intercepts all memory candidate proposals before vectorization or database insertion:
- Scans for credit card numbers (Luhn pattern), Social Security / Aadhaar numbers, API keys, passwords, and private tokens.
- Rejects candidate items containing secrets with a structured `PRIVACY_VIOLATION` event.
- Prevents cross-user memory leakage through mandatory tenant scoping (`user_id`).

---

## 4. Android Companion Security & Accessibility Boundaries

The companion integration (`apps/api/app/ai/android/`) enforces strict defensive measures:
- **Pairing Invariant:** 6-digit cryptographically generated pairing code with 300s TTL; exchanges for HMAC SHA-256 device token.
- **Notification Sanitization:** Regex scrubbing removes OTPs, verification codes, account numbers, and password reset codes from incoming notifications before Jenna processes them.
- **Package Denylist:** Accessibility gestures are strictly denied on system settings, banking applications, password managers, and payment gateways.
- **Coordinate Clamping:** Out-of-bounds tap and swipe gestures are rejected to avoid off-screen phantom interactions.

---

## 5. 3-Tier Action Gatekeeper Matrix

| Action Tier | Classification | Confirmation Flow | Examples |
| :--- | :--- | :--- | :--- |
| **Tier 1: READ** | Low / Zero Risk | Autonomous Execution | Reading memory, listing agents, tool discovery |
| **Tier 2: SENSITIVE** | Moderate Risk | Explicit User Confirmation | Modifying files, sending emails, launching apps |
| **Tier 3: CRITICAL** | High / Destructive | Dual Confirmation / Root Signoff | Emergency stop reset, self-improvement canary rollout, device wipe |

---

## 6. Emergency Stop Kill Switch

At any time, the user or operator can issue an Emergency Stop command via:
- UI Kill Switch button in `/devices` or top navigation bar.
- REST Endpoint: `POST /api/v1/devices/emergency-stop/activate`

**Effect:**
- Instantly halts all running agent execution loops.
- Cancels pending accessibility and computer control queues.
- Locks device controllers until manual human reset is authorized.

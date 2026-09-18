# Disaster Recovery & Backup Runbook — Jenna Personal AI

> **Status:** Active & Verified (Part 11 Disaster Recovery Engine)

---

## 1. Backup Architecture & Snapshot Strategy

Jenna features an automated, zero-downtime snapshot and disaster recovery subsystem implemented in `app.core.backup_restore.BackupManager`:

- **Storage Location:** `apps/api/backups/`
- **Format:** JSON Snapshot with SHA-256 cryptographic verification checksum.
- **Snapshot Contents:**
  - Database schema & version metadata
  - Users & session credentials (passwords pre-hashed with PBKDF2)
  - Long-term intelligent memory items & vector embedding representations
  - Agent task histories & step traces
  - System settings and user preferences
  - Audit event telemetry

---

## 2. Generating a Disaster Recovery Snapshot

### Via Production REST API:
```bash
curl -X POST http://localhost:8000/api/v1/production/backup \
  -H "Content-Type: application/json" \
  -d '{"description": "Pre-upgrade release snapshot"}'
```

Response:
```json
{
  "status": "SUCCESS",
  "snapshot_id": "backup_20260913_134037_3a8078",
  "created_at": "2026-09-13T13:40:37.892011Z",
  "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "tables": ["users", "sessions", "memory_items", "agent_tasks", "system_settings", "audit_events"],
  "total_records": 128
}
```

### Listing Snapshots:
```bash
curl http://localhost:8000/api/v1/production/backups
```

---

## 3. Cryptographic Integrity & Restoration Runbook

Every backup manifest generates a SHA-256 hash over its serialized payload. Prior to restoration, the engine recalculates the hash:

1. **Integrity Check:** If the calculated checksum does not match the manifest header, the restoration is aborted immediately with `ChecksumMismatchError`.
2. **Schema Compatibility Verification:** Ensures all foreign key constraints and model schemas align with the running migration head.
3. **Atomic Transaction Replay:** Restores entities inside an isolated transaction; rolling back fully if any constraint violation occurs.

---

## 4. Controlled Self-Improvement Rollback Runbook

If an autonomous self-improvement candidate deployed to canary introduces latency regressions, error spikes, or behavioral degradation:

1. **Trigger Rollback via API:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/improvement/proposals/{proposal_id}/rollback \
     -H "Content-Type: application/json" \
     -d '{"reason": "Canary error threshold breached (>2%)"}'
   ```
2. **Immediate Traffic Draining:** The router resets canary traffic weight to 0%, reverting all user traffic instantly to the stable baseline model.
3. **Audit Logging:** Emits an immutable `IMPROVEMENT_ROLLBACK` event to `audit_events` with detailed rationale and snapshot state.

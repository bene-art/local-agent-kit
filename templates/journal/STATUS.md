# STATUS — journal

**State:** blocked
**Blockers:**
  1. Persistent memory layer (owned by the memory track).
  2. Privacy audit — verify zero-network during a session and full local encryption.
**Owner:** memory track + kit
**Unblock condition:** memory track ships a local-encrypted store; an audit script confirms no outbound network traffic during a `lak bot templates/journal` session.

## What is built
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY rules prioritize asking-over-telling and refuse unprompted analysis.

## What is NOT built
- Persistent cross-session memory.
- Local encryption at rest.
- The audit script that verifies no network calls.

## Acceptance criteria for unblock
- A second session opened by the same user gets context from prior entries via memory recall, NOT via plaintext file replay.
- Audit script run during a session reports zero outbound network packets.
- Eval suite passes against `gemma4:e4b` on the "do not analyze" and "do not advise" cases.
- Docs include a "what touches disk" page.

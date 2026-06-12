# STATUS — journal

**State:** primitive ready; privacy hardening pending
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY rules prioritize asking-over-telling and refuse unprompted analysis.
- `SQLiteMemory` (`local_agent_kit.memory.SQLiteMemory`) — local SQLite-
  backed, per-thread history with pruning. 9 tests covering the contract.

## What runs today

A journal session that persists across restarts can be built with:

```python
from local_agent_kit.agent import Agent
from local_agent_kit.memory import SQLiteMemory

agent = Agent.from_directory("templates/journal")
mem = SQLiteMemory("./journal.db")

# Per-turn:
#   mem.append("default", "user", user_input)
#   prior = mem.history("default", limit=20)
#   response = await agent.handle(...)   # caller seeds prior context if desired
#   mem.append("default", "assistant", response)
```

A canonical `run_journal.py` runner like the interviewer's is not yet
shipped — it's the next layer of work on this template.

## Remaining blockers for "ready" status

1. **Encryption at rest.** SQLiteMemory writes plaintext rows. The
   IDENTITY's privacy promise ("everything you read stays on this
   machine") is satisfied locally, but a stolen laptop / shared
   machine would expose entries. Options:
   - Wrap the DB in macOS Keychain-protected file or `sqlcipher`
     (new dep).
   - Document the limit honestly and let users opt into FileVault.
2. **Audit script.** Confirms zero outbound network traffic during a
   `lak bot templates/journal` session. Hasn't been written.
3. **A `run_journal.py`** that wires Agent + SQLiteMemory together
   so users don't have to write Python to use the template.

## Acceptance for shipping publicly
- Encryption decision made (sqlcipher dep, or honest "use FileVault" doc).
- Audit script run + result published in template README.
- `run_journal.py` ships and is documented.

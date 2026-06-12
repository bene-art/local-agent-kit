# STATUS — journal

**State:** ready (with explicit privacy caveats)
**Last verified:** 2026-06-12

## What ships
- `agent.yaml`, `identity/IDENTITY.md`, `README.md`, eval cases.
- IDENTITY prioritizes asking over telling, refuses unprompted analysis.
- `SQLiteMemory` (`local_agent_kit.memory.SQLiteMemory`) for cross-
  session persistence, 9 tests.
- `run_journal.py` — runner that wires Agent + SQLiteMemory, restores
  prior context on each launch, persists user/assistant pairs as you go.

## Run it

```bash
python -m templates.journal.run_journal \
    --agent-dir templates/journal \
    --db        ./journal.db
```

Sessions resume where you left off — each launch reloads the last N
entries from the SQLite file into the agent's in-session history.

## Privacy posture — read this before journaling anything sensitive

This template's IDENTITY says "everything you read stays on this machine."
That's true at the *network* level — the agent never makes outbound
calls during a session (no search provider, no Telegram, no cloud).

It is **not** true at the *disk* level unless you take an action:

- The SQLite file (`./journal.db` by default) stores entries in plaintext.
- A stolen laptop, a shared machine login, or a snapshot backup exposes
  the contents.

**The kit's decision on encryption:** ship the honest doc rather than
add a `sqlcipher` dependency without operator approval. Two ways to get
encryption-at-rest:

1. **OS-level (recommended for most users)** — enable FileVault (macOS)
   or LUKS (Linux). The journal file inherits whole-disk encryption.
2. **Application-level** — write your own backend implementing the
   `Memory` Protocol (`local_agent_kit.memory.Memory`) that wraps
   reads/writes with a cipher of your choosing. Swap it in
   `run_journal.py` where `SQLiteMemory` is constructed.

## Outstanding (not yet built)
- An audit script that verifies zero outbound network packets during a
  journal session. Manual verification (`lsof`, `tcpdump`) until then.
- A `MemoryEncrypted` reference implementation, if/when `sqlcipher` is
  approved as a dependency.

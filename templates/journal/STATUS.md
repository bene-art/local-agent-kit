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

## Verifying the "zero outbound" claim

Two layers ship:

1. **pytest test** (`tests/test_journal_privacy.py`) — monkeypatches
   `aiohttp.ClientSession.post`, runs one `Agent.handle` turn from the
   journal template, fails CI if any non-localhost URL is requested.
   Also asserts `search.provider == "none"`, `web_search == False`, and
   `file_read_roots == []` in the agent.yaml. Locks in the contract.

2. **Runtime audit** (`templates/journal/audit.py`) — wraps
   `run_journal.py` under `lsof` monitoring; reports any non-local
   ESTABLISHED TCP connection observed during the session. Use when
   you want manual verification beyond the unit test:

       python -m templates.journal.audit \
           --agent-dir templates/journal \
           --db ./journal.db

## Outstanding (not yet built)
- A `MemoryEncrypted` reference implementation, if/when `sqlcipher` is
  approved as a dependency.

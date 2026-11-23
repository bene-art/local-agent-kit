"""Runner for the journal template.

Wires the Agent + SQLiteMemory so each turn persists across sessions.
Per turn: read input → seed prior context into the agent → handle → store
both sides → print. The next session continues where you left off.

Privacy posture (read the STATUS doc first):
    - All entries live in the SQLite file on this machine.
    - The file is NOT encrypted at rest by this runner. Use FileVault
      (macOS) or your OS-level disk encryption. The IDENTITY's privacy
      promise is "stays on this machine" — encryption is your OS's job,
      not the kit's, unless you wrap SQLiteMemory in an encrypted backend
      yourself.

Run from the kit root:

    python -m templates.journal.run_journal \
        --agent-dir templates/journal \
        --db        ./journal.db
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from local_agent_kit.agent import Agent
from local_agent_kit.memory import SQLiteMemory


THREAD_ID = "journal"


async def run(agent_dir: Path, db_path: Path) -> None:
    agent = Agent.from_directory(agent_dir)
    mem = SQLiteMemory(db_path)

    # Seed prior context into the agent's in-session history so the model
    # has continuity. SQLiteMemory.history() returns oldest-first which
    # matches Agent._history's expected order.
    prior = mem.history(THREAD_ID, limit=agent.config.memory_max_history)
    if prior:
        agent._history = prior
        print(f"(loaded {len(prior)} entries from prior sessions)\n")

    print("Journal open. Press Ctrl-D when you're done.\n")
    try:
        while True:
            try:
                entry = input("> ")
            except EOFError:
                print()
                break
            if not entry.strip():
                continue

            mem.append(THREAD_ID, "user", entry)
            response = await agent.handle(entry)
            mem.append(THREAD_ID, "assistant", response)
            print(f"\n{response}\n")
    finally:
        if agent._session and not agent._session.closed:
            await agent._session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the journal template with persistent memory.")
    parser.add_argument("--agent-dir", required=True, type=Path, help="Agent directory")
    parser.add_argument("--db", default=Path("./journal.db"), type=Path, help="SQLite memory file")
    args = parser.parse_args()
    try:
        asyncio.run(run(args.agent_dir, args.db))
    except KeyboardInterrupt:
        print("\nClosed.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

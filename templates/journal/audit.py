"""Runtime audit for the journal template's "zero outbound, non-localhost" promise.

Spawns `run_journal.py` as a subprocess and watches its open sockets via
`lsof -i -P -n -p <pid>` every two seconds. Any ESTABLISHED TCP connection
whose peer is NOT 127.0.0.1, ::1, or localhost prints a WARNING to stderr.

Use this when you want runtime verification (above the pytest test, which
mocks the network). The session is interactive — you still journal
normally — and the watcher runs alongside, surfacing offenders if any.

Run from the kit root:

    python -m templates.journal.audit \
        --agent-dir templates/journal \
        --db ./journal.db

Hit Ctrl-D in the journal prompt (not Ctrl-C — that kills the watcher
too).
"""
from __future__ import annotations

import argparse
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

LOCAL_PATTERNS = ("127.0.0.1", "localhost", "[::1]", "::1")


def is_local(line: str) -> bool:
    return any(p in line for p in LOCAL_PATTERNS)


def lsof_lines(pid: int) -> list[str]:
    if shutil.which("lsof") is None:
        return []
    out = subprocess.run(
        ["lsof", "-i", "-P", "-n", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    return [ln for ln in out.stdout.splitlines() if "ESTABLISHED" in ln]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit run_journal.py for non-local network activity.")
    parser.add_argument("--agent-dir", required=True, type=Path)
    parser.add_argument("--db", default=Path("./journal.db"), type=Path)
    parser.add_argument("--poll", default=2.0, type=float, help="Seconds between lsof checks.")
    args = parser.parse_args()

    if shutil.which("lsof") is None:
        print("audit: lsof not on PATH — install it or run under a system that ships it.", file=sys.stderr)
        return 2

    cmd = [
        sys.executable,
        "-m", "templates.journal.run_journal",
        "--agent-dir", str(args.agent_dir),
        "--db", str(args.db),
    ]
    print(f"audit: launching {' '.join(cmd)}", file=sys.stderr)
    proc = subprocess.Popen(cmd)

    seen_offenders: set[str] = set()
    try:
        while proc.poll() is None:
            time.sleep(args.poll)
            for line in lsof_lines(proc.pid):
                if is_local(line):
                    continue
                if line in seen_offenders:
                    continue
                seen_offenders.add(line)
                print(f"audit: NON-LOCAL CONNECTION → {line}", file=sys.stderr)
        proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        proc.wait()

    if seen_offenders:
        print(f"audit: FAILED — {len(seen_offenders)} non-local connection(s) observed.", file=sys.stderr)
        return 1
    print("audit: clean — no non-local connections observed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pre-commit gate: block files containing private vocabulary.

The blocklist is stored as salted SHA-256 digests, not plaintext — a
tracked guard file that enumerates the very terms it suppresses would
itself be a leak. Each candidate token in a scanned file is hashed the
same way and compared against the digest set.

Exit 1 (with file:line and a masked preview) on any hit; exit 0 clean.
Usage: vocab_scrub.py FILE [FILE ...]   (pre-commit passes filenames)
"""
from __future__ import annotations

import hashlib
import re
import sys

_SALT = "local-agent-kit-vocab-v1"

# sha256(salt + lowercased_token) for each blocked term. These are
# one-way digests of the blocklist, not credentials.
_BLOCKED_DIGESTS = {
    "533f28ba408fdbe83dd9ff0e805dd7fd71d4f1f06ecd4342613c090047fe2edd",  # pragma: allowlist secret
    "0f262ea40f7b025ed0712ab5108a1eb4b5c8bc9d49241d22a4eb4526e6a21dc8",  # pragma: allowlist secret
    "e87f81aad6ebc2c4c9539613d0d314f8fb46d308a4999d9ee26bb2f74a298e03",  # pragma: allowlist secret
    "b2294d1ee6e6c77fe74f723b04c76310b3a81326e8511858a98a3c9abba506ae",  # pragma: allowlist secret
    "8509e8478b8c1e87367553a8f294f1b1ea4fb083f0731234aa52983e05a34734",  # pragma: allowlist secret
    "e34f901cc5659d89c26315bee60ad887632ac87500f2b434d79be1976d477574",  # pragma: allowlist secret
    "1938a326c6de088ffa2ad5d86078b82911b41dca799477eaef2cc1039c59d5de",  # pragma: allowlist secret
}

_SCAN_SUFFIXES = (
    ".py", ".md", ".yaml", ".yml", ".toml", ".json", ".jsonl",
    ".sh", ".txt", ".cfg", ".ini",
)

# Words are runs of letters/digits — "com.benai.foo" and "BenAi_local"
# both tokenize so the parts are checked individually.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _digest(token: str) -> str:
    return hashlib.sha256((_SALT + token.lower()).encode()).hexdigest()


def _mask(token: str) -> str:
    return token[0] + "*" * (len(token) - 1)


def scan_file(path: str) -> list[str]:
    hits: list[str] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                for token in _TOKEN_RE.findall(line):
                    if _digest(token) in _BLOCKED_DIGESTS:
                        hits.append(f"{path}:{lineno}: blocked term {_mask(token)}")
    except OSError as exc:
        hits.append(f"{path}: unreadable ({exc})")
    return hits


def main(argv: list[str]) -> int:
    hits: list[str] = []
    for path in argv:
        if path.endswith(_SCAN_SUFFIXES) and not path.endswith("vocab_scrub.py"):
            hits.extend(scan_file(path))
    if hits:
        print("Private vocabulary found:")
        print("\n".join(hits))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

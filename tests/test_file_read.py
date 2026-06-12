"""Tests for the file_read tool."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.tools.file_read import file_read, list_files


@pytest.mark.asyncio
async def test_reads_file_in_allowed_root(tmp_path: Path):
    f = tmp_path / "note.md"
    f.write_text("hello")
    out = await file_read(str(f), allowed_roots=[tmp_path])
    assert out == "hello"


@pytest.mark.asyncio
async def test_denies_file_outside_allowlist(tmp_path: Path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    inside_root = tmp_path / "allowed"
    inside_root.mkdir()
    out = await file_read(str(outside), allowed_roots=[inside_root])
    assert out.startswith("[access denied:")


@pytest.mark.asyncio
async def test_blocks_secret_name_patterns(tmp_path: Path):
    f = tmp_path / "api_key.txt"
    f.write_text("AKIAxxx")
    out = await file_read(str(f), allowed_roots=[tmp_path])
    assert out.startswith("[access denied:")


@pytest.mark.asyncio
async def test_blocks_env_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("API_KEY=xxx")
    out = await file_read(str(f), allowed_roots=[tmp_path])
    assert out.startswith("[access denied:")


@pytest.mark.asyncio
async def test_truncates_long_content(tmp_path: Path):
    f = tmp_path / "big.txt"
    f.write_text("x" * 5000)
    out = await file_read(str(f), allowed_roots=[tmp_path], max_chars=100)
    assert out.startswith("x" * 100)
    assert "truncated at 100" in out


@pytest.mark.asyncio
async def test_file_not_found(tmp_path: Path):
    out = await file_read(str(tmp_path / "missing.txt"), allowed_roots=[tmp_path])
    assert out.startswith("[file not found:")


@pytest.mark.asyncio
async def test_disabled_with_empty_allowlist(tmp_path: Path):
    f = tmp_path / "note.md"
    f.write_text("hello")
    out = await file_read(str(f), allowed_roots=[])
    assert "disabled" in out


@pytest.mark.asyncio
async def test_prefix_collision_does_not_grant_access(tmp_path: Path):
    """`/foo` allowlisted must not grant access to `/foobar/...`."""
    allowed = tmp_path / "notes"
    allowed.mkdir()
    sibling = tmp_path / "notes_secret"
    sibling.mkdir()
    target = sibling / "leak.txt"
    target.write_text("secret")
    out = await file_read(str(target), allowed_roots=[allowed])
    assert out.startswith("[access denied:")


@pytest.mark.asyncio
async def test_list_files_returns_sorted_entries(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    out = await list_files(str(tmp_path), allowed_roots=[tmp_path])
    assert "a.txt" in out
    assert "b.txt" in out


@pytest.mark.asyncio
async def test_list_files_blocks_outside_allowlist(tmp_path: Path):
    inside = tmp_path / "ok"
    inside.mkdir()
    outside = tmp_path / "denied"
    outside.mkdir()
    out = await list_files(str(outside), allowed_roots=[inside])
    assert out.startswith("[access denied:")

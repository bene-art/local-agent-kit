"""Tests for the data_query tool."""
from __future__ import annotations

from pathlib import Path

import pytest

from local_agent_kit.tools.data_query import data_query


@pytest.fixture
def sales_csv(tmp_path: Path) -> Path:
    f = tmp_path / "sales.csv"
    f.write_text("region,revenue\nNorth,100\nSouth,80\nNorth,50\nEast,120\n")
    return f


@pytest.fixture
def events_jsonl(tmp_path: Path) -> Path:
    f = tmp_path / "events.jsonl"
    f.write_text(
        '{"id": 1, "type": "click", "user": "a"}\n'
        '{"id": 2, "type": "view", "user": "b"}\n'
        '{"id": 3, "type": "click", "user": "a"}\n'
    )
    return f


@pytest.mark.asyncio
async def test_csv_groupby_sum(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv),
        "SELECT region, SUM(CAST(revenue AS INTEGER)) AS total FROM data GROUP BY region ORDER BY region",
        allowed_roots=[tmp_path],
    )
    assert "region | total" in out
    assert "North | 150" in out
    assert "South | 80" in out
    assert "East | 120" in out


@pytest.mark.asyncio
async def test_jsonl_count_by_type(events_jsonl: Path, tmp_path: Path):
    out = await data_query(
        str(events_jsonl),
        "SELECT type, COUNT(*) AS n FROM data GROUP BY type",
        allowed_roots=[tmp_path],
    )
    assert "click | 2" in out
    assert "view | 1" in out


@pytest.mark.asyncio
async def test_rejects_non_select(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv), "DELETE FROM data", allowed_roots=[tmp_path]
    )
    assert out.startswith("[query blocked")


@pytest.mark.asyncio
async def test_rejects_select_with_blocked_keyword(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv),
        "SELECT * FROM data; DROP TABLE data",
        allowed_roots=[tmp_path],
    )
    assert out.startswith("[query blocked")


@pytest.mark.asyncio
async def test_column_names_containing_keywords_are_allowed(tmp_path: Path):
    # Regression: substring matching blocked SELECT created_at (CREATE),
    # last_updated (UPDATE), deleted (DELETE) — any dataset with timestamp
    # columns was unusable. Keywords must match as whole words only.
    f = tmp_path / "rows.csv"
    f.write_text(
        "created_at,last_updated,deleted\n"
        "2026-01-01,2026-01-02,0\n"
        "2026-02-01,2026-02-02,1\n"
    )
    out = await data_query(
        str(f),
        "SELECT created_at, last_updated FROM data WHERE deleted = 0",
        allowed_roots=[tmp_path],
    )
    assert not out.startswith("[query blocked")
    assert "2026-01-01" in out


@pytest.mark.asyncio
async def test_bare_blocked_keyword_still_blocked(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv),
        "SELECT * FROM data WHERE region IN (SELECT region FROM data); DELETE FROM data",
        allowed_roots=[tmp_path],
    )
    assert out.startswith("[query blocked")


@pytest.mark.asyncio
async def test_path_outside_allowlist_denied(sales_csv: Path, tmp_path: Path):
    elsewhere = tmp_path / "other"
    elsewhere.mkdir()
    out = await data_query(
        str(sales_csv),
        "SELECT * FROM data",
        allowed_roots=[elsewhere],
    )
    assert out.startswith("[access denied:")


@pytest.mark.asyncio
async def test_unsupported_file_type(tmp_path: Path):
    f = tmp_path / "notes.txt"
    f.write_text("not data")
    out = await data_query(str(f), "SELECT * FROM data", allowed_roots=[tmp_path])
    assert out.startswith("[unsupported file type:")


@pytest.mark.asyncio
async def test_empty_allowlist_disables(sales_csv: Path):
    out = await data_query(str(sales_csv), "SELECT * FROM data", allowed_roots=[])
    assert "disabled" in out


@pytest.mark.asyncio
async def test_max_rows_cap(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv),
        "SELECT region, revenue FROM data",
        allowed_roots=[tmp_path],
        max_rows=2,
    )
    assert "capped at 2 rows" in out


@pytest.mark.asyncio
async def test_no_results(sales_csv: Path, tmp_path: Path):
    out = await data_query(
        str(sales_csv),
        "SELECT * FROM data WHERE region = 'Nowhere'",
        allowed_roots=[tmp_path],
    )
    assert out == "[no results]"

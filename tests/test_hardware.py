"""Smoke tests for hardware detection."""
from __future__ import annotations

from local_agent_kit.hardware import (
    HardwareInfo,
    ModelRecommendation,
    detect_hardware,
    format_hardware_report,
    recommend_model,
)


def test_detect_hardware_returns_hardware_info():
    hw = detect_hardware()
    assert isinstance(hw, HardwareInfo)
    assert hw.os in {"darwin", "linux", "windows"}
    # RAM detection may fail on exotic CI images; allow zero but don't crash.
    assert hw.ram_gb >= 0


def test_recommend_model_returns_valid_recommendation():
    hw = HardwareInfo(ram_gb=16, chip="Apple M4", os="darwin", gpu="Apple M4", unified_memory=True)
    rec = recommend_model(hw)
    assert isinstance(rec, ModelRecommendation)
    assert rec.model.startswith("gemma") or rec.model.startswith("llama")
    assert rec.size_gb > 0


def test_recommend_model_scales_with_ram():
    low = recommend_model(HardwareInfo(ram_gb=8, chip="?", os="darwin", gpu="?", unified_memory=True))
    mid = recommend_model(HardwareInfo(ram_gb=16, chip="?", os="darwin", gpu="?", unified_memory=True))
    high = recommend_model(HardwareInfo(ram_gb=64, chip="?", os="darwin", gpu="?", unified_memory=True))
    # Bigger machines should not get a smaller-size model recommendation.
    assert mid.size_gb >= low.size_gb
    assert high.size_gb >= mid.size_gb


def test_format_hardware_report_is_human_readable():
    hw = HardwareInfo(ram_gb=24, chip="Apple M4 Pro", os="darwin", gpu="Apple M4 Pro", unified_memory=True)
    rec = recommend_model(hw)
    report = format_hardware_report(hw, rec)
    assert "Apple M4 Pro" in report
    assert "24" in report
    assert rec.model in report

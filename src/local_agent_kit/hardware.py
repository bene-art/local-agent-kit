"""Hardware detection — detect system capabilities and recommend models.

Uses sysctl on macOS, /proc on Linux. Returns structured info about
RAM, CPU/GPU, and the best Ollama model for the hardware.

Usage:
    from local_agent_kit.hardware import detect_hardware, recommend_model

    hw = detect_hardware()
    print(hw)  # HardwareInfo(ram_gb=16, chip="Apple M4", os="darwin")

    model = recommend_model(hw)
    print(model)  # ModelRecommendation(model="gemma3:12b", size_gb=8.1, ...)
"""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass


@dataclass
class HardwareInfo:
    ram_gb: int
    chip: str
    os: str
    gpu: str
    unified_memory: bool


@dataclass
class ModelRecommendation:
    model: str
    display_name: str
    size_gb: float
    expected_tokens_per_sec: str
    notes: str


# ── Model recommendation table ───────────────────────────────────────
# Based on Q4 quantization. Models must fit in RAM with room for OS + tools.

MODEL_TABLE: list[tuple[int, ModelRecommendation]] = [
    (8, ModelRecommendation(
        model="gemma3:4b",
        display_name="Gemma 3 4B",
        size_gb=3.3,
        expected_tokens_per_sec="~30-40",
        notes="Minimal. Good for testing. Limited conversation quality.",
    )),
    (16, ModelRecommendation(
        model="gemma3:12b",
        display_name="Gemma 3 12B",
        size_gb=8.1,
        expected_tokens_per_sec="~15-18",
        notes="Sweet spot for 16 GB. Patrick's reference model. ~20s responses.",
    )),
    (24, ModelRecommendation(
        model="gemma3:12b",
        display_name="Gemma 3 12B",
        size_gb=8.1,
        expected_tokens_per_sec="~15-18",
        notes="Comfortable fit. Room for multiple specialist models simultaneously.",
    )),
    (32, ModelRecommendation(
        model="gemma3:27b",
        display_name="Gemma 3 27B",
        size_gb=17.0,
        expected_tokens_per_sec="~8-12",
        notes="Higher quality. Slower responses. Good for complex reasoning.",
    )),
    (48, ModelRecommendation(
        model="gemma3:27b",
        display_name="Gemma 3 27B",
        size_gb=17.0,
        expected_tokens_per_sec="~12-15",
        notes="27B with headroom. Fast enough for real-time use.",
    )),
    (64, ModelRecommendation(
        model="llama3.3:70b",
        display_name="Llama 3.3 70B",
        size_gb=43.0,
        expected_tokens_per_sec="~5-8",
        notes="Near cloud quality. Requires patience on responses.",
    )),
    (128, ModelRecommendation(
        model="llama3.3:70b",
        display_name="Llama 3.3 70B",
        size_gb=43.0,
        expected_tokens_per_sec="~10-15",
        notes="70B with full headroom. Comfortable for sustained use.",
    )),
]


def detect_hardware() -> HardwareInfo:
    """Detect system hardware capabilities."""
    os_name = platform.system().lower()
    ram_gb = 0
    chip = "unknown"
    gpu = "unknown"
    unified = False

    if os_name == "darwin":
        # macOS — sysctl
        try:
            mem = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            ram_gb = int(mem.stdout.strip()) // (1024 ** 3)
        except Exception:
            pass

        try:
            cpu = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=5,
            )
            chip = cpu.stdout.strip()
        except Exception:
            pass

        # Check for Apple Silicon (unified memory)
        if "Apple" in chip:
            unified = True
            gpu = chip  # CPU and GPU are the same chip
        else:
            gpu = "discrete (Intel Mac)"

    elif os_name == "linux":
        # Linux — /proc
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_gb = kb // (1024 ** 2)
                        break
        except Exception:
            pass

        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        chip = line.split(":")[1].strip()
                        break
        except Exception:
            pass

        # Check for NVIDIA GPU
        try:
            nvidia = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5,
            )
            if nvidia.returncode == 0:
                gpu = nvidia.stdout.strip().split("\n")[0]
        except Exception:
            gpu = "none detected"

    return HardwareInfo(
        ram_gb=ram_gb,
        chip=chip,
        os=os_name,
        gpu=gpu,
        unified_memory=unified,
    )


def recommend_model(hw: HardwareInfo) -> ModelRecommendation:
    """Recommend the best Ollama model for the detected hardware."""
    for threshold, rec in reversed(MODEL_TABLE):
        if hw.ram_gb >= threshold:
            return rec

    # Fallback for <8 GB
    return ModelRecommendation(
        model="gemma3:1b",
        display_name="Gemma 3 1B",
        size_gb=1.0,
        expected_tokens_per_sec="~50+",
        notes="Very limited. Consider upgrading RAM for a usable agent.",
    )


def format_hardware_report(hw: HardwareInfo, rec: ModelRecommendation) -> str:
    """Format a human-readable hardware report."""
    lines = [
        "Hardware Detection",
        "=" * 40,
        f"  OS:              {hw.os}",
        f"  Chip:            {hw.chip}",
        f"  RAM:             {hw.ram_gb} GB {'(unified)' if hw.unified_memory else ''}",
        f"  GPU:             {hw.gpu}",
        "",
        "Recommended Model",
        "-" * 40,
        f"  Model:           {rec.model}",
        f"  Display name:    {rec.display_name}",
        f"  Size (Q4):       {rec.size_gb} GB",
        f"  Expected speed:  {rec.expected_tokens_per_sec} tok/s",
        f"  Notes:           {rec.notes}",
        "",
        f"  Install:         ollama pull {rec.model}",
    ]
    return "\n".join(lines)

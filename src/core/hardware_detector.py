"""
hardware_detector.py — Detect GPU/CPU capabilities for encoder selection
"""

import subprocess
import platform
import sys
import os
from typing import Optional


def _creationflags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def get_ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "ffmpeg")
    return os.path.join(base, "ffmpeg.exe")


def detect_cpu() -> dict:
    """Return CPU info: name, cores, threads."""
    name = platform.processor() or "Unknown CPU"
    try:
        import psutil
        cores = psutil.cpu_count(logical=False) or 1
        threads = psutil.cpu_count(logical=True) or cores
    except Exception:
        import os
        threads = os.cpu_count() or 1
        cores = threads

    return {"name": name, "cores": cores, "threads": threads}


def detect_gpu() -> Optional[dict]:
    """
    Try nvidia-smi to get GPU name + driver version.
    Returns dict or None if no NVIDIA GPU found.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_creationflags(),
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().splitlines()[0]
            parts = [p.strip() for p in line.split(",")]
            name = parts[0] if len(parts) > 0 else "NVIDIA GPU"
            driver = parts[1] if len(parts) > 1 else "Unknown"
            return {"name": name, "driver_version": driver, "nvenc_supported": False}
    except Exception:
        pass
    return None


def check_nvenc_support(ffmpeg_path: str) -> bool:
    """Check if h264_nvenc encoder is available in the bundled FFmpeg build."""
    if not os.path.isfile(ffmpeg_path):
        return False
    try:
        result = subprocess.run(
            [ffmpeg_path, "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_creationflags(),
        )
        return "h264_nvenc" in result.stdout
    except Exception:
        return False


def detect_hardware() -> dict:
    """
    Run full hardware detection.
    Returns:
    {
        "cpu": {name, cores, threads},
        "gpu": {name, driver_version, nvenc_supported} | None,
        "nvenc_in_ffmpeg": bool,
        "available_modes": ["Auto", "CPU (x264)", "NVIDIA NVENC"]  # subset
    }
    """
    cpu = detect_cpu()
    gpu = detect_gpu()
    ffmpeg_path = get_ffmpeg_path()
    nvenc_in_ffmpeg = check_nvenc_support(ffmpeg_path)

    if gpu is not None:
        gpu["nvenc_supported"] = nvenc_in_ffmpeg

    modes = ["Auto", "CPU (x264)"]
    if gpu is not None and nvenc_in_ffmpeg:
        modes.append("NVIDIA NVENC")

    return {
        "cpu": cpu,
        "gpu": gpu,
        "nvenc_in_ffmpeg": nvenc_in_ffmpeg,
        "available_modes": modes,
    }

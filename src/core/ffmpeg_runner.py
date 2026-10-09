"""
ffmpeg_runner.py — FFmpeg subprocess wrapper with progress parsing,
stream-copy logic, and automatic re-encode fallback.
"""

import os
import re
import sys
import subprocess
from typing import Callable, Optional

from src.core.models import MixPair, EncoderMode


def get_ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "ffmpeg")
    return os.path.join(base, "ffmpeg.exe")


def _creationflags() -> int:
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def build_command_stream_copy(ffmpeg: str, pair: MixPair, output_path: str) -> list:
    """Stream copy command — fast, no re-encode."""
    return [
        ffmpeg,
        "-stream_loop", "-1",
        "-i", pair.video_path,
        "-i", pair.audio_path,
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "copy",
        "-progress", "pipe:2",
        "-nostats",
        "-y",
        output_path,
    ]


def build_command_reencode(
    ffmpeg: str,
    pair: MixPair,
    output_path: str,
    encoder_mode: EncoderMode,
    hw_info: Optional[dict] = None,
) -> list:
    """Re-encode command — slower but more compatible."""
    use_nvenc = False
    if encoder_mode == EncoderMode.NVENC:
        use_nvenc = True
    elif encoder_mode == EncoderMode.AUTO:
        gpu = hw_info.get("gpu") if hw_info else None
        use_nvenc = bool(gpu and gpu.get("nvenc_supported"))

    if use_nvenc:
        video_codec = ["h264_nvenc", "-preset", "p4"]
    else:
        video_codec = ["libx264", "-preset", "veryfast"]

    return [
        ffmpeg,
        "-stream_loop", "-1",
        "-i", pair.video_path,
        "-i", pair.audio_path,
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", *video_codec,
        "-c:a", "aac", "-b:a", "192k",
        "-progress", "pipe:2",
        "-nostats",
        "-y",
        output_path,
    ]


def _is_stream_copy_error(stderr_text: str) -> bool:
    """Detect whether FFmpeg failed due to codec-copy incompatibility."""
    indicators = [
        "codec not currently supported in container",
        "Could not write header",
        "encoder not found",
        "Invalid data found",
        "error while opening encoder",
        "mp3float",
        "Trailing garbage",
    ]
    lower = stderr_text.lower()
    return any(ind.lower() in lower for ind in indicators)


def run_ffmpeg(
    pair: MixPair,
    output_path: str,
    encoder_mode: EncoderMode,
    always_reencode: bool,
    hw_info: Optional[dict],
    progress_callback: Optional[Callable[[float, str], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
    cancelled_flag: Optional[Callable[[], bool]] = None,
) -> tuple[bool, str]:
    """
    Run FFmpeg for one pair. Returns (success: bool, method_used: str).
    progress_callback(pct 0.0-1.0, eta_str)
    log_callback(message_str)
    cancelled_flag() -> bool
    """
    ffmpeg = get_ffmpeg_path()
    if not os.path.isfile(ffmpeg):
        raise FileNotFoundError(f"FFmpeg tidak ditemukan di: {ffmpeg}")

    audio_duration = pair.duration_audio or 0.0

    def _log(msg: str):
        if log_callback:
            log_callback(msg)

    def _run(cmd: list, label: str) -> tuple[bool, str, str]:
        """Execute cmd, parse progress, return (success, stdout, stderr)."""
        _log(f"[{label}] Memulai proses...")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_creationflags(),
        )

        stderr_lines = []
        current_time = 0.0
        import time
        start_wall = time.time()

        # Read stderr line by line for -progress output
        for raw_line in proc.stderr:
            line = raw_line.strip()
            stderr_lines.append(line)

            if cancelled_flag and cancelled_flag():
                proc.kill()
                return False, "", "\n".join(stderr_lines)

            # Parse -progress key=value lines from stderr
            if line.startswith("out_time_ms="):
                try:
                    ms = int(line.split("=")[1])
                    current_time = ms / 1_000_000.0  # microseconds → seconds
                    if audio_duration > 0:
                        pct = min(current_time / audio_duration, 1.0)
                        elapsed = time.time() - start_wall
                        eta = ""
                        if pct > 0.01:
                            remaining = elapsed / pct * (1.0 - pct)
                            mins = int(remaining // 60)
                            secs = int(remaining % 60)
                            eta = f"{mins}m {secs}s"
                        if progress_callback:
                            progress_callback(pct, eta)
                except (ValueError, IndexError):
                    pass

        proc.wait()
        stderr_text = "\n".join(stderr_lines)
        return proc.returncode == 0, "", stderr_text

    def _cleanup_output():
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass

    # ── Attempt 1: Stream copy (unless always_reencode) ──────────────────────
    if not always_reencode:
        cmd_copy = build_command_stream_copy(ffmpeg, pair, output_path)
        ok, _, stderr = _run(cmd_copy, "Stream Copy")
        if cancelled_flag and cancelled_flag():
            _cleanup_output()
            return False, "cancelled"
        if ok:
            _log("[Stream Copy] ✅ Selesai.")
            return True, "stream_copy"
        else:
            if _is_stream_copy_error(stderr):
                _log("[Stream Copy] ⚠️ Codec tidak kompatibel — fallback ke re-encode...")
            else:
                # Real error (file not found, corrupt, etc.) — don't fallback
                _cleanup_output()
                _log(f"[Stream Copy] ❌ Gagal: {_extract_error(stderr)}")
                return False, "stream_copy"

    # ── Attempt 2: Re-encode ──────────────────────────────────────────────────
    encoder_label = encoder_mode.value.upper()
    cmd_reencode = build_command_reencode(ffmpeg, pair, output_path, encoder_mode, hw_info)
    ok, _, stderr = _run(cmd_reencode, f"Re-encode ({encoder_label})")

    if cancelled_flag and cancelled_flag():
        _cleanup_output()
        return False, "cancelled"

    if ok:
        _log(f"[Re-encode] ✅ Selesai (encoder: {encoder_label}).")
        return True, f"reencode_{encoder_label}"

    # ── Attempt 3: NVENC → fallback CPU ──────────────────────────────────────
    if encoder_mode in (EncoderMode.NVENC, EncoderMode.AUTO):
        gpu = hw_info.get("gpu") if hw_info else None
        if gpu and gpu.get("nvenc_supported"):
            _log("[Re-encode] ⚠️ NVENC gagal — fallback ke CPU (x264)...")
            cmd_cpu = build_command_reencode(ffmpeg, pair, output_path, EncoderMode.CPU, hw_info)
            ok, _, stderr = _run(cmd_cpu, "Re-encode (CPU Fallback)")
            if cancelled_flag and cancelled_flag():
                _cleanup_output()
                return False, "cancelled"
            if ok:
                _log("[Re-encode] ✅ Selesai (CPU x264 fallback).")
                return True, "reencode_CPU_fallback"

    _cleanup_output()
    error_msg = _extract_error(stderr)
    _log(f"[Re-encode] ❌ Gagal: {error_msg}")
    return False, "failed"


def _extract_error(stderr: str) -> str:
    """Extract the most useful error line from FFmpeg stderr."""
    if not stderr:
        return "Unknown error"
    lines = stderr.splitlines()
    # Look for lines starting with "Error" or containing "Invalid"
    for line in reversed(lines):
        line = line.strip()
        if line and any(kw in line.lower() for kw in ["error", "invalid", "no such", "fail", "could not"]):
            return line
    # Fallback: last non-empty line
    for line in reversed(lines):
        if line.strip():
            return line.strip()
    return "Unknown error"

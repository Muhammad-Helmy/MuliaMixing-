"""
ffprobe_utils.py — Read media metadata via ffprobe subprocess
"""

import subprocess
import json
import os
import sys
from typing import Optional


def get_ffprobe_path() -> str:
    """Resolve ffprobe binary path (bundled or dev fallback)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "ffmpeg")
    return os.path.join(base, "ffprobe.exe")


def probe_duration(file_path: str) -> Optional[float]:
    """
    Return duration in seconds for a media file, or None on failure.
    Uses ffprobe JSON output.
    """
    ffprobe = get_ffprobe_path()
    if not os.path.isfile(ffprobe):
        return None
    if not os.path.isfile(file_path):
        return None

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        file_path,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        data = json.loads(result.stdout)
        duration = float(data.get("format", {}).get("duration", 0))
        return duration if duration > 0 else None
    except Exception:
        return None


def probe_streams(file_path: str) -> dict:
    """
    Return basic stream info dict with keys:
      has_video, has_audio, video_codec, audio_codec, duration
    """
    ffprobe = get_ffprobe_path()
    default = {"has_video": False, "has_audio": False,
                "video_codec": None, "audio_codec": None, "duration": None}
    if not os.path.isfile(ffprobe) or not os.path.isfile(file_path):
        return default

    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        file_path,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        duration = float(data.get("format", {}).get("duration", 0)) or None

        info = dict(default)
        info["duration"] = duration
        for s in streams:
            ct = s.get("codec_type", "")
            if ct == "video":
                info["has_video"] = True
                info["video_codec"] = s.get("codec_name")
            elif ct == "audio":
                info["has_audio"] = True
                info["audio_codec"] = s.get("codec_name")
        return info
    except Exception:
        return default

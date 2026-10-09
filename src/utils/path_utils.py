"""
path_utils.py — Output path helpers for MP4×MP3 Loop Merger
"""

import os
import re


def sanitize_filename(name: str) -> str:
    """Remove characters invalid in Windows filenames."""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def auto_output_name(video_path: str, audio_path: str = "") -> str:
    """Generate default output filename: [video]_merged.mp4"""
    v_stem = os.path.splitext(os.path.basename(video_path))[0]
    raw = f"{v_stem}_merged.mp4"
    return sanitize_filename(raw)


def default_output_folder(video_path: str, exe_dir: str) -> str:
    """
    Default output folder:
    - If video_path is set, use its parent directory.
    - Otherwise, use a subfolder 'Output' next to the exe.
    """
    if video_path:
        parent = os.path.dirname(video_path)
        if os.path.isdir(parent):
            return parent
    output_dir = os.path.join(exe_dir, "Output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def ensure_unique_path(folder: str, filename: str) -> str:
    """If the target file already exists, append (1), (2), etc."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(folder, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{base} ({counter}){ext}")
        counter += 1
    return candidate


def format_duration(seconds: float) -> str:
    """Format seconds to HH:MM:SS or MM:SS string."""
    if seconds is None:
        return "—"
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

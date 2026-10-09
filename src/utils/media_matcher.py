"""
media_matcher.py — Auto-detect and match video and audio files
"""

from __future__ import annotations
import os
import re
from typing import List, Tuple, Dict, Set
from difflib import SequenceMatcher

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".flv", ".ts", ".wmv"}
AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".wma"}

COMMON_SUFFIXES = [
    r"[-_ ]?loop",
    r"[-_ ]?audio",
    r"[-_ ]?sound",
    r"[-_ ]?bgm",
    r"[-_ ]?music",
    r"[-_ ]?instrumental",
    r"[-_ ]?inst",
    r"[-_ ]?vocal",
    r"[-_ ]?voc",
    r"[-_ ]?voice",
    r"[-_ ]?vo",
    r"[-_ ]?dub",
    r"[-_ ]?final",
    r"[-_ ]?mix",
    r"[-_ ]?track",
    r"[-_ ]?soundtrack",
    r"[-_ ]?video",
    r"[-_ ]?vid",
    r"\s*\(loop\)",
    r"\s*\[loop\]",
    r"\s*\(audio\)",
    r"\s*\[audio\]",
    r"\s*\(bgm\)",
    r"\s*\[bgm\]",
    r"\s*\(video\)",
    r"\s*\[video\]",
]

# Combined regex pattern for stripping suffixes at the end of the stem
_SUFFIX_PATTERN = re.compile(r"(?:" + "|".join(COMMON_SUFFIXES) + r")$", re.IGNORECASE)


def clean_stem(stem: str) -> str:
    """Strip common suffix tags like _loop, -audio, (bgm), etc."""
    cleaned = stem.strip()
    # Strip repeatedly if multiple suffixes exist, e.g. "name_loop_audio"
    for _ in range(3):
        new_cleaned = _SUFFIX_PATTERN.sub("", cleaned).strip()
        if new_cleaned == cleaned or not new_cleaned:
            break
        cleaned = new_cleaned
    return cleaned


def normalize_string(s: str) -> str:
    """Lowercases, replaces punctuation with space, and collapses spaces."""
    s = s.lower()
    s = re.sub(r"[-_.\s]+", " ", s).strip()
    return s


def calculate_match_score(video_path: str, audio_path: str) -> float:
    """
    Computes similarity score between a video and audio file.
    Returns a score from 0.0 to 100.0.
    """
    v_stem = os.path.splitext(os.path.basename(video_path))[0]
    a_stem = os.path.splitext(os.path.basename(audio_path))[0]

    v_low = v_stem.lower()
    a_low = a_stem.lower()

    # 1. Exact match (case-insensitive)
    if v_low == a_low:
        return 100.0

    # 2. Match after stripping common suffixes (e.g. shalawat-nabi--32 vs shalawat-nabi--32_loop)
    v_clean = clean_stem(v_stem).lower()
    a_clean = clean_stem(a_stem).lower()
    if v_clean == a_clean and v_clean:
        return 98.0
    if v_low == a_clean or a_low == v_clean:
        return 95.0

    # 3. Audio stem starts with video stem + delimiter (e.g. video_name and video_name_audio)
    if a_low.startswith(v_low) and len(a_low) > len(v_low) and a_low[len(v_low)] in "_- .":
        return 90.0

    # 4. Video stem starts with audio stem + delimiter
    if v_low.startswith(a_low) and len(v_low) > len(a_low) and v_low[len(a_low)] in "_- .":
        return 88.0

    # 5. Normalized alphanumeric string match
    v_norm = normalize_string(v_clean)
    a_norm = normalize_string(a_clean)
    if v_norm == a_norm and v_norm:
        return 85.0

    # 6. Check if both share identical numbers (e.g., episode/track numbers like 32, 33)
    v_nums = re.findall(r"\d+", v_stem)
    a_nums = re.findall(r"\d+", a_stem)
    if v_nums and a_nums and v_nums == a_nums:
        # If numbers are identical, check how similar the non-number prefixes are
        v_prefix = re.sub(r"\d+", "", v_norm).strip()
        a_prefix = re.sub(r"\d+", "", a_norm).strip()
        if v_prefix == a_prefix:
            return 82.0
        ratio = SequenceMatcher(None, v_prefix, a_prefix).ratio()
        if ratio > 0.6:
            return 75.0 + (ratio * 10)

    # 7. Fuzzy match using SequenceMatcher
    ratio = SequenceMatcher(None, v_clean, a_clean).ratio()
    if ratio >= 0.80:
        return 50.0 + (ratio * 30.0)

    return 0.0


def match_files(
    file_paths: List[str],
    min_score: float = 65.0,
) -> Tuple[List[Tuple[str, str]], List[str], List[str]]:
    """
    Given a list of file paths, separates them into video and audio,
    and returns:
      - matched_pairs: list of (video_path, audio_path)
      - unmatched_videos: list of video_path without audio
      - unmatched_audios: list of audio_path without video
    """
    videos = []
    audios = []

    for path in file_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTS:
            videos.append(path)
        elif ext in AUDIO_EXTS:
            audios.append(path)

    # Sort files naturally so pairs appear in order (e.g. 1, 2, 10)
    def natural_sort_key(s: str):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]

    videos.sort(key=natural_sort_key)
    audios.sort(key=natural_sort_key)

    matched_pairs: List[Tuple[str, str]] = []
    used_audios: Set[str] = set()
    unmatched_videos: List[str] = []

    # Greedy matching with highest score
    for v in videos:
        best_audio = None
        best_score = 0.0
        for a in audios:
            if a in used_audios:
                continue
            score = calculate_match_score(v, a)
            if score > best_score and score >= min_score:
                best_score = score
                best_audio = a

        if best_audio:
            matched_pairs.append((v, best_audio))
            used_audios.add(best_audio)
        else:
            unmatched_videos.append(v)

    unmatched_audios = [a for a in audios if a not in used_audios]

    return matched_pairs, unmatched_videos, unmatched_audios


def scan_and_match_folder(
    folder_path: str,
    min_score: float = 65.0,
) -> Tuple[List[Tuple[str, str]], List[str], List[str]]:
    """
    Scans a folder for video and audio files and automatically pairs them.
    """
    if not os.path.isdir(folder_path):
        return [], [], []

    all_files = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file():
                all_files.append(entry.path)
    except Exception:
        return [], [], []

    return match_files(all_files, min_score)

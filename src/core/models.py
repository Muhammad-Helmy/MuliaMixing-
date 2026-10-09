"""
models.py — Data models for MP4×MP3 Loop Merger
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class PairStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class EncoderMode(Enum):
    AUTO = "auto"
    CPU = "cpu"
    NVENC = "nvenc"


@dataclass
class MixPair:
    video_path: str = ""
    audio_path: str = ""
    output_name: str = ""
    output_folder: str = ""
    status: PairStatus = PairStatus.IDLE
    error_message: Optional[str] = None
    duration_video: Optional[float] = None   # seconds
    duration_audio: Optional[float] = None   # seconds
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_ready(self) -> bool:
        """Returns True if both video and audio are selected."""
        return bool(self.video_path and self.audio_path)

    def is_empty(self) -> bool:
        """Returns True if neither video nor audio is selected."""
        return not self.video_path and not self.audio_path

    def reset(self):
        self.status = PairStatus.IDLE
        self.error_message = None

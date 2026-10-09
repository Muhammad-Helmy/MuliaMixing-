"""
batch_worker.py — QThread sequential batch processor
"""

from __future__ import annotations
import os
import datetime
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from src.core.models import MixPair, PairStatus, EncoderMode
from src.core import ffmpeg_runner
from src.utils.path_utils import ensure_unique_path
from src.utils import ffprobe_utils


class BatchWorker(QThread):
    """
    Processes MixPair list sequentially in a background thread.
    Emits Qt signals for UI updates.
    """

    # Signals
    pair_started = Signal(str)           # pair id
    pair_progress = Signal(str, float, str)  # pair id, pct 0-1, eta str
    pair_done = Signal(str, str)         # pair id, method used
    pair_failed = Signal(str, str)       # pair id, error message
    log_message = Signal(str)            # log text line
    batch_finished = Signal()

    def __init__(
        self,
        pairs: List[MixPair],
        encoder_mode: EncoderMode,
        always_reencode: bool,
        hw_info: Optional[dict],
        parent=None,
    ):
        super().__init__(parent)
        self.pairs = pairs
        self.encoder_mode = encoder_mode
        self.always_reencode = always_reencode
        self.hw_info = hw_info
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _is_cancelled(self) -> bool:
        return self._cancelled

    def _emit_log(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] {msg}")

    def run(self):
        total = len(self.pairs)
        processed = 0

        for i, pair in enumerate(self.pairs):
            if self._cancelled:
                self._emit_log("⛔ Proses dibatalkan oleh user.")
                break

            if not pair.is_ready():
                self._emit_log(f"⚠️ Pair #{i+1}: Video atau Audio belum dipilih — dilewati.")
                self.pair_failed.emit(pair.id, "Video atau Audio belum dipilih")
                continue

            # Validate output folder
            output_folder = pair.output_folder
            try:
                os.makedirs(output_folder, exist_ok=True)
            except Exception as e:
                msg = f"Folder output tidak bisa dibuat: {output_folder} — {e}"
                self._emit_log(f"❌ Pair #{i+1}: {msg}")
                self.pair_failed.emit(pair.id, msg)
                continue

            output_path = ensure_unique_path(output_folder, pair.output_name)

            # Probe durations if not already done
            if pair.duration_audio is None:
                pair.duration_audio = ffprobe_utils.probe_duration(pair.audio_path)
            if pair.duration_video is None:
                pair.duration_video = ffprobe_utils.probe_duration(pair.video_path)

            self._emit_log(
                f"🎬 [{i+1}/{total}] Memproses: {pair.output_name}"
            )
            self._emit_log(
                f"   Video: {os.path.basename(pair.video_path)}"
            )
            self._emit_log(
                f"   Audio: {os.path.basename(pair.audio_path)}"
            )
            self._emit_log(
                f"   Output: {output_path}"
            )

            self.pair_started.emit(pair.id)

            try:
                success, method = ffmpeg_runner.run_ffmpeg(
                    pair=pair,
                    output_path=output_path,
                    encoder_mode=self.encoder_mode,
                    always_reencode=self.always_reencode,
                    hw_info=self.hw_info,
                    progress_callback=lambda pct, eta, pid=pair.id: self.pair_progress.emit(pid, pct, eta),
                    log_callback=self._emit_log,
                    cancelled_flag=self._is_cancelled,
                )
            except Exception as exc:
                success = False
                method = "exception"
                self._emit_log(f"❌ Exception: {exc}")

            if success:
                processed += 1
                self._emit_log(
                    f"✅ [{i+1}/{total}] Selesai → {os.path.basename(output_path)}"
                )
                self.pair_done.emit(pair.id, method)
            else:
                error = f"Gagal memproses (lihat log untuk detail)"
                self._emit_log(f"❌ [{i+1}/{total}] Gagal: {pair.output_name}")
                self.pair_failed.emit(pair.id, error)

        summary = f"Batch selesai: {processed}/{total} berhasil."
        self._emit_log(f"\n{'─'*50}")
        self._emit_log(f"🏁 {summary}")
        self.batch_finished.emit()

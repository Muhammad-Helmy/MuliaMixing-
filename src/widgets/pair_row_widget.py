"""
pair_row_widget.py — Dark premium pair row for batch mode
"""

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QFrame, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.models import MixPair, PairStatus
from src.utils.path_utils import auto_output_name, format_duration
from src.utils import ffprobe_utils


class DropLineEdit(QLineEdit):
    """QLineEdit that accepts file drag-and-drop."""
    file_dropped = Signal(str)

    def __init__(self, accept_ext: str, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.accept_ext = accept_ext.lower()
        self.setReadOnly(True)
        self.setPlaceholderText(placeholder)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                f = urls[0].toLocalFile()
                if not self.accept_ext or f.lower().endswith(self.accept_ext):
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            f = urls[0].toLocalFile()
            if not self.accept_ext or f.lower().endswith(self.accept_ext):
                self.file_dropped.emit(f)
                event.acceptProposedAction()
                return
        super().dropEvent(event)


class ProbeThread(QThread):
    finished = Signal(str, float)
    def __init__(self, field: str, path: str, parent=None):
        super().__init__(parent)
        self.field = field
        self.path = path
    def run(self):
        d = ffprobe_utils.probe_duration(self.path) or 0.0
        self.finished.emit(self.field, d)


class PairRowWidget(QFrame):
    """
    Premium dark pair row card.
    """
    remove_requested = Signal(str)
    pair_updated = Signal(str)

    STATUS_LABELS = {
        PairStatus.IDLE:       ("● Idle",          "badgeIdle"),
        PairStatus.PROCESSING: ("⟳ Memproses",     "badgeProcessing"),
        PairStatus.DONE:       ("✓ Selesai",        "badgeDone"),
        PairStatus.FAILED:     ("✗ Gagal",          "badgeFailed"),
    }
    FRAME_NAMES = {
        PairStatus.IDLE:       "pairRow",
        PairStatus.PROCESSING: "pairRowProcessing",
        PairStatus.DONE:       "pairRowDone",
        PairStatus.FAILED:     "pairRowFailed",
    }

    def __init__(self, pair: MixPair, row_index: int = 0, parent=None):
        super().__init__(parent)
        self.pair = pair
        self.row_index = row_index
        self._probes: list[QThread] = []
        self.setObjectName("pairRow")
        self.setFrameShape(QFrame.StyledPanel)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 12)
        outer.setSpacing(10)

        # ── Top row: index + status + remove ──────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        self.labelRowNum = QLabel(f"#{self.row_index + 1}")
        self.labelRowNum.setStyleSheet(
            "color: #484F58; font-size: 12px; font-weight: 700; min-width: 28px;"
        )
        top.addWidget(self.labelRowNum)

        top.addStretch()

        self.statusBadge = QLabel("● Idle")
        self.statusBadge.setObjectName("badgeIdle")
        self.statusBadge.setAlignment(Qt.AlignCenter)
        self.statusBadge.setFixedWidth(110)
        top.addWidget(self.statusBadge)

        self.btnRemove = QPushButton("✕")
        self.btnRemove.setObjectName("btnRemove")
        self.btnRemove.setFixedSize(28, 28)
        self.btnRemove.setToolTip("Hapus pasangan ini")
        self.btnRemove.clicked.connect(lambda: self.remove_requested.emit(self.pair.id))
        top.addWidget(self.btnRemove)

        outer.addLayout(top)

        # ── File pickers row ───────────────────────────────────────────────
        mid = QHBoxLayout()
        mid.setSpacing(12)

        # Video section
        mid.addLayout(self._make_picker("video", "🎬  Video (.mp4)", "Video MP4 (*.mp4)", ".mp4"), stretch=1)

        # VS divider
        vs = QLabel("×")
        vs.setStyleSheet("color: #30363D; font-size: 18px; font-weight: bold;")
        vs.setAlignment(Qt.AlignCenter)
        vs.setFixedWidth(20)
        mid.addWidget(vs)

        # Audio section
        mid.addLayout(self._make_picker("audio", "🎵  Audio (.mp3)", "Audio MP3 (*.mp3)", ".mp3"), stretch=1)

        outer.addLayout(mid)

        # ── Output name row ────────────────────────────────────────────────
        bot = QHBoxLayout()
        bot.setSpacing(8)

        out_lbl = QLabel("Output:")
        out_lbl.setStyleSheet("color: #8B9BB4; font-size: 12px; min-width: 50px;")
        bot.addWidget(out_lbl)

        self.editOutputName = QLineEdit(self.pair.output_name)
        self.editOutputName.setPlaceholderText("nama_output.mp4")
        self.editOutputName.textChanged.connect(lambda t: setattr(self.pair, "output_name", t))
        bot.addWidget(self.editOutputName, stretch=1)

        self.btnOpenFolder = QPushButton("📁")
        self.btnOpenFolder.setObjectName("btnIcon")
        self.btnOpenFolder.setFixedSize(30, 30)
        self.btnOpenFolder.setToolTip("Buka folder output")
        self.btnOpenFolder.clicked.connect(self._open_folder)
        self.btnOpenFolder.setEnabled(self.pair.status == PairStatus.DONE)
        bot.addWidget(self.btnOpenFolder)

        outer.addLayout(bot)

        # Error message
        self.labelError = QLabel("")
        self.labelError.setWordWrap(True)
        self.labelError.setStyleSheet("color: #E8A0A0; font-size: 11px; padding-left: 4px;")
        self.labelError.setVisible(False)
        outer.addWidget(self.labelError)

        # Initialize existing files if pair already has paths
        if self.pair.video_path and os.path.isfile(self.pair.video_path):
            self.set_file_path("video", self.pair.video_path)
        if self.pair.audio_path and os.path.isfile(self.pair.audio_path):
            self.set_file_path("audio", self.pair.audio_path)

    def _make_picker(self, field: str, label: str, filt: str, ext: str) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Header row with label + duration
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #8B9BB4; font-size: 11px; font-weight: 600;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        dur_lbl = QLabel("—")
        dur_lbl.setStyleSheet("color: #8FCB9B; font-size: 11px; font-weight: 600;")
        if field == "video":
            self.durVideoLabel = dur_lbl
        else:
            self.durAudioLabel = dur_lbl
        hdr.addWidget(dur_lbl)
        layout.addLayout(hdr)

        # Picker row
        row = QHBoxLayout()
        row.setSpacing(6)

        path_edit = DropLineEdit(accept_ext=ext, placeholder="Belum dipilih... (atau drag & drop file ke sini)")
        path_edit.file_dropped.connect(lambda p, f=field: self.set_file_path(f, p))

        if getattr(self.pair, f"{field}_path"):
            path_edit.setText(os.path.basename(getattr(self.pair, f"{field}_path")))
            path_edit.setToolTip(getattr(self.pair, f"{field}_path"))

        if field == "video":
            self.editVideoPath = path_edit
        else:
            self.editAudioPath = path_edit
        row.addWidget(path_edit, stretch=1)

        btn = QPushButton("Browse")
        btn.setObjectName("btnBrowse")
        btn.setFixedWidth(72)
        btn.clicked.connect(lambda chk=False, f=field, fi=filt, e=ext: self._browse(f, fi, e))
        row.addWidget(btn)
        layout.addLayout(row)
        return layout

    def set_file_path(self, field: str, path: str):
        if not path or not os.path.isfile(path):
            return
        setattr(self.pair, f"{field}_path", path)
        edit = self.editVideoPath if field == "video" else self.editAudioPath
        edit.setText(os.path.basename(path))
        edit.setToolTip(path)

        # Auto-fill output name if not yet set or is default
        if self.pair.video_path and not self.pair.output_name:
            name = auto_output_name(self.pair.video_path, self.pair.audio_path)
            self.pair.output_name = name
            self.editOutputName.blockSignals(True)
            self.editOutputName.setText(name)
            self.editOutputName.blockSignals(False)

        # Probe duration
        t = ProbeThread(field, path, self)
        t.finished.connect(self._on_probe)
        self._probes.append(t)
        t.start()
        self.pair_updated.emit(self.pair.id)

    def _browse(self, field: str, filt: str, ext: str):
        start = os.path.dirname(getattr(self.pair, f"{field}_path")) if getattr(self.pair, f"{field}_path") else ""
        path, _ = QFileDialog.getOpenFileName(self, f"Pilih file", start, filt)
        if path:
            self.set_file_path(field, path)

    def _on_probe(self, field: str, dur: float):
        dur_lbl = self.durVideoLabel if field == "video" else self.durAudioLabel
        if field == "video":
            self.pair.duration_video = dur or None
        else:
            self.pair.duration_audio = dur or None
        dur_lbl.setText(format_duration(dur) if dur > 0 else "?")

    def _open_folder(self):
        if self.pair.output_folder and os.path.isdir(self.pair.output_folder):
            import subprocess
            subprocess.Popen(["explorer", self.pair.output_folder])

    # ── Public API ────────────────────────────────────────────────────────────

    def set_row_index(self, idx: int):
        self.row_index = idx
        self.labelRowNum.setText(f"#{idx + 1}")

    def set_status(self, status: PairStatus, error_msg: str = ""):
        self.pair.status = status
        label_text, badge_name = self.STATUS_LABELS.get(status, ("● Idle", "badgeIdle"))
        frame_name = self.FRAME_NAMES.get(status, "pairRow")

        self.statusBadge.setText(label_text)
        self.statusBadge.setObjectName(badge_name)
        self.statusBadge.style().unpolish(self.statusBadge)
        self.statusBadge.style().polish(self.statusBadge)

        self.setObjectName(frame_name)
        self.style().unpolish(self)
        self.style().polish(self)

        self.labelError.setText(f"⚠  {error_msg}" if error_msg else "")
        self.labelError.setVisible(bool(error_msg) and status == PairStatus.FAILED)

        self.btnOpenFolder.setEnabled(status == PairStatus.DONE)

        editable = status not in (PairStatus.PROCESSING,)
        for w in [self.editVideoPath, self.editAudioPath, self.editOutputName]:
            w.setEnabled(editable)
        self.btnRemove.setEnabled(editable)

    def reset(self):
        self.set_status(PairStatus.IDLE)
        self.pair.reset()

    def get_pair(self) -> MixPair:
        return self.pair

"""
single_page.py — Mode Single: premium dark UI with drop-zone style file pickers
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem,
)
from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.models import MixPair, PairStatus
from src.utils.path_utils import auto_output_name, format_duration, default_output_folder
from src.utils import ffprobe_utils


class DropZone(QFrame):
    """Visual file drop zone / picker."""

    file_selected = Signal(str)   # emits file path

    def __init__(self, icon: str, title: str, subtitle: str,
                 file_filter: str, accept_ext: str, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.accept_ext = accept_ext.lower()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(110)
        self.setCursor(Qt.PointingHandCursor)
        self._path = ""
        self._setup_ui(icon, title, subtitle)

    def _setup_ui(self, icon: str, title: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        # Icon row
        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignCenter)
        self.iconLabel = QLabel(icon)
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setAlignment(Qt.AlignCenter)
        icon_row.addWidget(self.iconLabel)
        layout.addLayout(icon_row)

        self.titleLabel = QLabel(title)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 13px; font-weight: 600; color: #8B9BB4;")
        layout.addWidget(self.titleLabel)

        self.subtitleLabel = QLabel(subtitle)
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel.setStyleSheet("font-size: 11px; color: #484F58;")
        layout.addWidget(self.subtitleLabel)

        # File name (hidden until file selected)
        self.fileLabel = QLabel("")
        self.fileLabel.setAlignment(Qt.AlignCenter)
        self.fileLabel.setWordWrap(True)
        self.fileLabel.setStyleSheet("font-size: 12px; color: #8FCB9B; font-weight: 600;")
        self.fileLabel.setVisible(False)
        layout.addWidget(self.fileLabel)

        # Duration label
        self.durLabel = QLabel("")
        self.durLabel.setAlignment(Qt.AlignCenter)
        self.durLabel.setStyleSheet("font-size: 12px; color: #8B9BB4;")
        self.durLabel.setVisible(False)
        layout.addWidget(self.durLabel)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._browse()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toLocalFile()
            if url.lower().endswith(self.accept_ext):
                event.acceptProposedAction()
                self.setObjectName("dropZoneFilled")
                self.style().unpolish(self); self.style().polish(self)

    def dragLeaveEvent(self, event):
        if not self._path:
            self.setObjectName("dropZone")
            self.style().unpolish(self); self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        url = event.mimeData().urls()[0].toLocalFile()
        if url.lower().endswith(self.accept_ext):
            self._set_file(url)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Pilih {self.titleLabel.text()}", "", self.file_filter)
        if path:
            self._set_file(path)

    def _set_file(self, path: str):
        self._path = path
        self.setObjectName("dropZoneFilled")
        self.style().unpolish(self); self.style().polish(self)

        fname = os.path.basename(path)
        # Truncate long names
        if len(fname) > 40:
            fname = fname[:37] + "..."
        self.fileLabel.setText(f"📄 {fname}")
        self.fileLabel.setVisible(True)
        self.titleLabel.setStyleSheet("font-size: 12px; font-weight: 500; color: #8B9BB4;")
        self.subtitleLabel.setVisible(False)
        self.iconLabel.setStyleSheet("font-size: 20px; color: #8FCB9B;")
        self.durLabel.setText("⏱ Membaca durasi...")
        self.durLabel.setVisible(True)
        self.file_selected.emit(path)

    def set_duration(self, dur: float | None):
        if dur:
            self.durLabel.setText(f"⏱ {format_duration(dur)}")
        else:
            self.durLabel.setText("⏱ Durasi tidak terbaca")

    def get_path(self) -> str:
        return self._path

    def set_enabled_state(self, enabled: bool):
        self.setEnabled(enabled)
        if enabled:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)


class ProbeThread(QThread):
    finished = Signal(str, float)
    def __init__(self, tag: str, path: str, parent=None):
        super().__init__(parent)
        self.tag = tag; self.path = path
    def run(self):
        d = ffprobe_utils.probe_duration(self.path) or 0.0
        self.finished.emit(self.tag, d)


class SinglePage(QWidget):
    """Premium single-pair form with visual drop zones."""

    run_requested = Signal(object)

    def __init__(self, exe_dir: str, parent=None):
        super().__init__(parent)
        self.exe_dir = exe_dir
        self.pair = MixPair()
        self._probes: list[QThread] = []
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("scrollContent")
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(20)

        # Page header
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        title = QLabel("Single Mode")
        title.setObjectName("pageTitle")
        hdr.addWidget(title)
        sub = QLabel("Pilih satu pasangan video + audio, lalu klik Run.")
        sub.setObjectName("pageSubtitle")
        hdr.addWidget(sub)
        outer.addLayout(hdr)

        # ── File pickers row ─────────────────────────────────────────────
        pickers_row = QHBoxLayout()
        pickers_row.setSpacing(16)

        # Video drop zone
        v_col = QVBoxLayout()
        v_col.setSpacing(8)
        v_lbl = QLabel("File Video")
        v_lbl.setObjectName("sectionTitle")
        v_col.addWidget(v_lbl)
        v_hint = QLabel("Format: .mp4")
        v_hint.setObjectName("fieldLabel")
        v_col.addWidget(v_hint)
        self.dropVideo = DropZone("🎬", "Klik atau drag video di sini", ".mp4 supported",
                                   "Video MP4 (*.mp4)", ".mp4")
        self.dropVideo.file_selected.connect(lambda p: self._on_file_selected("video", p))
        v_col.addWidget(self.dropVideo)
        pickers_row.addLayout(v_col, stretch=1)

        # Arrow separator
        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 24px; color: #30363D; font-weight: bold;")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setFixedWidth(30)
        pickers_row.addWidget(arrow)

        # Audio drop zone
        a_col = QVBoxLayout()
        a_col.setSpacing(8)
        a_lbl = QLabel("File Audio")
        a_lbl.setObjectName("sectionTitle")
        a_col.addWidget(a_lbl)
        a_hint = QLabel("Format: .mp3")
        a_hint.setObjectName("fieldLabel")
        a_col.addWidget(a_hint)
        self.dropAudio = DropZone("🎵", "Klik atau drag audio di sini", ".mp3 supported",
                                   "Audio MP3 (*.mp3)", ".mp3")
        self.dropAudio.file_selected.connect(lambda p: self._on_file_selected("audio", p))
        a_col.addWidget(self.dropAudio)
        pickers_row.addLayout(a_col, stretch=1)

        outer.addLayout(pickers_row)

        # ── Output settings card ─────────────────────────────────────────
        out_card = QFrame()
        out_card.setObjectName("card")
        out_layout = QVBoxLayout(out_card)
        out_layout.setContentsMargins(20, 18, 20, 18)
        out_layout.setSpacing(14)

        out_title = QLabel("Output Settings")
        out_title.setObjectName("sectionTitle")
        out_layout.addWidget(out_title)

        # Output name
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = QLabel("Nama File:")
        name_lbl.setObjectName("fieldLabel")
        name_lbl.setFixedWidth(90)
        name_row.addWidget(name_lbl)
        self.editOutputName = QLineEdit()
        self.editOutputName.setPlaceholderText("output.mp4 (auto-generated)")
        self.editOutputName.textChanged.connect(lambda t: setattr(self.pair, "output_name", t))
        name_row.addWidget(self.editOutputName, stretch=1)
        out_layout.addLayout(name_row)

        # Output folder
        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)
        folder_lbl = QLabel("Folder Output:")
        folder_lbl.setObjectName("fieldLabel")
        folder_lbl.setFixedWidth(90)
        folder_row.addWidget(folder_lbl)
        self.editOutputFolder = QLineEdit()
        self.editOutputFolder.setReadOnly(True)
        self.editOutputFolder.setPlaceholderText("(otomatis — folder video sumber)")
        folder_row.addWidget(self.editOutputFolder, stretch=1)
        btn_folder = QPushButton("📁  Pilih")
        btn_folder.setObjectName("btnBrowse")
        btn_folder.setFixedWidth(90)
        btn_folder.clicked.connect(self._browse_folder)
        folder_row.addWidget(btn_folder)
        out_layout.addLayout(folder_row)

        outer.addWidget(out_card)
        outer.addStretch()

        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    def _on_file_selected(self, field: str, path: str):
        if field == "video":
            self.pair.video_path = path
        else:
            self.pair.audio_path = path

        # Probe duration in background
        t = ProbeThread(field, path, self)
        t.finished.connect(self._on_probe_done)
        self._probes.append(t)
        t.start()

        # Auto-fill output name + folder
        if self.pair.video_path and self.pair.audio_path:
            # Always auto-update output name to reflect the current video file
            name = auto_output_name(self.pair.video_path, self.pair.audio_path)
            self.editOutputName.blockSignals(True)
            self.editOutputName.setText(name)
            self.editOutputName.blockSignals(False)
            self.pair.output_name = name
            if not self.pair.output_folder:
                folder = default_output_folder(self.pair.video_path, self.exe_dir)
                self.pair.output_folder = folder
                self.editOutputFolder.setText(folder)

    def _on_probe_done(self, field: str, dur: float):
        if field == "video":
            self.pair.duration_video = dur or None
            self.dropVideo.set_duration(dur or None)
        else:
            self.pair.duration_audio = dur or None
            self.dropAudio.set_duration(dur or None)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output",
                                                   self.pair.output_folder or "")
        if folder:
            self.pair.output_folder = folder
            self.editOutputFolder.setText(folder)

    def get_pair(self) -> MixPair:
        self.pair.output_name = self.editOutputName.text() or "output.mp4"
        return self.pair

    def set_running(self, running: bool):
        self.dropVideo.set_enabled_state(not running)
        self.dropAudio.set_enabled_state(not running)
        self.editOutputName.setEnabled(not running)
        self.editOutputFolder.setEnabled(not running)

    def update_hw_info(self, hw_info: dict):
        pass

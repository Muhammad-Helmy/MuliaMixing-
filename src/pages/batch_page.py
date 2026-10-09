"""
batch_page.py — Batch mode: premium dark pair list with auto-detection
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
    QLineEdit, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Signal, Qt, Slot, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from src.core.models import MixPair, PairStatus
from src.widgets.pair_row_widget import PairRowWidget
from src.utils.path_utils import default_output_folder
from src.utils.media_matcher import scan_and_match_folder, match_files


class BatchPage(QWidget):
    run_all_requested = Signal(list)

    def __init__(self, exe_dir: str, parent=None):
        super().__init__(parent)
        self.exe_dir = exe_dir
        self._rows: list[PairRowWidget] = []
        self._running = False
        self._output_folder = default_output_folder("", exe_dir)
        self._last_folder = ""
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top toolbar ─────────────────────────────────────────────────
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("background: #161B22; border-bottom: 1px solid #21262D;")
        toolbar_frame.setFixedHeight(56)
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(20, 0, 20, 0)
        toolbar.setSpacing(12)

        title = QLabel("Batch Mode")
        title.setObjectName("pageTitle")
        toolbar.addWidget(title)

        self.labelBatchStatus = QLabel("")
        self.labelBatchStatus.setStyleSheet("color: #8B9BB4; font-size: 12px;")
        toolbar.addWidget(self.labelBatchStatus)

        toolbar.addStretch()

        # Auto detect folder button in toolbar
        self.btnAutoDetectTop = QPushButton("⚡ Auto Deteksi Folder")
        self.btnAutoDetectTop.setObjectName("btnAutoDetect")
        self.btnAutoDetectTop.setFixedHeight(34)
        self.btnAutoDetectTop.setCursor(Qt.PointingHandCursor)
        self.btnAutoDetectTop.setToolTip("Pilih folder berisi video dan mp3 untuk dipasangkan otomatis")
        self.btnAutoDetectTop.clicked.connect(lambda checked=False: self.auto_detect_folder())
        toolbar.addWidget(self.btnAutoDetectTop)

        # Separator
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background: #21262D;")
        toolbar.addWidget(sep)

        # Global output folder
        folder_icon = QLabel("📁")
        folder_icon.setStyleSheet("font-size: 14px;")
        toolbar.addWidget(folder_icon)

        self.editGlobalFolder = QLineEdit(self._output_folder)
        self.editGlobalFolder.setReadOnly(True)
        self.editGlobalFolder.setFixedWidth(200)
        self.editGlobalFolder.setToolTip("Folder output untuk semua pasangan")
        toolbar.addWidget(self.editGlobalFolder)

        btnFolder = QPushButton("Ubah")
        btnFolder.setObjectName("btnBrowse")
        btnFolder.setFixedWidth(60)
        btnFolder.clicked.connect(self._browse_global_folder)
        toolbar.addWidget(btnFolder)

        root.addWidget(toolbar_frame)

        # ── Scroll area ─────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setObjectName("mainScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setAcceptDrops(True)

        self.pairsContainer = QWidget()
        self.pairsContainer.setObjectName("scrollContent")
        self.pairsLayout = QVBoxLayout(self.pairsContainer)
        self.pairsLayout.setContentsMargins(20, 16, 20, 16)
        self.pairsLayout.setSpacing(10)
        self.pairsLayout.addStretch()

        self._scroll.setWidget(self.pairsContainer)
        root.addWidget(self._scroll, stretch=1)

        # ── Bottom bar ──────────────────────────────────────────────────
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background: #161B22; border-top: 1px solid #21262D;")
        bottom_bar.setFixedHeight(56)
        bot_layout = QHBoxLayout(bottom_bar)
        bot_layout.setContentsMargins(20, 0, 20, 0)
        bot_layout.setSpacing(10)

        # Add pair button
        self.btnAddPair = QPushButton("＋  Tambah Pasangan")
        self.btnAddPair.setObjectName("btnAddPair")
        self.btnAddPair.setFixedHeight(36)
        self.btnAddPair.setCursor(Qt.PointingHandCursor)
        self.btnAddPair.clicked.connect(lambda checked=False: self.add_pair())
        bot_layout.addWidget(self.btnAddPair)

        # Auto detect folder button
        self.btnAutoDetect = QPushButton("⚡  Auto Deteksi Folder")
        self.btnAutoDetect.setObjectName("btnAutoDetect")
        self.btnAutoDetect.setFixedHeight(36)
        self.btnAutoDetect.setCursor(Qt.PointingHandCursor)
        self.btnAutoDetect.setToolTip("Scan folder dan pasangkan video (.mp4) & audio (.mp3) secara otomatis")
        self.btnAutoDetect.clicked.connect(lambda checked=False: self.auto_detect_folder())
        bot_layout.addWidget(self.btnAutoDetect)

        # Clear all button
        self.btnClearAll = QPushButton("🗑  Bersihkan")
        self.btnClearAll.setObjectName("btnClearAll")
        self.btnClearAll.setFixedHeight(36)
        self.btnClearAll.setCursor(Qt.PointingHandCursor)
        self.btnClearAll.setToolTip("Hapus semua pasangan dari daftar")
        self.btnClearAll.clicked.connect(self.clear_all_pairs)
        bot_layout.addWidget(self.btnClearAll)

        bot_layout.addStretch()

        self.labelProgress = QLabel("")
        self.labelProgress.setStyleSheet("color: #8FCB9B; font-size: 12px; font-weight: 600;")
        bot_layout.addWidget(self.labelProgress)

        root.addWidget(bottom_bar)

        # Start with 2 initial empty rows
        self.add_pair()
        self.add_pair()

    # ── Drag and Drop Support ───────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return

        paths = [u.toLocalFile() for u in urls if u.toLocalFile()]
        if not paths:
            return

        # If a single directory was dropped, scan that folder
        if len(paths) == 1 and os.path.isdir(paths[0]):
            self.auto_detect_folder(paths[0])
            event.acceptProposedAction()
            return

        # If multiple files/directories were dropped
        all_files = []
        for p in paths:
            if os.path.isdir(p):
                try:
                    for entry in os.scandir(p):
                        if entry.is_file():
                            all_files.append(entry.path)
                except Exception:
                    pass
            elif os.path.isfile(p):
                all_files.append(p)

        if all_files:
            self.auto_detect_files(all_files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ── Auto Detect Methods ─────────────────────────────────────────────────

    def auto_detect_folder(self, folder: str = ""):
        if self._running:
            return

        if not folder:
            start_dir = self._last_folder or (self._output_folder if os.path.isdir(self._output_folder) else "")
            folder = QFileDialog.getExistingDirectory(
                self,
                "Pilih Folder Berisi Video (.mp4) dan Audio (.mp3)",
                start_dir,
            )

        if not folder or not os.path.isdir(folder):
            return

        self._last_folder = folder
        matched_pairs, unmatched_videos, unmatched_audios = scan_and_match_folder(folder)

        if not matched_pairs and not unmatched_videos:
            QMessageBox.information(
                self,
                "Auto Deteksi",
                f"Tidak ditemukan file video (.mp4, dll) atau audio (.mp3, dll) di folder:\n{folder}",
            )
            return

        # Remove existing blank rows before populating
        self._remove_empty_rows()

        # Add all matched pairs
        added_count = 0
        for v_path, a_path in matched_pairs:
            pair = MixPair(video_path=v_path, audio_path=a_path, output_folder=self._output_folder)
            self.add_pair(pair)
            added_count += 1

        # Also add any unmatched videos so user can manually select audio if needed
        unmatched_video_count = 0
        for v_path in unmatched_videos:
            pair = MixPair(video_path=v_path, audio_path="", output_folder=self._output_folder)
            self.add_pair(pair)
            unmatched_video_count += 1

        # Summary notification
        info_lines = [f"✅ Berhasil mendeteksi {added_count} pasangan video & audio cocok!"]
        if unmatched_video_count > 0:
            info_lines.append(f"⚠️ {unmatched_video_count} video belum memiliki audio (perlu dipilih manual).")
        if unmatched_audios:
            info_lines.append(f"ℹ️ {len(unmatched_audios)} file audio tidak memiliki pasangan video.")

        QMessageBox.information(
            self,
            "Auto Deteksi Selesai",
            "\n\n".join(info_lines),
        )

    def auto_detect_files(self, file_paths: list[str]):
        if self._running:
            return

        matched_pairs, unmatched_videos, unmatched_audios = match_files(file_paths)

        if not matched_pairs and not unmatched_videos:
            QMessageBox.information(
                self,
                "Auto Deteksi",
                "Tidak ada file video atau audio yang sesuai dari file yang di-drop/dipilih.",
            )
            return

        self._remove_empty_rows()

        added_count = 0
        for v_path, a_path in matched_pairs:
            pair = MixPair(video_path=v_path, audio_path=a_path, output_folder=self._output_folder)
            self.add_pair(pair)
            added_count += 1

        unmatched_video_count = 0
        for v_path in unmatched_videos:
            pair = MixPair(video_path=v_path, audio_path="", output_folder=self._output_folder)
            self.add_pair(pair)
            unmatched_video_count += 1

        info_lines = [f"✅ Berhasil mendeteksi {added_count} pasangan video & audio cocok!"]
        if unmatched_video_count > 0:
            info_lines.append(f"⚠️ {unmatched_video_count} video belum memiliki audio.")
        if unmatched_audios:
            info_lines.append(f"ℹ️ {len(unmatched_audios)} file audio tidak memiliki pasangan video.")

        QMessageBox.information(
            self,
            "Auto Deteksi Selesai",
            "\n\n".join(info_lines),
        )

    def _remove_empty_rows(self):
        """Remove empty placeholder rows."""
        empty_rows = [r for r in self._rows if r.pair.is_empty()]
        for r in empty_rows:
            self._rows.remove(r)
            self.pairsLayout.removeWidget(r)
            r.deleteLater()
        self._renumber()
        self._update_status()

    def clear_all_pairs(self):
        """Clear all pairs with confirmation if list is not empty."""
        if self._running:
            return

        has_data = any(not r.pair.is_empty() for r in self._rows)
        if has_data:
            reply = QMessageBox.question(
                self,
                "Bersihkan Semua Pasangan",
                "Apakah Anda yakin ingin menghapus semua pasangan dari daftar?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        for r in list(self._rows):
            self.pairsLayout.removeWidget(r)
            r.deleteLater()
        self._rows.clear()

        # Add 2 fresh rows
        self.add_pair()
        self.add_pair()
        self._update_status()

    # ── Pair Management ─────────────────────────────────────────────────────

    def add_pair(self, pair: MixPair | None = None) -> PairRowWidget:
        if not isinstance(pair, MixPair):
            pair = MixPair()
        if not pair.output_folder:
            pair.output_folder = self._output_folder

        row = PairRowWidget(pair, len(self._rows), self.pairsContainer)
        row.remove_requested.connect(self._remove_pair)
        row.pair_updated.connect(self._on_pair_updated)

        insert_pos = max(0, self.pairsLayout.count() - 1)
        self.pairsLayout.insertWidget(insert_pos, row)
        self._rows.append(row)
        self._update_status()

        QTimer.singleShot(60, lambda: self._scroll_to_bottom())
        return row

    def _scroll_to_bottom(self):
        if hasattr(self, "_scroll") and self._scroll:
            bar = self._scroll.verticalScrollBar()
            bar.setValue(bar.maximum())

    def _remove_pair(self, pair_id: str):
        if self._running:
            return
        row = self._find_row(pair_id)
        if row:
            self._rows.remove(row)
            self.pairsLayout.removeWidget(row)
            row.deleteLater()
            self._renumber()
            self._update_status()

    def _find_row(self, pair_id: str) -> PairRowWidget | None:
        return next((r for r in self._rows if r.pair.id == pair_id), None)

    def _renumber(self):
        for i, row in enumerate(self._rows):
            row.set_row_index(i)

    def _on_pair_updated(self, pair_id: str):
        self._update_status()
        row = self._find_row(pair_id)
        if row:
            row.pair.output_folder = self._output_folder

    def _browse_global_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Folder Output", self._output_folder)
        if folder:
            self._output_folder = folder
            self.editGlobalFolder.setText(folder)
            self.editGlobalFolder.setToolTip(folder)
            for row in self._rows:
                row.pair.output_folder = folder

    def _update_status(self):
        n = len(self._rows)
        ready = sum(1 for r in self._rows if r.pair.is_ready())
        self.labelBatchStatus.setText(f"{n} pasangan  •  {ready} siap")

    def get_ready_pairs(self) -> list[MixPair]:
        return [r.pair for r in self._rows if r.pair.is_ready()]

    def get_all_pairs(self) -> list[MixPair]:
        return [r.pair for r in self._rows]

    @Slot(str)
    def on_pair_started(self, pair_id: str):
        row = self._find_row(pair_id)
        if row:
            row.set_status(PairStatus.PROCESSING)

    @Slot(str, str)
    def on_pair_done(self, pair_id: str, method: str):
        row = self._find_row(pair_id)
        if row:
            row.set_status(PairStatus.DONE)

    @Slot(str, str)
    def on_pair_failed(self, pair_id: str, error: str):
        row = self._find_row(pair_id)
        if row:
            row.set_status(PairStatus.FAILED, error)

    def set_running(self, running: bool):
        self._running = running
        self.btnAddPair.setEnabled(not running)
        self.btnAutoDetect.setEnabled(not running)
        self.btnAutoDetectTop.setEnabled(not running)
        self.btnClearAll.setEnabled(not running)
        for row in self._rows:
            if row.pair.status != PairStatus.PROCESSING:
                row.btnRemove.setEnabled(not running)

    def update_batch_progress(self, current: int, total: int):
        if total > 0:
            self.labelProgress.setText(f"⏳ {current} / {total} diproses")
        else:
            self.labelProgress.setText("")

    def reset_all(self):
        for row in self._rows:
            row.reset()
        self.labelProgress.setText("")

    def update_hw_info(self, hw_info: dict):
        pass

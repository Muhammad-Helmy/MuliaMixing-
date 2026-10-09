"""
log_panel.py — Log panel with dark terminal aesthetic
"""

import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit, QProgressBar, QFileDialog,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QTextCursor


class LogPanel(QWidget):
    """Dark terminal-style log panel with progress bar and export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Header ──────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(8)

        lbl = QLabel("📋  Log Proses")
        lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #E8EDF2;")
        header.addWidget(lbl)
        header.addStretch()

        self.btnCopy = QPushButton("Copy")
        self.btnCopy.setObjectName("btnBrowse")
        self.btnCopy.setFixedWidth(70)
        self.btnCopy.clicked.connect(self._copy_log)
        header.addWidget(self.btnCopy)

        self.btnExport = QPushButton("Export")
        self.btnExport.setObjectName("btnBrowse")
        self.btnExport.setFixedWidth(70)
        self.btnExport.clicked.connect(self._export_log)
        header.addWidget(self.btnExport)

        layout.addLayout(header)

        # ── Progress row ─────────────────────────────────────────────────
        prog_row = QHBoxLayout()
        prog_row.setSpacing(12)

        self.labelCurrentFile = QLabel("Menunggu proses...")
        self.labelCurrentFile.setStyleSheet("font-size: 12px; color: #8B9BB4;")
        prog_row.addWidget(self.labelCurrentFile, stretch=1)

        self.labelEta = QLabel("")
        self.labelEta.setStyleSheet("font-size: 12px; color: #8FCB9B; font-weight: 600;")
        self.labelEta.setAlignment(Qt.AlignRight)
        prog_row.addWidget(self.labelEta)

        layout.addLayout(prog_row)

        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBig")
        self.progressBar.setRange(0, 1000)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(6)
        layout.addWidget(self.progressBar)

        # ── Log text ─────────────────────────────────────────────────────
        self.logEdit = QPlainTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMinimumHeight(120)
        self.logEdit.setPlaceholderText("Log output akan muncul di sini setelah proses dimulai...")
        font = QFont("Cascadia Code", 11)
        font.setStyleHint(QFont.Monospace)
        self.logEdit.setFont(font)
        layout.addWidget(self.logEdit)

    # ── Public slots ─────────────────────────────────────────────────────────

    @Slot(str)
    def append_log(self, text: str):
        self.logEdit.appendPlainText(text)
        self.logEdit.moveCursor(QTextCursor.End)

    @Slot(float, str)
    def update_progress(self, pct: float, eta: str):
        self.progressBar.setValue(int(pct * 1000))
        if eta:
            self.labelEta.setText(f"ETA: {eta}")
        else:
            self.labelEta.setText(f"{int(pct * 100)}%")

    @Slot(str)
    def set_current_file(self, filename: str):
        if filename:
            self.labelCurrentFile.setText(f"⏳ Memproses: {filename}")
        else:
            self.labelCurrentFile.setText("Menunggu proses...")

    def reset_progress(self):
        self.progressBar.setValue(0)
        self.labelEta.setText("")
        self.labelCurrentFile.setText("Memulai...")

    def set_progress_done(self):
        self.progressBar.setValue(1000)
        self.labelEta.setText("100%")
        self.labelCurrentFile.setText("✅ Semua selesai")

    def clear(self):
        self.logEdit.clear()
        self.reset_progress()
        self.labelCurrentFile.setText("Menunggu proses...")

    def _copy_log(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.logEdit.toPlainText())

    def _export_log(self):
        fname = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filename, _ = QFileDialog.getSaveFileName(self, "Export Log", fname, "Text files (*.txt)")
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.logEdit.toPlainText())
            except Exception as e:
                self.append_log(f"[Error] Gagal export log: {e}")

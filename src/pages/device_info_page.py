"""
device_info_page.py — Hardware information page
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from src.core import hardware_detector


class DetectThread(QThread):
    finished = Signal(dict)

    def run(self):
        info = hardware_detector.detect_hardware()
        self.finished.emit(info)


class DeviceInfoPage(QWidget):
    hw_info_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hw_info: dict | None = None
        self._setup_ui()
        self._start_detection()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Info Perangkat")
        title.setObjectName("sectionTitle")
        hdr.addWidget(title)
        hdr.addStretch()
        self.btnRefresh = QPushButton("🔄  Refresh Deteksi")
        self.btnRefresh.setObjectName("btnBrowse")
        self.btnRefresh.clicked.connect(self._start_detection)
        hdr.addWidget(self.btnRefresh)
        outer.addLayout(hdr)

        subtitle = QLabel("Informasi hardware yang digunakan untuk pemilihan encoder.")
        subtitle.setObjectName("labelSecondary")
        outer.addWidget(subtitle)

        # Status label (outside scroll — never cleared)
        self.labelStatus = QLabel("🔍 Mendeteksi hardware...")
        self.labelStatus.setObjectName("labelSecondary")
        outer.addWidget(self.labelStatus)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.contentLayout = QVBoxLayout(content)
        self.contentLayout.setSpacing(12)
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.contentLayout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _start_detection(self):
        self.btnRefresh.setEnabled(False)
        self.labelStatus.setText("🔍 Mendeteksi hardware...")
        self.labelStatus.setVisible(True)
        self._clear_info_cards()
        t = DetectThread(self)
        t.finished.connect(self._on_detection_done)
        t.start()
        self._detect_thread = t

    def _clear_info_cards(self):
        # Remove all items except the trailing stretch (last item)
        while self.contentLayout.count() > 1:
            item = self.contentLayout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _on_detection_done(self, hw_info: dict):
        self._hw_info = hw_info
        self.labelStatus.setVisible(False)
        self._clear_info_cards()

        idx = 0

        # ── CPU card ──────────────────────────────────────────────────────
        cpu = hw_info.get("cpu", {})
        cpu_card = self._make_card()
        self.contentLayout.insertWidget(idx, cpu_card); idx += 1
        c_layout = cpu_card.layout()
        c_layout.addWidget(self._card_title("🖥  CPU"))
        c_layout.addWidget(self._info_row("Nama", cpu.get("name", "Unknown")))
        c_layout.addWidget(self._info_row("Core Fisik", str(cpu.get("cores", "?"))))
        c_layout.addWidget(self._info_row("Thread (Logical)", str(cpu.get("threads", "?"))))

        # ── GPU card ──────────────────────────────────────────────────────
        gpu = hw_info.get("gpu")
        gpu_card = self._make_card()
        self.contentLayout.insertWidget(idx, gpu_card); idx += 1
        g_layout = gpu_card.layout()
        g_layout.addWidget(self._card_title("🎮  GPU"))

        if gpu:
            g_layout.addWidget(self._info_row("Nama", gpu.get("name", "Unknown")))
            g_layout.addWidget(self._info_row("Driver NVIDIA", gpu.get("driver_version", "Unknown")))
            nvenc = gpu.get("nvenc_supported", False)
            nvenc_txt = "✅ Tersedia" if nvenc else "❌ Tidak tersedia dalam build FFmpeg ini"
            g_layout.addWidget(self._info_row("NVENC (h264_nvenc)", nvenc_txt))
        else:
            lbl = QLabel("❌  GPU NVIDIA tidak terdeteksi di perangkat ini.")
            lbl.setObjectName("labelSecondary")
            g_layout.addWidget(lbl)

        # ── Encoding modes card ───────────────────────────────────────────
        enc_card = self._make_card()
        self.contentLayout.insertWidget(idx, enc_card); idx += 1
        e_layout = enc_card.layout()
        e_layout.addWidget(self._card_title("⚙  Mode Encoding Tersedia"))

        available = hw_info.get("available_modes", [])
        for mode in ["Auto", "CPU (x264)", "NVIDIA NVENC"]:
            ok = mode in available
            icon = "✅" if ok else "❌"
            lbl = QLabel(f"{icon}  {mode}")
            lbl.setStyleSheet("padding: 2px 0; font-size: 13px;")
            e_layout.addWidget(lbl)

        note_text = "Perangkat ini dapat berjalan di: " + ", ".join(available)
        note = QLabel(note_text)
        note.setWordWrap(True)
        note.setStyleSheet(
            "background: #F0FAF4; border: 1px solid #C6E6CF; border-radius: 6px; "
            "padding: 8px 12px; color: #065F46; font-size: 12px; margin-top: 8px;"
        )
        e_layout.addWidget(note)

        self.contentLayout.insertStretch(idx)
        self.btnRefresh.setEnabled(True)
        self.hw_info_ready.emit(hw_info)

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        return card

    def _card_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        return lbl

    def _info_row(self, key: str, value: str) -> QWidget:
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)
        k_lbl = QLabel(key + ":")
        k_lbl.setObjectName("labelSecondary")
        k_lbl.setFixedWidth(160)
        rl.addWidget(k_lbl)
        v_lbl = QLabel(value)
        v_lbl.setWordWrap(True)
        rl.addWidget(v_lbl, stretch=1)
        return row

    def get_hw_info(self) -> dict | None:
        return self._hw_info

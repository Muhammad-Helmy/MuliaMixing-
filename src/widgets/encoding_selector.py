"""
encoding_selector.py — Encoder mode selector widget
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QCheckBox, QFrame,
)
from PySide6.QtCore import Signal

from src.core.models import EncoderMode


class EncodingSelector(QWidget):
    """
    Widget for selecting encoding mode (Auto / CPU / NVENC)
    and the 'Always Re-encode' toggle.
    """

    mode_changed = Signal(EncoderMode)
    reencode_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hw_info: dict | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Encoder mode label + combo
        lbl_enc = QLabel("Mode Encoding:")
        lbl_enc.setObjectName("labelSecondary")
        layout.addWidget(lbl_enc)

        self.comboEncoder = QComboBox()
        self.comboEncoder.addItem("Auto", EncoderMode.AUTO)
        self.comboEncoder.addItem("CPU (x264)", EncoderMode.CPU)
        self.comboEncoder.addItem("NVIDIA NVENC", EncoderMode.NVENC)
        self.comboEncoder.setCurrentIndex(0)
        self.comboEncoder.currentIndexChanged.connect(self._on_mode_changed)
        layout.addWidget(self.comboEncoder)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setStyleSheet("color: #E4E7E9;")
        layout.addWidget(sep)

        # Always re-encode checkbox
        self.chkReencode = QCheckBox("Always Re-encode")
        self.chkReencode.setToolTip(
            "Paksa re-encode (lebih lambat tapi lebih kompatibel).\n"
            "Default: OFF → stream copy (cepat) dengan fallback otomatis."
        )
        self.chkReencode.setChecked(False)
        self.chkReencode.stateChanged.connect(
            lambda s: self.reencode_changed.emit(bool(s))
        )
        layout.addWidget(self.chkReencode)

        layout.addStretch()

    def set_hardware_info(self, hw_info: dict):
        """Update available modes based on detected hardware."""
        self._hw_info = hw_info
        available_modes = hw_info.get("available_modes", ["Auto", "CPU (x264)"])
        nvenc_available = "NVIDIA NVENC" in available_modes

        # Enable/disable NVENC option
        nvenc_idx = 2  # index of NVENC in combo
        model = self.comboEncoder.model()
        item = model.item(nvenc_idx)
        if item:
            from PySide6.QtCore import Qt
            item.setEnabled(nvenc_available)
            if not nvenc_available:
                item.setToolTip("GPU NVIDIA tidak terdeteksi di perangkat ini")

    def get_mode(self) -> EncoderMode:
        return self.comboEncoder.currentData()

    def get_always_reencode(self) -> bool:
        return self.chkReencode.isChecked()

    def _on_mode_changed(self, idx: int):
        mode = self.comboEncoder.itemData(idx)
        if mode == EncoderMode.NVENC and self._hw_info:
            gpu = self._hw_info.get("gpu")
            nvenc_ok = gpu and gpu.get("nvenc_supported")
            if not nvenc_ok:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "NVENC Tidak Tersedia",
                    "GPU NVIDIA tidak terdeteksi di perangkat ini.\n"
                    "Pilih mode 'Auto' atau 'CPU (x264)'.",
                )
                self.comboEncoder.setCurrentIndex(0)
                return
        if mode:
            self.mode_changed.emit(mode)

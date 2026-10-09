"""
app_window.py — MainWindow: dark premium UI with left sidebar navigation
"""

import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QMessageBox, QSplitter, QSizePolicy, QScrollArea,
    QSpacerItem,
)
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor

from src.core.models import MixPair, PairStatus, EncoderMode
from src.core.batch_worker import BatchWorker
from src.pages.single_page import SinglePage
from src.pages.batch_page import BatchPage
from src.pages.device_info_page import DeviceInfoPage
from src.pages.guide_page import GuidePage
from src.widgets.log_panel import LogPanel
from src.widgets.encoding_selector import EncodingSelector
from src.utils.path_utils import default_output_folder


def get_exe_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class NavButton(QPushButton):
    """Sidebar navigation button with active state."""
    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(f"  {icon_text}   {label}", parent)
        self.setObjectName("navBtn")
        self.setCheckable(False)
        self.setFixedHeight(42)
        self.setCursor(Qt.PointingHandCursor)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class MainWindow(QMainWindow):

    MODE_SINGLE = 0
    MODE_BATCH = 1
    MODE_DEVICE = 2
    MODE_GUIDE = 3

    def __init__(self):
        super().__init__()
        self.exe_dir = get_exe_dir()
        self._hw_info: dict | None = None
        self._worker: BatchWorker | None = None
        self._batch_total = 0
        self._batch_current = 0
        self._done_count = 0
        self._current_mode = self.MODE_SINGLE

        self.setWindowTitle("MuliaMixing")
        self.setMinimumSize(980, 700)
        self.resize(1200, 800)

        # Set window icon
        icon_path = os.path.join(self.exe_dir, "resources", "icons", "app.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "app.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self._load_stylesheet()
        self._switch_mode(self.MODE_SINGLE)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            icon_path = os.path.join(self.exe_dir, "resources", "icons", "app.ico")
            if not os.path.isfile(icon_path):
                icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "app.ico")
            try:
                from src.main import apply_windows_taskbar_icon
                apply_windows_taskbar_icon(int(self.winId()), icon_path)
            except Exception:
                pass

    def _load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "theme.qss")
        if os.path.isfile(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    # ─────────────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── LEFT SIDEBAR ──────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo area
        logo_area = QFrame()
        logo_area.setObjectName("sidebarLogoArea")
        logo_area.setFixedHeight(72)
        logo_layout = QHBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 12, 16, 12)
        logo_layout.setSpacing(12)

        # App icon
        icon_path = os.path.join(self.exe_dir, "resources", "icons", "app.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "app.ico")
        logo_icon = QLabel()
        logo_icon.setFixedSize(36, 36)
        if os.path.isfile(icon_path):
            pm = QPixmap(icon_path).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_icon.setPixmap(pm)
        else:
            logo_icon.setText("🎬")
            logo_icon.setStyleSheet("font-size: 24px;")
        logo_layout.addWidget(logo_icon)

        logo_text_col = QVBoxLayout()
        logo_text_col.setSpacing(1)
        lbl_name = QLabel("MuliaMixing")
        lbl_name.setObjectName("sidebarTitle")
        logo_text_col.addWidget(lbl_name)
        lbl_sub = QLabel("Video × Audio Merger")
        lbl_sub.setObjectName("sidebarSubtitle")
        logo_text_col.addWidget(lbl_sub)
        logo_layout.addLayout(logo_text_col)
        sidebar_layout.addWidget(logo_area)

        # Nav spacer top
        sidebar_layout.addSpacerItem(QSpacerItem(0, 16))

        # Section label
        nav_label = QLabel("  MENU")
        nav_label.setStyleSheet("color: #484F58; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")
        nav_label.setContentsMargins(16, 0, 0, 8)
        sidebar_layout.addWidget(nav_label)

        # Nav buttons
        nav_btn_layout = QVBoxLayout()
        nav_btn_layout.setContentsMargins(10, 0, 10, 0)
        nav_btn_layout.setSpacing(2)

        self.navSingle = NavButton("▶", "Single Mode")
        self.navSingle.clicked.connect(lambda: self._switch_mode(self.MODE_SINGLE))
        nav_btn_layout.addWidget(self.navSingle)

        self.navBatch = NavButton("⚡", "Batch Mode")
        self.navBatch.clicked.connect(lambda: self._switch_mode(self.MODE_BATCH))
        nav_btn_layout.addWidget(self.navBatch)

        self.navDevice = NavButton("💻", "Device Info")
        self.navDevice.clicked.connect(lambda: self._switch_mode(self.MODE_DEVICE))
        nav_btn_layout.addWidget(self.navDevice)

        self.navGuide = NavButton("📖", "Panduan")
        self.navGuide.clicked.connect(lambda: self._switch_mode(self.MODE_GUIDE))
        nav_btn_layout.addWidget(self.navGuide)

        sidebar_layout.addLayout(nav_btn_layout)
        sidebar_layout.addStretch()

        # Bottom: version label
        lbl_ver = QLabel("  v1.1.0")
        lbl_ver.setObjectName("sidebarVersion")
        lbl_ver.setContentsMargins(16, 0, 0, 16)
        sidebar_layout.addWidget(lbl_ver)

        root.addWidget(sidebar)

        # ── RIGHT COLUMN: topbar + pages + log + footer ───────────────────
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        # Top bar (encoding selector + status)
        topbar = QFrame()
        topbar.setObjectName("topBar")
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)
        topbar_layout.setSpacing(12)

        self.labelPageTitle = QLabel("Single Mode")
        self.labelPageTitle.setStyleSheet("font-size: 14px; font-weight: 600; color: #E8EDF2;")
        topbar_layout.addWidget(self.labelPageTitle)

        topbar_layout.addStretch()

        # Hardware status indicator
        self.labelHwStatus = QLabel("🔍 Mendeteksi hardware...")
        self.labelHwStatus.setStyleSheet("font-size: 12px; color: #8B9BB4;")
        topbar_layout.addWidget(self.labelHwStatus)

        # Separator
        sep = QFrame()
        sep.setObjectName("dividerV")
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background: #21262D;")
        topbar_layout.addWidget(sep)

        self.encodingSelector = EncodingSelector()
        topbar_layout.addWidget(self.encodingSelector)

        right_col.addWidget(topbar)

        # ── Main splitter: page stack (top) + log (bottom) ────────────────
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle { background: #21262D; }")

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("mainContent")

        self.singlePage = SinglePage(self.exe_dir)
        self.batchPage = BatchPage(self.exe_dir)
        self.devicePage = DeviceInfoPage()
        self.guidePage = GuidePage()

        self.stack.addWidget(self.singlePage)   # index 0
        self.stack.addWidget(self.batchPage)    # index 1
        self.stack.addWidget(self.devicePage)   # index 2
        self.stack.addWidget(self.guidePage)    # index 3

        self.devicePage.hw_info_ready.connect(self._on_hw_info_ready)

        splitter.addWidget(self.stack)

        # Log panel
        log_frame = QFrame()
        log_frame.setObjectName("logContainer")
        log_inner = QVBoxLayout(log_frame)
        log_inner.setContentsMargins(16, 12, 16, 12)
        log_inner.setSpacing(0)
        self.logPanel = LogPanel()
        log_inner.addWidget(self.logPanel)
        splitter.addWidget(log_frame)

        splitter.setSizes([500, 220])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        right_col.addWidget(splitter, stretch=1)

        # ── Footer bar ─────────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("footerBar")
        footer.setFixedHeight(66)
        foot_layout = QHBoxLayout(footer)
        foot_layout.setContentsMargins(20, 0, 20, 0)
        foot_layout.setSpacing(12)

        # Batch progress label
        self.labelBatchProgress = QLabel("")
        self.labelBatchProgress.setStyleSheet("color: #8B9BB4; font-size: 12px;")
        foot_layout.addWidget(self.labelBatchProgress)

        foot_layout.addStretch()

        self.btnCancel = QPushButton("✕  Batalkan")
        self.btnCancel.setObjectName("btnCancel")
        self.btnCancel.setFixedHeight(44)
        self.btnCancel.setFixedWidth(130)
        self.btnCancel.setVisible(False)
        self.btnCancel.clicked.connect(self._cancel_processing)
        foot_layout.addWidget(self.btnCancel)

        self.btnRun = QPushButton("▶  Run")
        self.btnRun.setObjectName("btnRunPrimary")
        self.btnRun.setFixedHeight(44)
        self.btnRun.setFixedWidth(160)
        self.btnRun.setCursor(Qt.PointingHandCursor)
        self.btnRun.clicked.connect(self._on_run_clicked)
        foot_layout.addWidget(self.btnRun)

        right_col.addWidget(footer)

        right_widget = QWidget()
        right_widget.setObjectName("mainContent")
        right_widget.setLayout(right_col)
        root.addWidget(right_widget, stretch=1)

    # ─────────────────────────────────────────────────────────────────────────
    # Mode switching
    # ─────────────────────────────────────────────────────────────────────────

    def _switch_mode(self, mode: int):
        self._current_mode = mode
        self.stack.setCurrentIndex(mode)

        page_titles = {
            self.MODE_SINGLE: "Single Mode",
            self.MODE_BATCH:  "Batch Mode",
            self.MODE_DEVICE: "Device Info",
            self.MODE_GUIDE:  "Panduan Penggunaan",
        }
        self.labelPageTitle.setText(page_titles.get(mode, ""))

        # Show/hide Run button
        if mode in (self.MODE_DEVICE, self.MODE_GUIDE):
            self.btnRun.setVisible(False)
        else:
            self.btnRun.setVisible(True)
            self.btnRun.setText("▶  Run" if mode == self.MODE_SINGLE else "⚡  Run All")

        # Update nav active states
        self.navSingle.set_active(mode == self.MODE_SINGLE)
        self.navBatch.set_active(mode == self.MODE_BATCH)
        self.navDevice.set_active(mode == self.MODE_DEVICE)
        self.navGuide.set_active(mode == self.MODE_GUIDE)

    # ─────────────────────────────────────────────────────────────────────────
    # Hardware info
    # ─────────────────────────────────────────────────────────────────────────

    @Slot(dict)
    def _on_hw_info_ready(self, hw_info: dict):
        self._hw_info = hw_info
        self.encodingSelector.set_hardware_info(hw_info)
        gpu = hw_info.get("gpu")
        cpu = hw_info.get("cpu", {})
        cpu_short = cpu.get("name", "CPU")[:28]
        if gpu:
            self.labelHwStatus.setText(f"🎮 {gpu['name']}  |  🖥 {cpu_short}")
            self.labelHwStatus.setStyleSheet("font-size: 12px; color: #8FCB9B;")
        else:
            self.labelHwStatus.setText(f"🖥 {cpu_short}  |  No GPU NVIDIA")
            self.labelHwStatus.setStyleSheet("font-size: 12px; color: #8B9BB4;")

    # ─────────────────────────────────────────────────────────────────────────
    # Run / Cancel
    # ─────────────────────────────────────────────────────────────────────────

    def _on_run_clicked(self):
        if self._current_mode == self.MODE_SINGLE:
            pair = self.singlePage.get_pair()
            if not pair.is_ready():
                QMessageBox.warning(self, "File Belum Dipilih",
                                    "Pilih file video (.mp4) dan audio (.mp3) terlebih dahulu.")
                return
            if not pair.output_folder:
                pair.output_folder = default_output_folder(pair.video_path, self.exe_dir)
            if not pair.output_name:
                pair.output_name = "output.mp4"
            self._start_processing([pair])

        elif self._current_mode == self.MODE_BATCH:
            pairs = self.batchPage.get_ready_pairs()
            if not pairs:
                QMessageBox.warning(self, "Tidak Ada Pasangan Siap",
                                    "Tambahkan minimal satu pasangan video+audio yang lengkap.")
                return
            not_ready = len(self.batchPage.get_all_pairs()) - len(pairs)
            if not_ready > 0:
                reply = QMessageBox.question(
                    self, "Ada Pasangan Tidak Lengkap",
                    f"{not_ready} pasangan belum lengkap dan akan dilewati.\n"
                    f"Lanjutkan proses {len(pairs)} pasangan yang siap?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
            self._start_processing(pairs)

    def _start_processing(self, pairs: list[MixPair]):
        encoder_mode = self.encodingSelector.get_mode()
        always_reencode = self.encodingSelector.get_always_reencode()

        if encoder_mode == EncoderMode.NVENC:
            gpu = self._hw_info.get("gpu") if self._hw_info else None
            if not gpu or not gpu.get("nvenc_supported"):
                QMessageBox.critical(
                    self, "NVENC Tidak Tersedia",
                    "GPU NVIDIA tidak terdeteksi atau NVENC tidak didukung FFmpeg ini.\n"
                    "Pilih mode 'Auto' atau 'CPU (x264)'.",
                )
                return

        self._batch_total = len(pairs)
        self._batch_current = 0
        self._done_count = 0

        self.logPanel.clear()
        self.logPanel.append_log(
            f"══════════════════════════════════════════════════════\n"
            f"  MuliaMixing — Mulai proses {len(pairs)} pasangan\n"
            f"  Encoder : {encoder_mode.value.upper()}\n"
            f"  Mode    : {'Re-encode (paksa)' if always_reencode else 'Stream Copy (cepat, auto-fallback)'}\n"
            f"══════════════════════════════════════════════════════\n"
        )

        # Lock UI
        self.btnRun.setEnabled(False)
        self.btnCancel.setVisible(True)
        self.singlePage.set_running(True)
        self.batchPage.set_running(True)
        self.labelBatchProgress.setText(f"Menyiapkan {len(pairs)} pasangan...")

        self._worker = BatchWorker(
            pairs=pairs,
            encoder_mode=encoder_mode,
            always_reencode=always_reencode,
            hw_info=self._hw_info,
            parent=self,
        )
        self._worker.pair_started.connect(self._on_pair_started)
        self._worker.pair_progress.connect(self._on_pair_progress)
        self._worker.pair_done.connect(self._on_pair_done)
        self._worker.pair_failed.connect(self._on_pair_failed)
        self._worker.log_message.connect(self.logPanel.append_log)
        self._worker.batch_finished.connect(self._on_batch_finished)
        self._worker.start()

    @Slot()
    def _cancel_processing(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.logPanel.append_log("\n⛔  Permintaan pembatalan dikirim...")
            self.btnCancel.setEnabled(False)

    # ─────────────────────────────────────────────────────────────────────────
    # Worker signals
    # ─────────────────────────────────────────────────────────────────────────

    @Slot(str)
    def _on_pair_started(self, pair_id: str):
        self._batch_current += 1
        self.batchPage.on_pair_started(pair_id)
        self.batchPage.update_batch_progress(self._batch_current, self._batch_total)
        self.labelBatchProgress.setText(
            f"⏳  Memproses {self._batch_current} / {self._batch_total}"
        )
        self.logPanel.reset_progress()

    @Slot(str, float, str)
    def _on_pair_progress(self, pair_id: str, pct: float, eta: str):
        self.logPanel.update_progress(pct, eta)

    @Slot(str, str)
    def _on_pair_done(self, pair_id: str, method: str):
        self._done_count += 1
        self.batchPage.on_pair_done(pair_id, method)

    @Slot(str, str)
    def _on_pair_failed(self, pair_id: str, error: str):
        self.batchPage.on_pair_failed(pair_id, error)

    @Slot()
    def _on_batch_finished(self):
        self.btnRun.setEnabled(True)
        self.btnCancel.setVisible(False)
        self.btnCancel.setEnabled(True)
        self.singlePage.set_running(False)
        self.batchPage.set_running(False)
        self.logPanel.set_progress_done()

        done = self._done_count
        total = self._batch_total
        failed = total - done

        self.labelBatchProgress.setText(
            f"✅ Selesai: {done}/{total} berhasil"
            + (f"  |  ❌ {failed} gagal" if failed > 0 else "")
        )

        # Offer to open output folder
        if done > 0:
            output_folder = self.batchPage._output_folder
            if self._current_mode == self.MODE_SINGLE:
                pair = self.singlePage.get_pair()
                if pair.output_folder:
                    output_folder = pair.output_folder

            reply = QMessageBox.question(
                self,
                "Proses Selesai",
                f"✅  {done} dari {total} file berhasil diproses.\n\n"
                f"Buka folder output?\n{output_folder}",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                import subprocess
                subprocess.Popen(["explorer", output_folder])

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        event.accept()

from PySide6.QtWidgets import QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from src.pages.task_page_base import TaskPage

class LoopPage(TaskPage):
    title = "Loop Video"
    run_label = "Run Loop"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        lbl = QLabel("Halaman Loop Video (Segera hadir - Fase 1)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; color: #8B9BB4;")
        layout.addWidget(lbl)

    def prepare_jobs(self, parent_window):
        return None

    def create_worker(self, jobs, encoder_mode, always_reencode, hw_info, parent):
        return None

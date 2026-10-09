from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QThread

class TaskPage(QWidget):
    """
    Base class for new generic task pages (Loop Video, Gabung Video).
    """
    title: str = ""
    run_label: str = "Run"

    def prepare_jobs(self, parent_window) -> list | None:
        """
        Validates inputs and shows warnings. 
        Returns a list of job objects (can be MixPair or any other dataclass) if ready.
        Returns None if cancelled or invalid.
        """
        pass

    def create_worker(self, jobs, encoder_mode, always_reencode, hw_info, parent) -> QThread:
        """
        Returns a configured QThread worker instance.
        The worker must emit the same signals as BatchWorker:
        pair_started, pair_progress, pair_done, pair_failed, log_message, batch_finished.
        """
        pass

    def set_running(self, running: bool):
        """Disables/enables UI elements during processing."""
        pass

    def on_job_started(self, job_id: str):
        pass

    def on_job_progress(self, job_id: str, pct: float, eta: str):
        pass

    def on_job_done(self, job_id: str, info: str):
        pass

    def on_job_failed(self, job_id: str, error: str):
        pass

    def output_folder(self) -> str:
        """Returns the base output folder for the batch/jobs."""
        return ""

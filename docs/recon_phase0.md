# Recon Phase 0 - MuliaMixing v1.2.0

## 1. Field `MixPair` & Enums
**Enum `PairStatus`:** `IDLE`, `PROCESSING`, `DONE`, `FAILED`
**Enum `EncoderMode`:** `AUTO`, `CPU`, `NVENC`

**Dataclass `MixPair`:**
- `video_path`: str
- `audio_path`: str
- `output_name`: str
- `output_folder`: str
- `status`: PairStatus
- `error_message`: Optional[str]
- `duration_video`: Optional[float]
- `duration_audio`: Optional[float]
- `id`: str

## 2. Signature Fungsi Utilitas
- `ensure_unique_path(folder: str, filename: str) -> str`
- `default_output_folder(video_path: str, exe_dir: str) -> str`
- `probe_duration(file_path: str) -> Optional[float]`

## 3. Method Publik Page yang Dipanggil `MainWindow`
**`SinglePage`:**
- `get_pair() -> MixPair`
- `set_running(running: bool)`
- `update_hw_info(hw_info: dict)`

**`BatchPage`:**
- `get_ready_pairs() -> list[MixPair]`
- `get_all_pairs() -> list[MixPair]`
- `on_pair_started(pair_id: str)`
- `on_pair_done(pair_id: str, method: str)`
- `on_pair_failed(pair_id: str, error: str)`
- `set_running(running: bool)`
- `update_batch_progress(current: int, total: int)`
- `_output_folder` (Akses field langsung, bukan method, dipanggil di _on_batch_finished)

## 4. API `LogPanel`
- `append_log(self, text: str)`
- `update_progress(self, pct: float, eta: str)`
- `reset_progress(self)`
- `set_progress_done(self)`
- `clear(self)`

## 5. Selector QSS yang Dipakai (Referensi untuk halaman baru)
- `QWidget#mainContent`, `QScrollArea#mainScroll`, `QWidget#scrollContent`
- `QLabel#pageTitle`, `QLabel#pageSubtitle`
- `QLabel#sectionTitle`, `QLabel#fieldLabel`, `QLabel#valueLabel`
- `QFrame#card`, `QFrame#cardHighlight`
- `QFrame#dropZone`, `QFrame#dropZoneFilled`
- `QPushButton#btnRunPrimary`, `QPushButton#btnCancel`, `QPushButton#btnBrowse`
- `QPushButton#btnAddPair`, `QPushButton#btnAutoDetect`, `QPushButton#btnClearAll`
- `QLineEdit`, `QComboBox`, `QCheckBox`
- `QFrame#pairRow`, `QFrame#pairRowProcessing`, `QFrame#pairRowDone`, `QFrame#pairRowFailed`
- `QLabel#badgeIdle`, `QLabel#badgeProcessing`, `QLabel#badgeDone`, `QLabel#badgeFailed`

# MP4×MP3 Loop Merger

Aplikasi desktop Windows untuk menggabungkan file video MP4 dengan audio MP3, di mana video di-loop otomatis mengikuti durasi audio. Mendukung mode Single (1 pasang) dan Batch (banyak pasang, diproses berurutan dalam satu kali klik).

## Fitur Utama

- 🎬 **Video Loop Otomatis** — video di-loop hingga durasinya sama persis dengan audio
- 📋 **Mode Batch** — definisikan banyak pasangan sekaligus, proses semua dengan satu klik
- ⚡ **Stream Copy (Cepat)** — tanpa re-encode by default, dengan fallback otomatis
- 🎮 **Deteksi GPU/CPU** — auto-pilih NVIDIA NVENC jika tersedia, fallback ke CPU
- 📊 **Log Real-time** — progress %, ETA, status per file
- 💻 **Standalone .exe** — tidak perlu install Python/FFmpeg

## Cara Menjalankan (Development)

```bash
# Install dependencies
pip install PySide6 psutil

# Jalankan aplikasi
python src/main.py
```

> **Catatan:** Butuh `ffmpeg.exe` dan `ffprobe.exe` di folder `resources/ffmpeg/`

## Cara Build ke .exe

```bash
pip install pyinstaller
pyinstaller build.spec
```

Hasil build ada di `dist/LoopMerger/LoopMerger.exe`

## Struktur Proyek

```
src/
├── main.py                  # Entry point
├── app_window.py            # MainWindow
├── core/
│   ├── models.py            # MixPair dataclass + enums
│   ├── ffmpeg_runner.py     # FFmpeg subprocess + progress parsing
│   ├── hardware_detector.py # GPU/CPU detection
│   └── batch_worker.py      # QThread sequential batch processor
├── pages/
│   ├── single_page.py       # Mode Single UI
│   ├── batch_page.py        # Mode Batch UI
│   └── device_info_page.py  # Hardware info page
├── widgets/
│   ├── log_panel.py         # Log + progress bar
│   ├── pair_row_widget.py   # Satu baris pasangan
│   └── encoding_selector.py # Encoder mode selector
├── utils/
│   ├── ffprobe_utils.py     # Read duration via ffprobe
│   └── path_utils.py        # Output path helpers
└── styles/
    └── theme.qss            # Qt StyleSheet

resources/
├── ffmpeg/                  # ffmpeg.exe + ffprobe.exe (tidak di-commit ke git)
└── icons/                   # app.ico
```

## FFmpeg Command yang Digunakan

**Stream copy (default — cepat):**
```
ffmpeg -stream_loop -1 -i video.mp4 -i audio.mp3 -shortest -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -y output.mp4
```

**Re-encode fallback (CPU):**
```
ffmpeg -stream_loop -1 -i video.mp4 -i audio.mp3 -shortest -map 0:v:0 -map 1:a:0 -c:v libx264 -preset veryfast -c:a aac -b:a 192k -y output.mp4
```

**Re-encode NVENC:**
```
ffmpeg -stream_loop -1 -i video.mp4 -i audio.mp3 -shortest -map 0:v:0 -map 1:a:0 -c:v h264_nvenc -preset p4 -c:a aac -b:a 192k -y output.mp4
```

## Palet Warna UI

| Elemen | Warna |
|--------|-------|
| Background | `#F7F9F8` |
| Tombol primer (Run) | `#8FCB9B` |
| Border | `#E4E7E9` |
| Teks utama | `#374151` |
| Teks sekunder | `#6B7280` |
| Status Done | `#D1FAE5` |
| Status Failed | `#FEE2E2` |
| Log panel | `#1E2327` (dark) |

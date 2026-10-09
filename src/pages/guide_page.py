"""
guide_page.py — Panduan lengkap penggunaan MuliaMixing
Tampil sebagai halaman navigasi di sidebar.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _h(text: str, size: int = 14, color: str = "#E8EDF2", bold: bool = True) -> QLabel:
    """Buat label heading."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size: {size}px; font-weight: {'700' if bold else '500'}; color: {color};"
    )
    lbl.setWordWrap(True)
    return lbl


def _p(text: str, color: str = "#B0BDCC", size: int = 13) -> QLabel:
    """Buat label paragraf biasa."""
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: {size}px; color: {color}; line-height: 1.6;")
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.RichText)
    return lbl


def _divider() -> QFrame:
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #21262D; margin: 4px 0px;")
    return sep


def _badge(text: str, bg: str, fg: str = "#0D1117") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background: {bg}; color: {fg}; font-size: 11px; font-weight: 700;"
        f"border-radius: 4px; padding: 2px 8px;"
    )
    lbl.setFixedHeight(22)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return lbl


def _code(text: str) -> QLabel:
    """Inline code block."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "background: #161B22; border: 1px solid #30363D; border-radius: 5px;"
        "font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;"
        "color: #8FCB9B; padding: 8px 12px;"
    )
    lbl.setWordWrap(True)
    lbl.setTextFormat(Qt.PlainText)
    return lbl


# ─────────────────────────────────────────────────────────────────────────────
# Accordion Section Widget
# ─────────────────────────────────────────────────────────────────────────────

class AccordionSection(QFrame):
    """
    Collapsible section card untuk guide.
    Click header untuk toggle buka/tutup konten.
    """

    def __init__(self, emoji: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._collapsed = False
        self._setup(emoji, title)

    def _setup(self, emoji: str, title: str):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # ── Header (clickable) ────────────────────────────────────────────
        self._header = QFrame()
        self._header.setObjectName("guideAccordionHeader")
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setFixedHeight(50)
        self._header.setStyleSheet(
            "QFrame#guideAccordionHeader {"
            "   background: transparent;"
            "   border-radius: 10px;"
            "   padding: 0px 4px;"
            "}"
            "QFrame#guideAccordionHeader:hover {"
            "   background: rgba(255,255,255,0.03);"
            "}"
        )
        hdr_row = QHBoxLayout(self._header)
        hdr_row.setContentsMargins(16, 0, 16, 0)
        hdr_row.setSpacing(12)

        self._emoji_lbl = QLabel(emoji)
        self._emoji_lbl.setStyleSheet("font-size: 20px;")
        self._emoji_lbl.setFixedWidth(28)
        hdr_row.addWidget(self._emoji_lbl)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #E8EDF2;"
        )
        hdr_row.addWidget(self._title_lbl, stretch=1)

        self._arrow = QLabel("▾")
        self._arrow.setStyleSheet("font-size: 16px; color: #8B9BB4;")
        hdr_row.addWidget(self._arrow)

        self._layout.addWidget(self._header)

        # ── Body ──────────────────────────────────────────────────────────
        self._body = QFrame()
        self._body.setStyleSheet("padding: 0px 16px 16px 16px;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 8, 0, 0)
        self._body_layout.setSpacing(10)
        self._layout.addWidget(self._body)

        # Make header clickable
        self._header.mousePressEvent = self._toggle

    def _toggle(self, event=None):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        self._arrow.setText("▸" if self._collapsed else "▾")

    def add_widget(self, widget: QWidget):
        self._body_layout.addWidget(widget)

    def add_layout(self, layout):
        self._body_layout.addLayout(layout)

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout


# ─────────────────────────────────────────────────────────────────────────────
# Comparison card — dipakai untuk Stream Copy vs Re-encode
# ─────────────────────────────────────────────────────────────────────────────

def _comparison_card(
    title_l: str, items_l: list[tuple[str, str]],
    title_r: str, items_r: list[tuple[str, str]],
    color_l: str = "#8FCB9B", color_r: str = "#E8A0A0",
) -> QFrame:
    """Buat 2-kolom comparison card."""
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame { background: #0D1117; border: 1px solid #21262D;"
        "border-radius: 8px; }"
    )
    row = QHBoxLayout(frame)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(0)

    def _col(title, items, color, border_right=False):
        col_frame = QFrame()
        border = f"border-right: 1px solid #21262D;" if border_right else ""
        col_frame.setStyleSheet(f"QFrame {{ {border} }}")
        col_layout = QVBoxLayout(col_frame)
        col_layout.setContentsMargins(16, 14, 16, 14)
        col_layout.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {color};"
            "letter-spacing: 0.8px; text-transform: uppercase;"
        )
        col_layout.addWidget(t)

        for icon, text in items:
            item_row = QHBoxLayout()
            item_row.setSpacing(8)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 13px;")
            ic.setFixedWidth(20)
            item_row.addWidget(ic)
            tx = QLabel(text)
            tx.setStyleSheet(f"font-size: 12px; color: #B0BDCC;")
            tx.setWordWrap(True)
            item_row.addWidget(tx, stretch=1)
            col_layout.addLayout(item_row)

        col_layout.addStretch()
        return col_frame

    row.addWidget(_col(title_l, items_l, color_l, border_right=True), stretch=1)
    row.addWidget(_col(title_r, items_r, color_r, border_right=False), stretch=1)
    return frame


# ─────────────────────────────────────────────────────────────────────────────
# Info row — icon + teks horizontal
# ─────────────────────────────────────────────────────────────────────────────

def _info_row(icon: str, text: str, icon_color: str = "#8FCB9B") -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)
    ic = QLabel(icon)
    ic.setStyleSheet(f"font-size: 15px; color: {icon_color};")
    ic.setFixedWidth(22)
    ic.setAlignment(Qt.AlignTop)
    row.addWidget(ic)
    tx = _p(text)
    row.addWidget(tx, stretch=1)
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Guide Page
# ─────────────────────────────────────────────────────────────────────────────

class GuidePage(QWidget):
    """Halaman panduan lengkap MuliaMixing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setObjectName("scrollContent")
        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 24, 28, 32)
        outer.setSpacing(16)

        # ── Page Header ───────────────────────────────────────────────────
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        title = QLabel("📖  Panduan Penggunaan")
        title.setObjectName("pageTitle")
        hdr.addWidget(title)
        sub = QLabel("Cara pakai MuliaMixing dari awal sampai hasil — lengkap dengan penjelasan teknis.")
        sub.setObjectName("pageSubtitle")
        hdr.addWidget(sub)
        outer.addLayout(hdr)

        # ── Quick Start Banner ────────────────────────────────────────────
        banner = QFrame()
        banner.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "  stop:0 rgba(143,203,155,0.18), stop:1 rgba(143,203,155,0.05));"
            "border: 1px solid rgba(143,203,155,0.3); border-radius: 10px; }"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(20, 16, 20, 16)
        banner_layout.setSpacing(16)

        rocket = QLabel("🚀")
        rocket.setStyleSheet("font-size: 32px;")
        banner_layout.addWidget(rocket)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(4)
        txt_col.addWidget(_h("Quick Start — 3 Langkah", 14, "#8FCB9B"))
        steps_row = QHBoxLayout()
        steps_row.setSpacing(12)
        for num, step in [("1", "Pilih file .mp4"), ("2", "Pilih file .mp3"), ("3", "Klik Run ▶")]:
            chip = QFrame()
            chip.setStyleSheet(
                "QFrame { background: rgba(143,203,155,0.12); border-radius: 6px; }"
            )
            chip_lay = QHBoxLayout(chip)
            chip_lay.setContentsMargins(10, 6, 10, 6)
            chip_lay.setSpacing(6)
            n = QLabel(num)
            n.setStyleSheet(
                "background: #8FCB9B; color: #0D1117; font-weight: 700;"
                "border-radius: 10px; min-width: 20px; min-height: 20px;"
                "qproperty-alignment: AlignCenter; font-size: 11px;"
            )
            n.setFixedSize(20, 20)
            chip_lay.addWidget(n)
            chip_lay.addWidget(_p(step, "#E8EDF2", 12))
            steps_row.addWidget(chip)
        steps_row.addStretch()
        txt_col.addLayout(steps_row)
        banner_layout.addLayout(txt_col, stretch=1)
        outer.addWidget(banner)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 1 — Single Mode
        # ─────────────────────────────────────────────────────────────────
        s1 = AccordionSection("▶", "Single Mode — Satu Pasangan Video + Audio")
        outer.addWidget(s1)

        s1.add_widget(_p(
            "Single Mode dipakai kalau kamu punya <b>1 file video</b> dan ingin mengganti "
            "audio-nya dengan <b>1 file MP3</b>. Cocok untuk proses cepat satu-satu."
        ))

        s1.add_widget(_h("Langkah-langkah:", 13, "#8FCB9B"))

        for num, icon, step in [
            ("1", "🎬", "<b>File Video (.mp4)</b> — Klik kotak video atau drag & drop file .mp4 ke sana. "
                        "Durasi video akan terbaca otomatis."),
            ("2", "🎵", "<b>File Audio (.mp3)</b> — Klik kotak audio atau drag & drop file .mp3. "
                        "Durasi audio juga terbaca otomatis."),
            ("3", "📝", "<b>Nama Output</b> — Otomatis terisi sebagai <code>[nama_video]_merged.mp4</code>. "
                        "Bisa kamu ubah manual kalau mau."),
            ("4", "📁", "<b>Folder Output</b> — Default: folder yang sama dengan file video. "
                        "Klik tombol <b>Pilih</b> untuk mengubahnya."),
            ("5", "▶", "<b>Klik Run</b> — Proses dimulai. Progress bar akan bergerak. "
                        "Log proses muncul di panel bawah."),
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            nb = QLabel(num)
            nb.setStyleSheet(
                "background: #21262D; color: #8FCB9B; font-weight: 700; font-size: 11px;"
                "border-radius: 10px; qproperty-alignment: AlignCenter;"
            )
            nb.setFixedSize(22, 22)
            row.addWidget(nb)
            ic = QLabel(icon)
            ic.setStyleSheet("font-size: 14px;")
            ic.setFixedWidth(22)
            row.addWidget(ic)
            tx = _p(step)
            row.addWidget(tx, stretch=1)
            s1.add_layout(row)

        s1.add_widget(_divider())
        s1.add_widget(_h("⚠ Catatan Penting:", 12, "#E8C07A"))
        s1.add_widget(_p(
            "• Audio akan di-<b>loop otomatis</b> jika durasinya lebih pendek dari video.<br>"
            "• Output hanya mengambil durasi sepanjang yang <b>lebih pendek</b> antara video dan audio "
            "(flag <code>-shortest</code>).<br>"
            "• Kalau audio lebih panjang dari video, audio akan dipotong otomatis di akhir video."
        ))

        # ─────────────────────────────────────────────────────────────────
        # SECTION 2 — Batch Mode
        # ─────────────────────────────────────────────────────────────────
        s2 = AccordionSection("⚡", "Batch Mode — Banyak Pasangan Sekaligus")
        outer.addWidget(s2)

        s2.add_widget(_p(
            "Batch Mode cocok kalau kamu punya <b>banyak file video</b> yang masing-masing butuh audio berbeda. "
            "Semua diproses otomatis satu per satu tanpa harus nunggu satu-satu."
        ))

        s2.add_widget(_h("Langkah-langkah:", 13, "#8FCB9B"))
        for icon, step in [
            ("⚡", "<b>Auto Deteksi Otomatis</b> — Klik <b>⚡ Auto Deteksi Folder</b> atau drag & drop folder/koleksi file langsung ke aplikasi! Video dan MP3 dengan nama yang cocok (misal <code>shalawat-32.mp4</code> & <code>shalawat-32_loop.mp3</code>) akan langsung dipasangkan otomatis."),
            ("➕", "<b>Tambah Pasangan Manual</b> — Klik tombol <b>+ Tambah Pasangan</b> untuk menambah baris baru tanpa batas."),
            ("🎬", "<b>Isi / Ganti File</b> — Bisa klik tombol Browse atau langsung drag & drop file ke kolom Video / Audio."),
            ("📝", "<b>Nama Output</b> — Otomatis terisi <code>[nama_video]_merged.mp4</code> per baris. Bisa diubah manual."),
            ("📁", "<b>Folder Output Global</b> — Ada di bagian atas toolbar. Semua hasil proses akan disimpan ke folder ini."),
            ("🗑", "<b>Bersihkan Daftar</b> — Klik tombol <b>🗑 Bersihkan</b> untuk mengosongkan daftar jika ingin mulai dari awal."),
            ("⚡", "<b>Klik Run All</b> — Semua pasangan diproses berurutan. Status tiap baris update real-time."),
            ("✕", "<b>Hapus Pasangan</b> — Klik tombol ✕ di kanan baris untuk menghapus pasangan tertentu."),
        ]:
            s2.add_layout(_info_row(icon, step))

        s2.add_widget(_divider())
        s2.add_widget(_h("Tentang Status Badge:", 12, "#8B9BB4"))
        badge_row = QHBoxLayout()
        badge_row.setSpacing(10)
        for text, bg, meaning in [
            ("● Idle", "#2D3748", "Belum diproses"),
            ("⟳ Memproses", "#2A4A6B", "Sedang berjalan"),
            ("✓ Selesai", "#1E4731", "Berhasil"),
            ("✗ Gagal", "#4A1E1E", "Ada error"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(4)
            b = QLabel(text)
            b.setStyleSheet(
                f"background: {bg}; border-radius: 4px; padding: 3px 10px;"
                f"font-size: 12px; font-weight: 600;"
            )
            col.addWidget(b)
            col.addWidget(_p(meaning, "#8B9BB4", 11))
            badge_row.addLayout(col)
        badge_row.addStretch()
        s2.add_layout(badge_row)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 3 — Stream Copy vs Re-encode
        # ─────────────────────────────────────────────────────────────────
        s3 = AccordionSection("⚙️", "Stream Copy vs Re-encode — Apa Bedanya?")
        outer.addWidget(s3)

        s3.add_widget(_p(
            "MuliaMixing punya dua cara memproses file. Kamu bisa pilih di opsi "
            "<b>Always Re-encode</b> di pojok kanan atas, atau biarkan sistem memilih otomatis."
        ))

        comp = _comparison_card(
            "⚡  STREAM COPY (Default)",
            [
                ("🚀", "Ultra cepat — hampir instan"),
                ("🔒", "Tidak mengubah kualitas video sama sekali"),
                ("💾", "Ukuran file tetap sama dengan aslinya"),
                ("🎬", "Cocok: video H.264/H.265, audio AAC/MP3"),
                ("⚠️",  "Bisa gagal jika codec tidak kompatibel dengan container .mp4"),
            ],
            "🔄  RE-ENCODE",
            [
                ("🐢", "Lebih lambat (butuh rendering ulang video)"),
                ("🎨", "Hasilnya lebih kompatibel di semua device"),
                ("📦", "Ukuran file bisa berubah (biasanya lebih kecil)"),
                ("🔧", "Otomatis dipakai saat Stream Copy gagal"),
                ("✅", "Cocok untuk semua jenis codec input"),
            ],
        )
        s3.add_widget(comp)

        s3.add_widget(_divider())
        s3.add_widget(_h("🔄 Alur Otomatis (Mode Default):", 13, "#8FCB9B"))
        flow_frame = QFrame()
        flow_frame.setStyleSheet(
            "QFrame { background: #0D1117; border: 1px solid #21262D; border-radius: 8px; }"
        )
        flow_lay = QVBoxLayout(flow_frame)
        flow_lay.setContentsMargins(16, 14, 16, 14)
        flow_lay.setSpacing(8)
        for step_icon, step_txt, step_color in [
            ("1️⃣", "Coba <b>Stream Copy</b> dulu — cepat, tanpa re-encode", "#8FCB9B"),
            ("✅", "Kalau berhasil → selesai, output langsung tersimpan", "#8FCB9B"),
            ("❌", "Kalau gagal (codec tidak kompatibel) → otomatis fallback ke <b>Re-encode</b>", "#E8A0A0"),
            ("2️⃣", "<b>Re-encode</b> dengan encoder terpilih (NVENC/x264)", "#8B9BB4"),
            ("✅", "Kalau NVENC gagal → otomatis fallback lagi ke <b>CPU x264</b>", "#8FCB9B"),
        ]:
            r = QHBoxLayout()
            r.setSpacing(10)
            ic = QLabel(step_icon)
            ic.setStyleSheet("font-size: 14px;")
            ic.setFixedWidth(24)
            r.addWidget(ic)
            r.addWidget(_p(step_txt, step_color, 12))
            flow_lay.addLayout(r)
        s3.add_widget(flow_frame)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 4 — Encoder Mode
        # ─────────────────────────────────────────────────────────────────
        s4 = AccordionSection("🎮", "Pilihan Encoder — AUTO / NVENC / CPU")
        outer.addWidget(s4)

        s4.add_widget(_p(
            "Encoder hanya berlaku saat proses <b>Re-encode</b> (Stream Copy tidak pakai encoder). "
            "Pilihan encoder ada di dropdown <b>Mode Encoding</b> di topbar."
        ))

        enc_data = [
            ("🤖", "AUTO", "#8FCB9B",
             "Rekomendasi untuk sebagian besar pengguna. "
             "Sistem otomatis deteksi GPU NVIDIA — kalau ada, pakai NVENC. "
             "Kalau tidak ada, pakai CPU x264."),
            ("🎮", "NVENC (GPU NVIDIA)", "#64B5F6",
             "Hardware encoding menggunakan GPU NVIDIA. "
             "Kecepatan 5–10× lebih cepat dari CPU. "
             "Kualitas sangat baik. <b>Hanya tersedia jika kamu punya GPU NVIDIA.</b> "
             "Kalau dipilih tapi tidak ada GPU → proses akan ditolak."),
            ("💻", "CPU (x264)", "#FFB74D",
             "Software encoding menggunakan processor. "
             "Kompatibel di semua komputer. "
             "Lebih lambat dari NVENC tapi <b>output paling kompatibel</b> — "
             "bisa diputar di hampir semua device/platform."),
        ]

        for icon, name, color, desc in enc_data:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: #0D1117; border: 1px solid #21262D;"
                f"border-left: 3px solid {color}; border-radius: 8px; }}"
            )
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(16, 12, 16, 12)
            c_lay.setSpacing(6)
            title_row = QHBoxLayout()
            title_row.setSpacing(8)
            title_row.addWidget(QLabel(icon))
            lbl = QLabel(name)
            lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {color};")
            title_row.addWidget(lbl)
            title_row.addStretch()
            c_lay.addLayout(title_row)
            c_lay.addWidget(_p(desc))
            s4.add_widget(card)

        s4.add_widget(_divider())
        s4.add_widget(_h("☑ Always Re-encode:", 12, "#E8C07A"))
        s4.add_widget(_p(
            "Centang <b>Always Re-encode</b> di topbar untuk <b>melewati</b> fase Stream Copy "
            "dan langsung re-encode. Berguna kalau:<br>"
            "• Kamu tahu audio input tidak kompatibel dengan container MP4<br>"
            "• Kamu ingin hasil yang selalu di-encode ulang dengan quality setting tertentu<br>"
            "• Stream Copy selalu gagal untuk file-file kamu"
        ))

        # ─────────────────────────────────────────────────────────────────
        # SECTION 5 — Format yang Didukung
        # ─────────────────────────────────────────────────────────────────
        s5 = AccordionSection("📂", "Format File yang Didukung")
        outer.addWidget(s5)

        s5.add_widget(_h("Input:", 13, "#8FCB9B"))
        fmt_row = QHBoxLayout()
        for icon, fmt, note in [
            ("🎬", ".mp4", "Video — H.264, H.265, dsb"),
            ("🎵", ".mp3", "Audio — semua bitrate"),
        ]:
            f = QFrame()
            f.setStyleSheet(
                "QFrame { background: #161B22; border: 1px solid #21262D; border-radius: 8px; }"
            )
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 12, 16, 12)
            fl.setSpacing(4)
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(QLabel(icon))
            ext = QLabel(fmt)
            ext.setStyleSheet("font-size: 15px; font-weight: 700; color: #8FCB9B;")
            row.addWidget(ext)
            row.addStretch()
            fl.addLayout(row)
            fl.addWidget(_p(note, "#8B9BB4", 12))
            fmt_row.addWidget(f)
        s5.add_layout(fmt_row)

        s5.add_widget(_h("Output:", 13, "#8FCB9B"))
        s5.add_widget(_p(
            "Selalu <b>.mp4</b> — container yang paling kompatibel di semua platform "
            "(YouTube, TikTok, Instagram, perangkat mobile, dsb)."
        ))

        s5.add_widget(_divider())
        s5.add_widget(_h("Tentang Loop Audio:", 13, "#8FCB9B"))
        s5.add_widget(_p(
            "MuliaMixing otomatis melakukan <b>loop</b> pada audio jika durasinya lebih pendek dari video. "
            "Misalnya video 5 menit + audio 1 menit → audio akan diputar berulang sebanyak 5×. "
            "Seamless, tanpa jeda. Ini sangat berguna untuk background music."
        ))

        # ─────────────────────────────────────────────────────────────────
        # SECTION 6 — Log & Error
        # ─────────────────────────────────────────────────────────────────
        s6 = AccordionSection("📋", "Membaca Log & Mengatasi Error")
        outer.addWidget(s6)

        s6.add_widget(_p(
            "Panel log di bagian bawah menampilkan semua aktivitas proses secara real-time."
        ))

        for symbol, color, meaning in [
            ("✅", "#8FCB9B", "Proses berhasil"),
            ("⚠️", "#E8C07A", "Peringatan — proses tetap jalan tapi ada fallback"),
            ("❌", "#E8A0A0", "Error — proses gagal"),
            ("🏁", "#8B9BB4", "Ringkasan akhir batch"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            ic = QLabel(symbol)
            ic.setStyleSheet("font-size: 14px;")
            ic.setFixedWidth(24)
            row.addWidget(ic)
            row.addWidget(_p(meaning, color, 12))
            s6.add_layout(row)

        s6.add_widget(_divider())
        s6.add_widget(_h("Error Umum & Solusi:", 13, "#E8A0A0"))

        errors = [
            (
                "charmap / codec error",
                "Terjadi encoding error saat baca output FFprobe.",
                "Pastikan nama file tidak mengandung karakter emoji atau simbol aneh. "
                "Atau update ke versi terbaru MuliaMixing."
            ),
            (
                "Could not write header / codec not supported",
                "Stream Copy gagal karena audio codec tidak kompatibel dengan container MP4.",
                "Aktifkan <b>Always Re-encode</b> atau biarkan sistem fallback otomatis."
            ),
            (
                "NVENC not available",
                "GPU NVIDIA tidak terdeteksi atau driver tidak support NVENC.",
                "Ganti encoder ke <b>AUTO</b> atau <b>CPU (x264)</b>."
            ),
            (
                "File not found / path error",
                "File video atau audio tidak ditemukan di lokasi yang dipilih.",
                "Pastikan file tidak dipindah atau dihapus setelah dipilih. Pilih ulang file."
            ),
        ]

        for err_title, cause, solution in errors:
            err_card = QFrame()
            err_card.setStyleSheet(
                "QFrame { background: rgba(232,160,160,0.05); border: 1px solid rgba(232,160,160,0.2);"
                "border-radius: 8px; }"
            )
            ec_lay = QVBoxLayout(err_card)
            ec_lay.setContentsMargins(14, 12, 14, 12)
            ec_lay.setSpacing(6)
            ec_lay.addWidget(_h(f"❌  {err_title}", 12, "#E8A0A0"))
            ec_lay.addLayout(_info_row("🔎", f"<i>Penyebab:</i> {cause}", "#8B9BB4"))
            ec_lay.addLayout(_info_row("💡", f"<i>Solusi:</i> {solution}", "#8FCB9B"))
            s6.add_widget(err_card)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 7 — Tips & Trik
        # ─────────────────────────────────────────────────────────────────
        s7 = AccordionSection("💡", "Tips & Trik")
        outer.addWidget(s7)

        tips = [
            ("⚡", "Untuk file besar, gunakan <b>Stream Copy</b> (default) — hasilnya instan dan kualitas tidak turun."),
            ("🎮", "Punya GPU NVIDIA? Pilih encoder <b>NVENC</b> untuk re-encode 5× lebih cepat."),
            ("📁", "Di Batch Mode, set folder output di awal sebelum mulai isi pasangan — lebih efisien."),
            ("🔄", "Kalau sering gagal, aktifkan <b>Always Re-encode</b> untuk skip Stream Copy."),
            ("📋", "Klik <b>Copy</b> di log panel untuk copy semua log ke clipboard — berguna untuk laporan bug."),
            ("💾", "Nama output otomatis menggunakan nama file video — jadi kalau nama video-nya deskriptif, output-nya juga rapi."),
            ("🗂️", "Gunakan Batch Mode untuk proses massal — bisa sampai puluhan file sekaligus tanpa batas."),
        ]

        for icon, tip in tips:
            s7.add_layout(_info_row(icon, tip))

        # ─────────────────────────────────────────────────────────────────
        # SECTION 8 — Device Info
        # ─────────────────────────────────────────────────────────────────
        s8 = AccordionSection("💻", "Halaman Device Info")
        outer.addWidget(s8)

        s8.add_widget(_p(
            "Halaman <b>Device Info</b> menampilkan informasi hardware komputer kamu "
            "yang relevan untuk proses encoding video."
        ))

        for icon, item, desc in [
            ("🎮", "GPU (Graphics Card)", "Nama GPU, VRAM, dan apakah NVENC (hardware encoding) didukung."),
            ("💻", "CPU (Processor)", "Nama CPU dan jumlah core yang tersedia untuk encoding."),
            ("💾", "RAM", "Total RAM yang bisa digunakan sistem."),
            ("⚡", "NVENC Support", "Status apakah FFmpeg yang bundled bisa menggunakan GPU kamu untuk encoding."),
        ]:
            s8.add_layout(_info_row(icon, f"<b>{item}</b> — {desc}"))

        s8.add_widget(_divider())
        s8.add_widget(_p(
            "Info ini digunakan otomatis oleh sistem saat mode <b>AUTO</b> dipilih — "
            "kamu tidak perlu konfigurasi manual apapun."
        ))

        # ── Footer ────────────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #161B22; border: 1px solid #21262D; border-radius: 10px; }"
        )
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(20, 16, 20, 16)
        foot_lay.setSpacing(12)
        heart = QLabel("🎬")
        heart.setStyleSheet("font-size: 24px;")
        foot_lay.addWidget(heart)
        txt = QVBoxLayout()
        txt.setSpacing(2)
        txt.addWidget(_h("MuliaMixing v1.0.0", 13, "#E8EDF2"))
        txt.addWidget(_p(
            "Dibuat dengan ❤️ untuk kebutuhan produksi konten video dan audio. "
            "Semua proses berjalan lokal di komputer kamu — tidak ada upload ke server.",
            "#484F58", 11
        ))
        foot_lay.addLayout(txt, stretch=1)
        outer.addWidget(footer)

        outer.addStretch()

        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

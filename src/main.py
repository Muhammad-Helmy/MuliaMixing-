"""
main.py — Entry point for MuliaMixing
"""

import sys
import os

# ── Windows: set App User Model ID SEBELUM import apapun ────────────────────
# Ini WAJIB dipanggil sebelum QApplication — ini yang membuat icon muncul di taskbar
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "MuliaMixing"
        )
    except Exception:
        pass  # Gagal silent — tidak crash

# Add project root to path when running from source
if not getattr(sys, "frozen", False):
    project_root = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(project_root)
    if parent not in sys.path:
        sys.path.insert(0, parent)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


def _find_icon() -> str:
    """Find app.ico — works both in frozen EXE and dev mode."""
    if getattr(sys, "frozen", False):
        # PyInstaller: icon ada di _internal/ folder (onedir) atau _MEIPASS (onefile)
        candidates = [
            os.path.join(os.path.dirname(sys.executable), "_internal", "resources", "icons", "app.ico"),
            os.path.join(sys._MEIPASS, "resources", "icons", "app.ico"),  # type: ignore
            os.path.join(os.path.dirname(sys.executable), "resources", "icons", "app.ico"),
        ]
    else:
        # Dev mode: icon di project root/resources/icons/
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base, "resources", "icons", "app.ico"),
        ]

    for p in candidates:
        try:
            if os.path.isfile(p):
                return p
        except Exception:
            pass
    return ""


def apply_windows_taskbar_icon(hwnd: int, icon_path: str):
    """Explicitly assign HICON to Win32 HWND via WM_SETICON and SetClassLongPtr."""
    if sys.platform != "win32" or not icon_path or not os.path.isfile(icon_path):
        return
    try:
        import ctypes
        user32 = ctypes.windll.user32
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x00000010
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        abs_icon_path = os.path.abspath(icon_path)
        hicon_small = user32.LoadImageW(None, abs_icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        hicon_big = user32.LoadImageW(None, abs_icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)

        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)

        GCLP_HICON = -14
        GCLP_HICONSM = -34
        if hasattr(user32, 'SetClassLongPtrW'):
            if hicon_big:
                user32.SetClassLongPtrW(hwnd, GCLP_HICON, hicon_big)
            if hicon_small:
                user32.SetClassLongPtrW(hwnd, GCLP_HICONSM, hicon_small)
        else:
            if hicon_big:
                user32.SetClassLongW(hwnd, GCLP_HICON, hicon_big)
            if hicon_small:
                user32.SetClassLongW(hwnd, GCLP_HICONSM, hicon_small)
    except Exception:
        pass


def main():
    # HiDPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("MuliaMixing")
    app.setApplicationDisplayName("MuliaMixing")
    app.setOrganizationName("MuliaMixing")
    app.setOrganizationDomain("muliamixing.app")

    # Set icon — dipakai untuk taskbar, Alt+Tab, title bar
    icon_path = _find_icon()
    icon = QIcon()
    if icon_path:
        icon = QIcon(icon_path)

    # Pastikan icon valid sebelum di-set
    if not icon.isNull():
        app.setWindowIcon(icon)

    from src.app_window import MainWindow
    window = MainWindow()

    # Set di window level
    if not icon.isNull():
        window.setWindowIcon(icon)

    window.show()

    # Win32 taskbar & window caption icon
    if icon_path:
        apply_windows_taskbar_icon(int(window.winId()), icon_path)

    # Trigger device detection
    window.devicePage._start_detection()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

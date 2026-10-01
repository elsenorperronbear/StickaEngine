"""
StickaEngine — Desktop sticker / GIF hub
Glassmorphism UI (iOS 28 / visionOS) · PyQt6
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import (
    QCoreApplication,
    QObject,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QIcon, QImage, QMovie, QPainter, QPen, QPixmap, QScreen
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_VERSION = "1.0.0"
APP_NAME = "StickaEngine"
ACCENT = "#007AFF"

# GitHub configuration for auto-updates
GITHUB_REPO = "elsenorperronbear/StickaEngine"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GLASS_BORDER = "1px solid rgba(255, 255, 255, 0.12)"
WINDOW_W, WINDOW_H = 980, 640  # Vine-like fixed preset
# Solid dark base — never see-through to desktop (WA_TranslucentBackground still used for round corners)
GLASS_BASE = QColor(18, 20, 28, 245)  # #12141C @ ~0.96
GLASS_RADIUS = 26


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")


def _bundle_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _user_data_dir() -> Path:
    if _is_frozen() or sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / APP_NAME
    return Path(__file__).resolve().parent / "data"


DATA_DIR = _user_data_dir()
LIBRARY_FILE = DATA_DIR / "library.json"
STATE_FILE = DATA_DIR / "session.json"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME / "App"
INSTALL_META = INSTALL_DIR / "version.json"


def _is_installed() -> bool:
    """Check if the application is properly installed."""
    if _is_frozen():
        # Running from PyInstaller bundle, always allow
        return True
    # Check if INSTALL_META exists with correct version
    if INSTALL_META.exists():
        try:
            with open(INSTALL_META, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if data.get("name") == APP_NAME:
                    return True
        except (json.JSONDecodeError, OSError):
            pass
    return False

STYLE_SHEET = f"""
* {{
    font-family: "Segoe UI Variable Text", "SF Pro Text", "Segoe UI", "SF Pro Display", sans-serif;
}}
QMainWindow#StickaHub, QDialog#InstallerDlg {{ background: transparent; }}
#GlassRoot {{
    background-color: transparent;
    border: none;
    border-radius: {GLASS_RADIUS}px;
}}
#TitleBar {{
    background-color: rgba(44, 44, 46, 0.55);
    border-bottom: {GLASS_BORDER};
    border-top-left-radius: {GLASS_RADIUS}px;
    border-top-right-radius: {GLASS_RADIUS}px;
}}
#Sidebar {{
    background-color: rgba(28, 28, 30, 0.92);
    border-right: {GLASS_BORDER};
    border-bottom-left-radius: {GLASS_RADIUS}px;
}}
#ContentPane, #PageRoot {{
    background-color: rgba(18, 20, 28, 0.98);
    border: none;
    border-bottom-right-radius: {GLASS_RADIUS}px;
}}
#GlassCard {{
    background-color: rgba(44, 44, 46, 0.92);
    border: {GLASS_BORDER};
    border-radius: 20px;
}}
#GlassCard[selected="true"] {{
    border: 1.5px solid {ACCENT};
    background-color: rgba(0, 122, 255, 0.22);
}}
#InsetGroup {{
    background-color: rgba(44, 44, 46, 0.95);
    border: {GLASS_BORDER};
    border-radius: 20px;
}}
#PreviewPane {{
    background-color: rgba(0, 0, 0, 0.55);
    border: {GLASS_BORDER};
    border-radius: 20px;
}}
QLabel {{ color: rgba(255, 255, 255, 0.95); background: transparent; }}
QLabel#Muted {{ color: rgba(235, 235, 245, 0.55); }}
QLineEdit {{
    background-color: rgba(118, 118, 128, 0.22);
    border: {GLASS_BORDER};
    border-radius: 16px;
    padding: 11px 16px;
    color: white;
    selection-background-color: {ACCENT};
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid rgba(0, 122, 255, 0.7);
    background-color: rgba(118, 118, 128, 0.28);
}}
QPushButton {{
    background-color: rgba(118, 118, 128, 0.24);
    color: white;
    border: {GLASS_BORDER};
    border-radius: 14px;
    padding: 9px 16px;
    font-weight: 500;
    font-size: 13px;
}}
QPushButton:hover {{ background-color: rgba(118, 118, 128, 0.36); }}
QPushButton:pressed {{ background-color: rgba(118, 118, 128, 0.18); }}
#NavButton {{
    background: transparent;
    border: none;
    border-radius: 14px;
    color: rgba(235, 235, 245, 0.55);
    text-align: left;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 500;
}}
#NavButton:hover {{
    background-color: rgba(118, 118, 128, 0.22);
    color: rgba(255, 255, 255, 0.95);
}}
#NavButton[active="true"] {{
    background-color: rgba(0, 122, 255, 0.28);
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}}
#AddCapsule {{
    background-color: {ACCENT};
    border: none;
    border-radius: 20px;
    color: #FFFFFF;
    font-weight: 600;
    padding: 8px 20px;
}}
#AddCapsule:hover {{ background-color: #0A84FF; }}
#LaunchButton {{
    background-color: {ACCENT};
    border: none;
    border-radius: 18px;
    color: white;
    font-weight: 700;
    font-size: 14px;
}}
#LaunchButton:hover {{ background-color: #0A84FF; }}
#LaunchButton:disabled {{
    background-color: rgba(0, 122, 255, 0.28);
    color: rgba(255, 255, 255, 0.45);
}}
#TitleBtn {{
    background: transparent;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
    color: rgba(255, 255, 255, 0.7);
}}
#TitleBtn:hover {{ background-color: rgba(255, 255, 255, 0.12); color: white; }}
#CloseBtn {{
    background: transparent;
    border: none;
    border-radius: 10px;
    font-size: 13px;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
    color: rgba(255, 255, 255, 0.7);
}}
#CloseBtn:hover {{ background-color: #E81123; color: white; }}
#DangerBtn {{
    background: transparent;
    border: 1px solid rgba(255, 69, 58, 0.4);
    color: #FF453A;
    border-radius: 14px;
}}
#DangerBtn:hover {{ background-color: rgba(255, 69, 58, 0.18); }}
#InstallBtn {{
    background-color: {ACCENT};
    border: none;
    border-radius: 18px;
    font-weight: 700;
    min-height: 46px;
    color: white;
}}
#InstallBtn:hover {{ background-color: #0A84FF; }}
QSlider::groove:horizontal {{
    height: 4px;
    background: rgba(255, 255, 255, 0.16);
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
    border: 2px solid rgba(255, 255, 255, 0.9);
}}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.22);
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
#FloatChrome {{
    background-color: rgba(28, 28, 30, 0.96);
    border: 1px solid rgba(0, 122, 255, 0.55);
    border-radius: 14px;
}}
#FloatChromeBtn {{
    background-color: rgba(118, 118, 128, 0.28);
    border: {GLASS_BORDER};
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}}
#FloatChromeBtn:hover {{ background-color: rgba(0, 122, 255, 0.4); }}
QProgressBar {{
    background: rgba(118, 118, 128, 0.24);
    border: {GLASS_BORDER};
    border-radius: 10px;
    text-align: center;
    color: white;
    max-height: 18px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #007AFF, stop:1 #5AC8FA);
    border-radius: 9px;
}}
"""


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_library() -> list[dict]:
    ensure_data_dir()
    if not LIBRARY_FILE.exists():
        return []
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return [i for i in data if Path(i.get("path", "")).exists()]
    except (json.JSONDecodeError, OSError):
        return []


def save_library(items: list[dict]) -> None:
    ensure_data_dir()
    with open(LIBRARY_FILE, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2, ensure_ascii=False)


def load_session() -> dict:
    ensure_data_dir()
    if not STATE_FILE.exists():
        return {"stickers_active": True, "floats": []}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {"stickers_active": True, "floats": []}


def save_session(state: dict) -> None:
    ensure_data_dir()
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)





def is_apng(path: str) -> bool:
    """Check if a file is an APNG (Animated PNG)."""
    try:
        if not path.lower().endswith('.png'):
            return False
        # Try with Pillow first
        try:
            from PIL import Image
            with Image.open(path) as img:
                return getattr(img, 'is_animated', False) and getattr(img, 'n_frames', 1) > 1
        except ImportError:
            pass
        # Fallback: check for acTL chunk
        with open(path, 'rb') as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                return False
            while True:
                chunk_length_bytes = f.read(4)
                if len(chunk_length_bytes) < 4:
                    break
                chunk_length = int.from_bytes(chunk_length_bytes, 'big')
                chunk_type = f.read(4)
                if chunk_type == b'acTL':
                    return True
                if chunk_length == 0:
                    break
                f.read(chunk_length + 4)
        return False
    except (OSError, IOError):
        return False


class APNGMovie(QObject):
    """Custom movie class for APNG animation using Pillow."""
    frame_ready = pyqtSignal(QPixmap)
    
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path
        self.frames = []
        self.current_frame = 0
        self.fps = 15
        self._load_frames()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
    
    def _load_frames(self):
        """Load all frames from APNG using Pillow."""
        try:
            from PIL import Image
            with Image.open(self.path) as img:
                self.fps = getattr(img, 'info', {}).get('duration', 100)
                if self.fps == 0:
                    self.fps = 15
                else:
                    self.fps = 1000 / self.fps  # Convert ms to fps approximation
                
                n_frames = getattr(img, 'n_frames', 1)
                for frame_idx in range(n_frames):
                    img.seek(frame_idx)
                    # Convert PIL Image to QPixmap
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    data = img.tobytes('raw', 'RGBA')
                    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.frames.append(pixmap)
        except (ImportError, OSError):
            self.frames = []
    
    def start(self):
        """Start the animation."""
        if self.frames:
            self.current_frame = 0
            frame_duration = int(1000 / min(60, max(1, self.fps)))
            self.timer.start(frame_duration)
            self.frame_ready.emit(self.frames[0])
    
    def stop(self):
        """Stop the animation."""
        self.timer.stop()
    
    def next_frame(self):
        """Emit next frame."""
        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.frame_ready.emit(self.frames[self.current_frame])
    
    def isValid(self) -> bool:
        """Check if movie is valid."""
        return len(self.frames) > 0
    
    def setSpeed(self, speed: int):
        """Set animation speed (percentage)."""
        if speed <= 0:
            self.timer.stop()
        else:
            frame_duration = int(1000 / min(60, max(1, self.fps * speed / 100)))
            if self.timer.isActive():
                self.timer.start(frame_duration)


def create_default_icon(path: Path) -> bool:
    """Create a simple default icon for the app."""
    try:
        from PIL import Image, ImageDraw
        # Create 32x32 icon with blue circle
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 28, 28), fill=(0, 122, 255, 255))
        img.save(str(path))
        return True
    except ImportError:
        return False




def apply_soft_shadow(widget: QWidget, blur: int = 28, dy: int = 8) -> None:
    """Drop-shadow for solid surfaces only — avoid on translucent glass roots."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(0, 0, 0, 120))
    widget.setGraphicsEffect(effect)


def hi_dpi_pixmap(path: str, w: int, h: int, widget: QWidget | None = None) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return pix
    dpr = widget.devicePixelRatioF() if widget else 1.0
    target = QSize(max(1, int(w * dpr)), max(1, int(h * dpr)))
    scaled = pix.scaled(
        target,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    scaled.setDevicePixelRatio(dpr)
    return scaled


def get_device_pixel_ratio(widget: QWidget | None = None) -> float:
    """Get device pixel ratio for HiDPI scaling."""
    if widget:
        return widget.devicePixelRatioF()
    from PyQt6.QtGui import QScreen
    from PyQt6.QtCore import QCoreApplication
    screen = QCoreApplication.primaryScreen()
    if screen:
        return screen.devicePixelRatio()
    return 1.0

def hi_dpi_size(w: int, h: int, widget: QWidget | None = None) -> QSize:
    """Scale size for HiDPI displays."""
    dpr = get_device_pixel_ratio(widget)
    return QSize(max(1, int(w * dpr)), max(1, int(h * dpr)))

def create_hi_dpi_movie(path: str, w: int, h: int, widget: QWidget | None = None) -> QMovie:
    """Create a QMovie with proper HiDPI scaling."""
    movie = QMovie(path)
    if movie.isValid():
        size = hi_dpi_size(w, h, widget)
        movie.setScaledSize(size)
        movie.setCacheMode(QMovie.CacheMode.CacheAll)
        movie.setSpeed(100)
    return movie



def installed_version() -> str | None:
    if not INSTALL_META.exists():
        exe = INSTALL_DIR / f"{APP_NAME}.exe"
        return "0.0.0" if exe.exists() else None
    try:
        with open(INSTALL_META, "r", encoding="utf-8") as fh:
            return json.load(fh).get("version")
    except (json.JSONDecodeError, OSError):
        return None



def check_for_updates(current_version: str) -> dict | None:
    """Check GitHub for newer releases."""
    import urllib.request
    import json
    
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        latest_version = data.get("tag_name", "").lstrip("v")
        if not latest_version:
            return None
        
        if version_tuple(latest_version) > version_tuple(current_version):
            return {
                "version": latest_version,
                "url": data.get("html_url", RELEASES_URL),
                "name": data.get("name", f"v{latest_version}"),
                "body": data.get("body", ""),
                "assets": [a["browser_download_url"] for a in data.get("assets", [])]
            }
        return None
    except Exception as e:
        print(f"Update check error: {e}")
        return None


def download_file(url: str, target_path: Path) -> bool:
    """Download a file from URL."""
    import urllib.request
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(target_path))
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def version_tuple(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


# ---------------------------------------------------------------------------
# Opaque glass shell (fixes desktop bleed-through)
# ---------------------------------------------------------------------------

class GlassRootWidget(QWidget):
    """Paints a nearly-opaque rounded glass plate so content is always visible."""

    def __init__(self, parent=None, radius: int = GLASS_RADIUS):
        super().__init__(parent)
        self.setObjectName("GlassRoot")
        self._radius = radius
        self._base = QColor(GLASS_BASE)
        self.setAutoFillBackground(False)
        # Force opaque background to prevent transparency issues
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        # Fill entire widget with base color first (prevents transparency)
        rect = self.rect()
        p.fillRect(rect, self._base)
        
        # Now draw the glass effect layers
        adjusted_rect = rect.adjusted(1, 1, -1, -1)
        for inset, alpha in ((0, 50), (1, 28), (2, 14)):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, alpha))
            p.drawRoundedRect(
                adjusted_rect.adjusted(inset, inset + 1, -inset, -inset),
                self._radius,
                self._radius,
            )
        
        # Draw border
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 36), 1.0))
        p.drawRoundedRect(adjusted_rect, self._radius, self._radius)
        
        p.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
        p.drawRoundedRect(adjusted_rect.adjusted(1, 1, -1, -1), self._radius - 1, self._radius - 1)
        
        p.end()


# ---------------------------------------------------------------------------
# iOS-style Activar / Desactivar toggle
# ---------------------------------------------------------------------------

class ActiveToggle(QWidget):
    """Green check / red X pill toggle (Activar / Desactivar)."""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked: bool = True):
        super().__init__(parent)
        self.setFixedSize(124, 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._knob_x = 88.0 if checked else 4.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, animate: bool = True) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        end = 88.0 if checked else 4.0
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._knob_x)
            self._anim.setEndValue(end)
            self._anim.start()
        else:
            self._knob_x = end
            self.update()
        self.toggled.emit(checked)

    def _on_anim(self, value):
        self._knob_x = float(value)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        r = self.rect().adjusted(1, 1, -1, -1)
        bg = QColor(52, 199, 89) if self._checked else QColor(255, 59, 48)
        # Soft outer ring
        p.setPen(QPen(QColor(255, 255, 255, 40), 1.25))
        p.setBrush(bg)
        p.drawRoundedRect(r, 19, 19)

        font = QFont("Segoe UI Variable Text", 13, QFont.Weight.DemiBold)
        if not font.exactMatch():
            font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QColor(255, 255, 255))
        if self._checked:
            p.drawText(QRect(12, 0, 42, 38), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "✓")
        else:
            p.drawText(QRect(72, 0, 42, 38), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, "✕")

        # Knob with soft edge
        knob = QRect(int(self._knob_x), 4, 30, 30)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(knob.adjusted(1, 2, 1, 2))
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(knob)
        p.end()


# ---------------------------------------------------------------------------
# Floating sticker
# ---------------------------------------------------------------------------

class ResizeHandle(QWidget):
    def __init__(self, parent: "FloatingSticker"):
        super().__init__(parent)
        self._sticker = parent
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setStyleSheet(
            f"background: {ACCENT}; border-radius: 7px; border: 1px solid rgba(255,255,255,0.5);"
        )
        self._origin = QPoint()
        self._geo = QRect()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.globalPosition().toPoint()
            self._geo = self._sticker.geometry()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._origin
            w = max(80, self._geo.width() + delta.x())
            h = max(80, self._geo.height() + delta.y())
            self._sticker.resize(w, h)
            self._sticker._layout_chrome()
            self._sticker.geometry_changed.emit(self._sticker)
            event.accept()


class FloatingSticker(QWidget):
    closed = pyqtSignal(object)
    mode_changed = pyqtSignal(object, str)
    geometry_changed = pyqtSignal(object)

    def __init__(self, gif_path: str, fps: int = 15, size: QSize | None = None, parent=None):
        super().__init__(parent)
        self.gif_path = str(Path(gif_path).resolve())
        self.fps = max(1, min(60, fps))
        self.mode = "edit"
        self._drag_offset = QPoint()
        self._dragging = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(80, 80)
        if size:
            self.resize(size)
        else:
            self.resize(280, 280)

        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setScaledContents(True)
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Handle APNG files with APNGMovie
        if is_apng(self.gif_path):
            self.apng_movie = APNGMovie(self.gif_path, self)
            if self.apng_movie.isValid():
                self.apng_movie.frame_ready.connect(self.gif_label.setPixmap)
                speed = int(100 * (self.fps / 15.0))
                self.apng_movie.setSpeed(max(10, min(400, speed)))
                self.apng_movie.start()
                self.gif_label.setToolTip("APNG (Animated PNG)")
            else:
                # Fallback to static image
                pix = hi_dpi_pixmap(self.gif_path, self.width(), self.height(), self)
                if not pix.isNull():
                    self.gif_label.setPixmap(pix)
                    self.gif_label.setToolTip("APNG (Animated PNG) - Displayed as static")
            self.movie = QMovie()  # Dummy for compatibility
        else:
            self.apng_movie = None
            self.movie = create_hi_dpi_movie(self.gif_path, self.width(), self.height(), self)
            if self.movie.isValid():
                speed = int(100 * (self.fps / 15.0))
                self.movie.setSpeed(max(10, min(400, speed)))
                self.gif_label.setMovie(self.movie)
                self.movie.start()

        self.chrome = QFrame(self)
        self.chrome.setObjectName("FloatChrome")
        chrome_layout = QHBoxLayout(self.chrome)
        chrome_layout.setContentsMargins(8, 6, 8, 6)
        chrome_layout.setSpacing(6)

        title = QLabel(Path(self.gif_path).stem[:18])
        title.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.75);")
        chrome_layout.addWidget(title)
        chrome_layout.addStretch()

        self.lock_btn = QPushButton("LOCK")
        self.lock_btn.setObjectName("FloatChromeBtn")
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.clicked.connect(self.enter_lock_mode)
        chrome_layout.addWidget(self.lock_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("FloatChromeBtn")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        chrome_layout.addWidget(self.close_btn)

        self.handle = ResizeHandle(self)
        self._layout_chrome()
        self._apply_edit_chrome()
        
        # Animación de aparición
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)
        
        self._fade_in_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_in_anim.setDuration(300)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def set_fps(self, fps: int) -> None:
        self.fps = max(1, min(60, fps))
        if hasattr(self, 'apng_movie') and self.apng_movie and self.apng_movie.isValid():
            speed = int(100 * (self.fps / 15.0))
            self.apng_movie.setSpeed(max(10, min(400, speed)))
        elif self.movie and self.movie.isValid():
            speed = int(100 * (self.fps / 15.0))
            self.movie.setSpeed(max(10, min(400, speed)))

    def set_sticker_size(self, w: int, h: int) -> None:
        self.resize(max(80, w), max(80, h))
        self._layout_chrome()
        # Recreate movie with new size for proper HiDPI scaling
        if self.movie:
            old_path = self.movie.fileName()
            self.movie.stop()
            self.movie.setFileName("")
            self.movie = create_hi_dpi_movie(old_path, self.width(), self.height(), self)
            if self.movie.isValid():
                speed = int(100 * (self.fps / 15.0))
                self.movie.setSpeed(max(10, min(400, speed)))
                self.gif_label.setMovie(self.movie)
                self.movie.start()
        self.geometry_changed.emit(self)

    def _layout_chrome(self) -> None:
        margin = 10 if self.mode == "edit" else 0
        bar_h = 36 if self.mode == "edit" else 0
        self.gif_label.setGeometry(
            margin,
            margin + bar_h,
            max(1, self.width() - margin * 2),
            max(1, self.height() - margin * 2 - bar_h),
        )
        if self.mode == "edit":
            self.chrome.setGeometry(margin, margin, max(1, self.width() - margin * 2), 32)
            self.handle.move(self.width() - 18, self.height() - 18)
            self.handle.raise_()
            self.chrome.raise_()

    def resizeEvent(self, event):
        self._layout_chrome()
        # Update movie scaled size on resize for HiDPI
        if self.movie and self.movie.isValid():
            self.movie.setScaledSize(hi_dpi_size(self.gif_label.width(), self.gif_label.height(), self))
        super().resizeEvent(event)

    def paintEvent(self, event):
        if self.mode == "edit":
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor(0, 122, 255, 220))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 12, 12)
            painter.end()
        super().paintEvent(event)

    def _apply_edit_chrome(self) -> None:
        self.mode = "edit"
        self.chrome.show()
        self.handle.show()
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.show()
        self._layout_chrome()
        self.update()
        self.mode_changed.emit(self, "edit")

    def enter_lock_mode(self) -> None:
        self.mode = "lock"
        self.chrome.hide()
        self.handle.hide()
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setWindowFlags(flags)
        self.show()
        self._layout_chrome()
        self.update()
        self.mode_changed.emit(self, "lock")

    def enter_edit_mode(self) -> None:
        self._apply_edit_chrome()
    
    def showEvent(self, event):
        if self._opacity_effect.opacity() == 0.0:
            self._fade_in_anim.start()
        super().showEvent(event)

    def mousePressEvent(self, event):
        if self.mode != "edit":
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.mode != "edit" or not self._dragging:
            return
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self.geometry_changed.emit(self)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        super().mouseReleaseEvent(event)

    def closeEvent(self, event):
        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_out.setDuration(200)
        fade_out.setStartValue(self._opacity_effect.opacity())
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        
        def _finish_close():
            if self.movie:
                self.movie.stop()
                self.movie.setFileName("")
            self.closed.emit(self)
            super(FloatingSticker, self).closeEvent(event)
        
        fade_out.finished.connect(_finish_close)
        fade_out.start()
        event.ignore()


# ---------------------------------------------------------------------------
# Library card
# ---------------------------------------------------------------------------

class AnimationCard(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, name: str, path: str, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setFixedSize(152, 178)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.name = name
        self.path = path
        self._movie: QMovie | None = None
        self._apng_movie = None
        self._loaded = False  # Lazy loading flag

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.img = QLabel()
        self.img.setFixedSize(128, 108)
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img.setStyleSheet(
            "background-color: rgba(0,0,0,0.4); border-radius: 14px;"
        )
        
        # Placeholder image
        placeholder = QPixmap(128, 108)
        placeholder.fill(QColor(0, 0, 0, 100))
        self.img.setPixmap(placeholder)

        # Store path for lazy loading
        self._path = path
        self._name = name

        self.name_label = QLabel(name)
        self.name_label.setObjectName("Muted")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 11px;")
        self.name_label.setWordWrap(True)

        layout.addWidget(self.img, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Lazy load when selected
        if selected and not self._loaded:
            self._load_content()
    
    def _load_content(self) -> None:
        """Lazy load the actual content (GIF, APNG, or image)."""
        if self._loaded:
            return
        self._loaded = True
        
        path = self._path
        if path.lower().endswith(".gif"):
            self._movie = create_hi_dpi_movie(path, 128, 108, self)
            if self._movie.isValid():
                self.img.setMovie(self._movie)
                self._movie.start()
        elif is_apng(path):
            self._apng_movie = APNGMovie(path, self)
            if self._apng_movie.isValid():
                self._apng_movie.frame_ready.connect(self.img.setPixmap)
                self._apng_movie.start()
                self.img.setToolTip("APNG (Animated PNG)")
            else:
                scaled = hi_dpi_pixmap(path, 128, 108, self)
                if not scaled.isNull():
                    self.img.setPixmap(scaled)
                    self.img.setToolTip("APNG (Animated PNG) - Displayed as static")
        else:
            scaled = hi_dpi_pixmap(path, 128, 108, self)
            if not scaled.isNull():
                self.img.setPixmap(scaled)
    
    def showEvent(self, event):
        """Lazy load when card becomes visible."""
        if not self._loaded:
            self._load_content()
        super().showEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def stop_movie(self) -> None:
        if self._movie:
            self._movie.stop()


# ---------------------------------------------------------------------------
# Installer dialog
# ---------------------------------------------------------------------------

class InstallerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InstallerDlg")
        self.setWindowTitle(f"{APP_NAME} Installer")
        self.setFixedSize(480, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE_SHEET)
        
        # Try to set window icon
        try:
            icon_path = _bundle_dir() / "icon.png"
            if not icon_path.exists():
                icon_path = Path(tempfile.gettempdir()) / "animaengine_icon.png"
                create_default_icon(icon_path)
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass
        self._drag = QPoint()
        self._result_msg = ""
        self._opened = False
        self._closing = False
        self._target_geo = QRect()

        outer = GlassRootWidget(self, radius=24)
        outer.setGeometry(0, 0, 440, 340)
        self._shell = outer

        lay = QVBoxLayout(outer)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(14)

        top = QHBoxLayout()
        brand = QLabel(f"●  {APP_NAME}")
        brand.setStyleSheet(f"font-weight: 700; color: {ACCENT}; font-size: 14px;")
        close = QPushButton("✕")
        close.setObjectName("CloseBtn")
        close.clicked.connect(self.reject)
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(close)
        lay.addLayout(top)

        title = QLabel("Instalar en el escritorio")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        lay.addWidget(title)

        self.status = QLabel(self._status_text())
        self.status.setObjectName("Muted")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("font-size: 12px;")
        lay.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        lay.addWidget(self.progress)

        self.detail = QLabel("")
        self.detail.setObjectName("Muted")
        self.detail.setStyleSheet("font-size: 11px;")
        lay.addWidget(self.detail)

        lay.addStretch()

        self.action_btn = QPushButton(self._action_label())
        self.action_btn.setObjectName("InstallBtn")
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self._run_install)
        lay.addWidget(self.action_btn)

        cancel = QPushButton("Cerrar")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        lay.addWidget(cancel)

    def showEvent(self, event):
        super().showEvent(event)
        if self._opened:
            return
        self._opened = True
        self._play_open()

    def _play_open(self) -> None:
        self._target_geo = self.geometry()
        geo = self._target_geo
        cx, cy = geo.center().x(), geo.center().y()
        sw, sh = int(geo.width() * 0.92), int(geo.height() * 0.92)
        start = QRect(cx - sw // 2, cy - sh // 2, sw, sh)
        self.setWindowOpacity(0.0)
        self.setGeometry(start)

        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(300)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        scale = QPropertyAnimation(self, b"geometry", self)
        scale.setDuration(300)
        scale.setStartValue(start)
        scale.setEndValue(geo)
        scale.setEasingCurve(QEasingCurve.Type.OutCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(fade)
        group.addAnimation(scale)
        group.start()
        self._open_anim = group

    def _close_animated(self, accepted: bool) -> None:
        if self._closing:
            return
        self._closing = True
        fade = QPropertyAnimation(self, b"windowOpacity", self)
        fade.setDuration(220)
        fade.setStartValue(self.windowOpacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InCubic)

        geo = self.geometry()
        cx, cy = geo.center().x(), geo.center().y()
        ew, eh = int(geo.width() * 0.94), int(geo.height() * 0.94)
        end = QRect(cx - ew // 2, cy - eh // 2, ew, eh)
        scale = QPropertyAnimation(self, b"geometry", self)
        scale.setDuration(220)
        scale.setStartValue(geo)
        scale.setEndValue(end)
        scale.setEasingCurve(QEasingCurve.Type.InCubic)

        group = QParallelAnimationGroup(self)
        group.addAnimation(fade)
        group.addAnimation(scale)

        def _finish():
            if accepted:
                QDialog.accept(self)
            else:
                QDialog.reject(self)

        group.finished.connect(_finish)
        group.start()
        self._close_anim = group

    def accept(self) -> None:
        self._close_animated(True)

    def reject(self) -> None:
        self._close_animated(False)

    def _status_text(self) -> str:
        ver = installed_version()
        if ver is None:
            return (
                f"Se instalará {APP_NAME} {APP_VERSION} en:\n"
                f"{INSTALL_DIR}\n+ acceso directo en el Escritorio."
            )
        if version_tuple(ver) >= version_tuple(APP_VERSION):
            return f"Ya está instalada la versión {ver}.\nEstás en la última versión ({APP_VERSION})."
        return f"Instalada: {ver} → Disponible: {APP_VERSION}\nPuedes actualizar ahora."

    def _action_label(self) -> str:
        ver = installed_version()
        if ver is None:
            return "Instalar"
        if version_tuple(ver) >= version_tuple(APP_VERSION):
            return "Ya está en su última versión"
        return "Actualizar"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag)

    def _set_progress(self, value: int, text: str) -> None:
        self.progress.setValue(value)
        self.detail.setText(text)
        QApplication.processEvents()

    def _source_payload(self) -> Path | None:
        """Folder that contains StickaEngine.exe + _internal (or script dir in dev)."""
        if _is_frozen():
            # Running from dist/StickaEngine/StickaEngine.exe
            return Path(sys.executable).resolve().parent
        # Dev: prefer already-built dist
        dist = Path(__file__).resolve().parent / "dist" / APP_NAME
        if (dist / f"{APP_NAME}.exe").exists():
            return dist
        return None

    def _create_shortcut(self, target: Path) -> None:
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        lnk = desktop / f"{APP_NAME}.lnk"
        # PowerShell WScript shortcut
        ps = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{lnk}"); '
            f'$s.TargetPath = "{target}"; '
            f'$s.WorkingDirectory = "{target.parent}"; '
            f'$s.Description = "{APP_NAME} {APP_VERSION}"; '
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=False,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def _run_install(self) -> None:
        ver = installed_version()
        if ver is not None and version_tuple(ver) >= version_tuple(APP_VERSION):
            self.status.setText(f"Ya está en su última versión ({APP_VERSION}).")
            self.action_btn.setText("Ya está en su última versión")
            self.action_btn.setEnabled(False)
            self._set_progress(100, "Nada que hacer.")
            return

        src = self._source_payload()
        if src is None:
            self.status.setText(
                "No se encontró el paquete compilado.\n"
                "Compila con PyInstaller primero (dist/StickaEngine)."
            )
            self._set_progress(0, "Falta dist/StickaEngine")
            return

        self.action_btn.setEnabled(False)
        try:
            self._set_progress(10, "Preparando carpeta…")
            INSTALL_DIR.mkdir(parents=True, exist_ok=True)

            self._set_progress(30, "Copiando archivos…")
            # Copy onedir tree
            for item in src.iterdir():
                dest = INSTALL_DIR / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest, ignore_errors=True)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

            self._set_progress(70, "Escribiendo versión…")
            with open(INSTALL_META, "w", encoding="utf-8") as fh:
                json.dump({"version": APP_VERSION, "name": APP_NAME}, fh, indent=2)

            exe = INSTALL_DIR / f"{APP_NAME}.exe"
            self._set_progress(85, "Creando acceso directo…")
            if exe.exists():
                self._create_shortcut(exe)

            self._set_progress(100, "Listo.")
            verb = "actualizada" if ver else "instalada"
            self.status.setText(
                f"{APP_NAME} {APP_VERSION} {verb} correctamente.\n"
                f"Acceso directo en el Escritorio."
            )
            self.action_btn.setText("Ya está en su última versión")
        except OSError as exc:
            self.status.setText(f"Error al instalar:\n{exc}")
            self.action_btn.setEnabled(True)
            self.action_btn.setText(self._action_label())
            self._set_progress(0, "Falló la instalación")


# ---------------------------------------------------------------------------
# Main hub
# ---------------------------------------------------------------------------

class StickaEngineHub(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("StickaHub")
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Create and set central widget with opaque background
        central_widget = QWidget()
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(palette.ColorRole.Window, GLASS_BASE)
        central_widget.setPalette(palette)
        self.setCentralWidget(central_widget)
        self.setStyleSheet(STYLE_SHEET)

        self.library: list[dict] = load_library()
        self.session = load_session()
        self._window_geometry = self._load_window_geometry()
        self.cards: list[AnimationCard] = []
        self.selected_card: AnimationCard | None = None
        self.active_floats: list[FloatingSticker] = []
        self.focused_float: FloatingSticker | None = None
        self.stickers_active = bool(self.session.get("stickers_active", True))
        self._preview_movie: QMovie | None = None
        self._drag_pos = QPoint()
        self._sidebar_expanded = True
        self._sidebar_anim: QPropertyAnimation | None = None
        self._fade_anim: QPropertyAnimation | None = None
        self._nav_labels = {
            "library": "  Library",
            "editor": "  Editor",
            "workshop": "  Workshop",
            "settings": "  Settings",
        }

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(300)  # Guardar más frecuentemente
        self._autosave_timer.timeout.connect(self._flush_autosave)
        
        # Timer para guardar al mover/redimensionar stickers
        self._sticker_autosave_timer = QTimer(self)
        self._sticker_autosave_timer.setSingleShot(True)
        self._sticker_autosave_timer.setInterval(500)
        self._sticker_autosave_timer.timeout.connect(self._flush_autosave)

        self._build_ui()
        self._restore_window_geometry()
        self._rebuild_grid()
        self._select_tab("library")
        self._sync_install_button()

        # Spring animation for hub
        self._opacity = QGraphicsOpacityEffect(self.centralWidget())
        self.centralWidget().setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)
        
        fade = QPropertyAnimation(self._opacity, b"opacity", self)
        fade.setDuration(400)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.Type.OutBack)  # Spring effect
        fade.start()
        self._boot_fade = fade

    # -- UI -----------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QWidget()
        outer.setObjectName("GlassRoot")
        self.setCentralWidget(outer)
        apply_soft_shadow(outer, blur=40, dy=12)

        root = QVBoxLayout(outer)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_title_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = self._build_sidebar()
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentPane")
        self.page_library = self._build_library_page()
        self.page_editor = self._build_editor_page()
        self.page_workshop = self._build_placeholder_page(
            "Workshop", "Compose and remix stickers. Coming soon."
        )
        self.page_settings = self._build_settings_page()
        self.page_marketplace = self._build_marketplace_page()
        for p in (self.page_library, self.page_editor, self.page_workshop, self.page_marketplace, self.page_settings):
            self.stack.addWidget(p)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TitleBar")
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 10, 0)
        layout.setSpacing(8)

        accent_dot = QLabel("●")
        accent_dot.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
        brand = QLabel(APP_NAME)
        brand.setStyleSheet("font-weight: 700; font-size: 13px; color: white;")
        layout.addWidget(accent_dot)
        layout.addWidget(brand)
        layout.addStretch()

        self.min_btn = QPushButton("−")
        self.min_btn.setObjectName("TitleBtn")
        self.min_btn.clicked.connect(self.showMinimized)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.clicked.connect(self.close)

        layout.addWidget(self.min_btn)
        layout.addWidget(self.close_btn)

        bar.mousePressEvent = self._title_press  # type: ignore
        bar.mouseMoveEvent = self._title_move  # type: ignore
        return bar

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        side.setFixedWidth(200)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(6)

        self.menu_btn = QPushButton("☰  Menu")
        self.menu_btn.setObjectName("NavButton")
        self.menu_btn.clicked.connect(self._toggle_sidebar)
        layout.addWidget(self.menu_btn)

        self.nav_library = QPushButton("  Library")
        self.nav_editor = QPushButton("  Editor")
        self.nav_workshop = QPushButton("  Workshop")
        self.nav_marketplace = QPushButton("  Marketplace")
        self.nav_settings = QPushButton("  Settings")
        self._nav_buttons = {
            "library": self.nav_library,
            "editor": self.nav_editor,
            "workshop": self.nav_workshop,
            "marketplace": self.nav_marketplace,
            "settings": self.nav_settings,
        }
        for key, btn in self._nav_buttons.items():
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._select_tab(k))
            layout.addWidget(btn)

        layout.addStretch()

        floats_hint = QLabel("Active stickers")
        floats_hint.setObjectName("Muted")
        floats_hint.setStyleSheet("font-size: 11px; padding-left: 4px;")
        self.floats_hint = floats_hint
        layout.addWidget(floats_hint)

        self.floats_list = QVBoxLayout()
        self.floats_list.setSpacing(4)
        layout.addLayout(self.floats_list)

        toggle_row = QVBoxLayout()
        toggle_row.setSpacing(6)
        self.toggle_label = QLabel("Activar / Desactivar")
        self.toggle_label.setObjectName("Muted")
        self.toggle_label.setStyleSheet("font-size: 11px;")
        self.active_toggle = ActiveToggle(checked=self.stickers_active)
        self.active_toggle.toggled.connect(self._on_active_toggled)
        toggle_row.addWidget(self.toggle_label)
        toggle_row.addWidget(self.active_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(toggle_row)

        return side

    def _build_library_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)
        top = QHBoxLayout()
        top.setSpacing(10)

        self.add_btn = QPushButton("+ Add GIF")
        self.add_btn.setObjectName("AddCapsule")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setFixedHeight(40)
        self.add_btn.clicked.connect(self.import_animations)
        top.addWidget(self.add_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search stickers in library...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self._filter_cards)
        top.addWidget(self.search_input, 1)
        left.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_host = QWidget()
        self.grid_host.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(14)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.scroll.setWidget(self.grid_host)
        left.addWidget(self.scroll, 1)
        layout.addLayout(left, 3)

        details = QFrame()
        details.setObjectName("GlassCard")
        details.setFixedWidth(280)
        d = QVBoxLayout(details)
        d.setContentsMargins(14, 14, 14, 14)
        d.setSpacing(10)

        self.preview = QLabel("No selection")
        self.preview.setObjectName("PreviewPane")
        self.preview.setFixedSize(250, 160)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet(
            "#PreviewPane { background-color: rgba(0,0,0,0.35); "
            f"border: {GLASS_BORDER}; border-radius: 16px; color: rgba(255,255,255,0.4); }}"
        )
        d.addWidget(self.preview)

        sel = QLabel("Selected sticker")
        sel.setStyleSheet("font-weight: 600; font-size: 13px;")
        d.addWidget(sel)

        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        self.name_edit.setPlaceholderText("Select a sticker…")
        d.addWidget(self.name_edit)

        fps_row = QHBoxLayout()
        self.fps_label = QLabel("FPS: 15")
        self.fps_label.setObjectName("Muted")
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(1, 60)
        self.fps_slider.setValue(15)
        self.fps_slider.valueChanged.connect(lambda v: self.fps_label.setText(f"FPS: {v}"))
        fps_row.addWidget(self.fps_label)
        fps_row.addWidget(self.fps_slider, 1)
        d.addLayout(fps_row)

        self.launch_btn = QPushButton("LAUNCH")
        self.launch_btn.setObjectName("LaunchButton")
        self.launch_btn.setFixedHeight(44)
        self.launch_btn.setEnabled(False)
        self.launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_btn.clicked.connect(self.launch_sticker)
        d.addWidget(self.launch_btn)

        self.delete_btn = QPushButton("Delete from library")
        self.delete_btn.setObjectName("DangerBtn")
        self.delete_btn.clicked.connect(self.delete_selected)
        d.addWidget(self.delete_btn)
        d.addStretch()

        hint = QLabel("LAUNCH · Edit drag/resize · LOCK click-through")
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px;")
        d.addWidget(hint)
        layout.addWidget(details)
        return page

    def _build_editor_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(16)

        title = QLabel("Editor")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        sub = QLabel("Ajusta tamaño y FPS del sticker flotante activo.")
        sub.setObjectName("Muted")
        layout.addWidget(sub)

        card = QFrame()
        card.setObjectName("GlassCard")
        c = QVBoxLayout(card)
        c.setContentsMargins(20, 18, 20, 18)
        c.setSpacing(14)

        self.editor_target = QLabel("Ningún sticker activo")
        self.editor_target.setStyleSheet("font-weight: 600;")
        c.addWidget(self.editor_target)

        size_row = QHBoxLayout()
        self.size_label = QLabel("Size: 280 × 280")
        self.size_label.setObjectName("Muted")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(80, 600)
        self.size_slider.setValue(280)
        self.size_slider.valueChanged.connect(self._on_editor_size)
        size_row.addWidget(self.size_label)
        size_row.addWidget(self.size_slider, 1)
        c.addLayout(size_row)

        fps_row = QHBoxLayout()
        self.editor_fps_label = QLabel("FPS: 15")
        self.editor_fps_label.setObjectName("Muted")
        self.editor_fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.editor_fps_slider.setRange(1, 60)
        self.editor_fps_slider.setValue(15)
        self.editor_fps_slider.valueChanged.connect(self._on_editor_fps)
        fps_row.addWidget(self.editor_fps_label)
        fps_row.addWidget(self.editor_fps_slider, 1)
        c.addLayout(fps_row)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Aplicar al sticker")
        apply_btn.setObjectName("LaunchButton")
        apply_btn.setFixedHeight(40)
        apply_btn.clicked.connect(self._apply_editor)
        lock_btn = QPushButton("LOCK")
        lock_btn.clicked.connect(lambda: self.focused_float and self.focused_float.enter_lock_mode())
        edit_btn = QPushButton("EDIT")
        edit_btn.clicked.connect(lambda: self.focused_float and self.focused_float.enter_edit_mode())
        btn_row.addWidget(apply_btn, 2)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(lock_btn)
        c.addLayout(btn_row)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_placeholder_page(self, title: str, subtitle: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(title)
        t.setStyleSheet("font-size: 28px; font-weight: 700;")
        s = QLabel(subtitle)
        s.setObjectName("Muted")
        layout.addWidget(t, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(s, alignment=Qt.AlignmentFlag.AlignCenter)
        return page

    def _build_marketplace_page(self) -> QWidget:
        """Marketplace page with auto-update from GitHub."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(16)

        title = QLabel("Marketplace")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        subtitle = QLabel("Descarga stickers desde GitHub. Actualizaciones automáticas.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        # Update section
        update_card = QFrame()
        update_card.setObjectName("GlassCard")
        uc = QVBoxLayout(update_card)
        uc.setContentsMargins(20, 18, 20, 18)
        uc.setSpacing(12)

        self.check_updates_btn = QPushButton("Buscar actualizaciones")
        self.check_updates_btn.setObjectName("LaunchButton")
        self.check_updates_btn.setFixedHeight(40)
        self.check_updates_btn.clicked.connect(self._check_for_app_updates)
        uc.addWidget(self.check_updates_btn)

        self.update_status = QLabel(f"Versión actual: {APP_VERSION}")
        self.update_status.setObjectName("Muted")
        uc.addWidget(self.update_status)

        layout.addWidget(update_card)

        # Marketplace stickers
        marketplace_card = QFrame()
        marketplace_card.setObjectName("GlassCard")
        mc = QVBoxLayout(marketplace_card)
        mc.setContentsMargins(20, 18, 20, 18)
        mc.setSpacing(12)

        mc_title = QLabel("Stickers disponibles")
        mc_title.setStyleSheet("font-weight: 600;")
        mc.addWidget(mc_title)

        self.marketplace_scroll = QScrollArea()
        self.marketplace_scroll.setWidgetResizable(True)
        self.marketplace_content = QWidget()
        self.marketplace_layout = QVBoxLayout(self.marketplace_content)
        self.marketplace_layout.setSpacing(10)
        self.marketplace_scroll.setWidget(self.marketplace_content)
        mc.addWidget(self.marketplace_scroll)

        self._load_marketplace_stickers()
        layout.addWidget(marketplace_card)
        layout.addStretch()
        return page

    def _check_for_app_updates(self) -> None:
        """Check for app updates from GitHub."""
        self.check_updates_btn.setEnabled(False)
        self.update_status.setText("Buscando actualizaciones...")
        QApplication.processEvents()

        update_info = check_for_updates(APP_VERSION)
        
        if update_info:
            self.update_status.setText(f"Nueva versión: {update_info['version']} - {update_info['name']}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle(f"{APP_NAME} - Actualización")
            msg.setText(f"Versión {update_info['version']} disponible\n{update_info.get('body', '')[:100]}...")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            self.update_status.setText(f"Versión actual: {APP_VERSION} (última)")
        
        self.check_updates_btn.setEnabled(True)

    def _load_marketplace_stickers(self) -> None:
        """Load marketplace stickers (placeholder for now)."""
        while self.marketplace_layout.count():
            item = self.marketplace_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        # Placeholder marketplace items
        marketplace_items = [
            {"name": "iOS Pack", "author": "Team", "desc": "Stickers estilo iOS"},
            {"name": "Animals", "author": "Community", "desc": "Animales divertidos"},
            {"name": "Memes", "author": "Community", "desc": "Pack de memes"},
        ]

        for item in marketplace_items:
            card = QFrame()
            card.setObjectName("GlassCard")
            card.setFixedHeight(60)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            
            info = QVBoxLayout()
            name_label = QLabel(item["name"])
            name_label.setStyleSheet("font-weight: 600;")
            desc_label = QLabel(item["desc"])
            desc_label.setObjectName("Muted")
            desc_label.setStyleSheet("font-size: 11px;")
            info.addWidget(name_label)
            info.addWidget(desc_label)
            
            cl.addLayout(info)
            cl.addStretch()
            
            author_label = QLabel(f"by {item['author']}")
            author_label.setObjectName("Muted")
            author_label.setStyleSheet("font-size: 11px;")
            cl.addWidget(author_label)
            
            download_btn = QPushButton("GET")
            download_btn.setObjectName("AddCapsule")
            download_btn.setFixedSize(60, 30)
            cl.addWidget(download_btn)
            
            self.marketplace_layout.addWidget(card)

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 28, 36, 28)
        layout.setSpacing(14)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("GlassCard")
        c = QVBoxLayout(card)
        c.setContentsMargins(20, 18, 20, 18)
        c.setSpacing(10)

        c.addWidget(QLabel("Appearance"))
        muted = QLabel("Glassmorphism dark · accent #007AFF · Vine 980×640 fixed")
        muted.setObjectName("Muted")
        muted.setStyleSheet("font-size: 12px;")
        c.addWidget(muted)

        c.addSpacing(6)
        c.addWidget(QLabel(f"Version {APP_VERSION}"))
        path_lbl = QLabel(f"Data: {DATA_DIR}")
        path_lbl.setObjectName("Muted")
        path_lbl.setStyleSheet("font-size: 11px;")
        path_lbl.setWordWrap(True)
        c.addWidget(path_lbl)

        c.addSpacing(8)
        self.install_btn = QPushButton("Instalar en el escritorio")
        self.install_btn.setObjectName("InstallBtn")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(self._open_installer)
        c.addWidget(self.install_btn)

        self.install_status = QLabel("")
        self.install_status.setObjectName("Muted")
        self.install_status.setStyleSheet("font-size: 11px;")
        self.install_status.setWordWrap(True)
        c.addWidget(self.install_status)

        # Add uninstall button
        c.addSpacing(12)
        self.uninstall_btn = QPushButton("Desinstalar")
        self.uninstall_btn.setObjectName("DangerBtn")
        self.uninstall_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.uninstall_btn.clicked.connect(self._run_uninstall)
        c.addWidget(self.uninstall_btn)

    def _run_uninstall(self) -> None:
        """Run uninstall process."""
        import shutil
        import subprocess
        
        # Remove installation directory
        if INSTALL_DIR.exists():
            shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        
        # Remove desktop shortcut
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        lnk = desktop / f"{APP_NAME}.lnk"
        if lnk.exists():
            lnk.unlink()
        
        # Show completion message
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle(f"{APP_NAME} - Desinstalado")
        msg.setText(f"{APP_NAME} ha sido desinstalado correctamente.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        
        # Update install button status
        self._sync_install_button()

        layout.addWidget(card)
        layout.addStretch()
        return page

    # -- navigation / menu --------------------------------------------------

    def _select_tab(self, key: str) -> None:
        mapping = {
            "library": 0,
            "editor": 1,
            "workshop": 2,
            "settings": 3,
        }
        idx = mapping[key]
        # Fade transition
        effect = QGraphicsOpacityEffect(self.stack.currentWidget())
        self.stack.currentWidget().setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(140)
        anim.setStartValue(1.0)
        anim.setEndValue(0.35)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def _finish():
            self.stack.setCurrentIndex(idx)
            for k, btn in self._nav_buttons.items():
                btn.setProperty("active", "true" if k == key else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
            new_fx = QGraphicsOpacityEffect(self.stack.currentWidget())
            self.stack.currentWidget().setGraphicsEffect(new_fx)
            new_fx.setOpacity(0.35)
            fade_in = QPropertyAnimation(new_fx, b"opacity", self)
            fade_in.setDuration(180)
            fade_in.setStartValue(0.35)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
            fade_in.start()
            self._fade_anim = fade_in
            if key == "editor":
                self._refresh_editor()
            if key == "settings":
                self._sync_install_button()

        anim.finished.connect(_finish)
        anim.start()
        self._tab_fade = anim

    def _toggle_sidebar(self) -> None:
        """Safe collapse: only width + label text; never break layout."""
        if self._sidebar_anim and self._sidebar_anim.state() == QPropertyAnimation.State.Running:
            return
        self._sidebar_expanded = not self._sidebar_expanded
        target = 200 if self._sidebar_expanded else 72

        anim = QPropertyAnimation(self.sidebar, b"maximumWidth", self)
        anim.setDuration(240)
        anim.setStartValue(self.sidebar.width())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _apply(v):
            w = int(v)
            self.sidebar.setFixedWidth(w)
            self.sidebar.setMaximumWidth(w)
            self.sidebar.setMinimumWidth(w)

        anim.valueChanged.connect(_apply)

        def _done():
            expanded = self._sidebar_expanded
            self.menu_btn.setText("☰  Menu" if expanded else "☰")
            for key, btn in self._nav_buttons.items():
                btn.setText(self._nav_labels[key] if expanded else self._nav_labels[key].strip()[:1])
            self.floats_hint.setVisible(expanded)
            self.toggle_label.setVisible(expanded)
            # Keep toggle visible but compact when collapsed
            self.active_toggle.setVisible(True)

        anim.finished.connect(_done)
        anim.start()
        self._sidebar_anim = anim

    # -- library ------------------------------------------------------------

    def schedule_autosave(self) -> None:
        self._autosave_timer.start()

    def _flush_autosave(self) -> None:
        """Save all state: library, floats, window geometry, and settings."""
        save_library(self.library)
        
        floats_state = []
        for s in self.active_floats:
            g = s.geometry()
            floats_state.append({
                "path": s.gif_path,
                "fps": s.fps,
                "mode": s.mode,
                "x": g.x(),
                "y": g.y(),
                "w": g.width(),
                "h": g.height(),
            })
        
        # Guardar geometría de la ventana
        geo = self.geometry()
        window_geo = {
            "x": geo.x(),
            "y": geo.y(),
            "width": geo.width(),
            "height": geo.height()
        }
        
        self.session = {
            "stickers_active": self.stickers_active,
            "floats": floats_state,
            "window_geometry": window_geo,
        }
        save_session(self.session)

    def import_animations(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add GIF / sticker",
            "",
            "Animations (*.gif);;Images (*.gif *.png *.jpg *.jpeg *.webp);;All files (*.*)",
        )
        if not files:
            return
        existing = {item["path"] for item in self.library}
        for path in files:
            path = str(Path(path).resolve())
            if path in existing:
                continue
            self.library.append({"name": Path(path).name, "path": path})
        self.schedule_autosave()
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                if isinstance(w, AnimationCard):
                    w.stop_movie()
                w.deleteLater()
        self.cards.clear()
        self.selected_card = None
        self.launch_btn.setEnabled(False)
        self.name_edit.clear()
        self._clear_preview()

        query = self.search_input.text().strip().lower()
        col_count = 3
        row = col = 0
        for item in self.library:
            name, path = item["name"], item["path"]
            if query and query not in name.lower():
                continue
            card = AnimationCard(name, path)
            card.clicked.connect(self.select_card)
            self.grid.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

    def _filter_cards(self, _text: str = "") -> None:
        self._rebuild_grid()

    def select_card(self, card: AnimationCard) -> None:
        if self.selected_card:
            self.selected_card.set_selected(False)
        self.selected_card = card
        card.set_selected(True)
        self.name_edit.setText(card.name)
        self.launch_btn.setEnabled(True)
        self._show_preview(card.path)

    def _clear_preview(self) -> None:
        if self._preview_movie:
            self._preview_movie.stop()
            self._preview_movie = None
        self.preview.clear()
        self.preview.setText("No selection")

    def _show_preview(self, path: str) -> None:
        self._clear_preview()
        if path.lower().endswith(".gif"):
            movie = create_hi_dpi_movie(path, 240, 150, self.preview)
            self.preview.setMovie(movie)
            movie.start()
            self._preview_movie = movie
        else:
            pix = QPixmap(path)
            if not pix.isNull():
                self.preview.setPixmap(
                    pix.scaled(240, 150, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                )

    def delete_selected(self) -> None:
        if not self.selected_card:
            return
        path = str(Path(self.selected_card.path).resolve())
        # Close ALL floating stickers using this path
        for sticker in list(self.active_floats):
            if str(Path(sticker.gif_path).resolve()) == path:
                if sticker.movie:
                    sticker.movie.stop()
                sticker.close()
        self.library = [i for i in self.library if str(Path(i["path"]).resolve()) != path]
        self.schedule_autosave()
        self._rebuild_grid()
        self._refresh_floats_list()
        self._refresh_editor()

    # -- floating stickers --------------------------------------------------

    def launch_sticker(self) -> None:
        if not self.selected_card:
            return
        sticker = FloatingSticker(
            self.selected_card.path,
            fps=self.fps_slider.value(),
        )
        sticker.closed.connect(self._on_float_closed)
        sticker.mode_changed.connect(lambda *_: self._on_float_changed())
        sticker.geometry_changed.connect(lambda *_: self.schedule_autosave())
        offset = 28 * len(self.active_floats)
        sticker.move(120 + offset, 120 + offset)
        if self.stickers_active:
            sticker.show()
            sticker.raise_()
        else:
            sticker.hide()
        self.active_floats.append(sticker)
        self.focused_float = sticker
        
        # Conectar señales de cambio para auto-guardado
        sticker.geometry_changed.connect(self._on_sticker_geometry_changed)
        sticker.mode_changed.connect(self.schedule_autosave)
        
        self._refresh_floats_list()
        self._refresh_editor()
        self.schedule_autosave()

    def _on_float_closed(self, sticker: FloatingSticker) -> None:
        if sticker in self.active_floats:
            self.active_floats.remove(sticker)
        if self.focused_float is sticker:
            self.focused_float = self.active_floats[-1] if self.active_floats else None
        self._refresh_floats_list()
        self._refresh_editor()
        self.schedule_autosave()

    def _on_float_changed(self) -> None:
        self._refresh_floats_list()
        self.schedule_autosave()

    def _refresh_floats_list(self) -> None:
        while self.floats_list.count():
            item = self.floats_list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for sticker in self.active_floats:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)
            name = Path(sticker.gif_path).stem[:12]
            lbl = QLabel(f"{name} · {sticker.mode}")
            lbl.setStyleSheet("font-size: 11px;")
            btn = QPushButton("Focus")
            btn.setFixedHeight(24)
            btn.setStyleSheet("font-size: 10px; padding: 2px 8px; border-radius: 8px;")
            btn.clicked.connect(lambda _=False, s=sticker: self._focus_float(s))
            h.addWidget(lbl, 1)
            h.addWidget(btn)
            self.floats_list.addWidget(row)

    def _focus_float(self, sticker: FloatingSticker) -> None:
        self.focused_float = sticker
        if sticker.mode == "lock":
            sticker.enter_edit_mode()
        sticker.raise_()
        self._refresh_editor()
        self._select_tab("editor")

    def _on_active_toggled(self, active: bool) -> None:
        self.stickers_active = active
        for s in self.active_floats:
            if active:
                s.show()
            else:
                s.hide()
        self.schedule_autosave()

    # -- editor -------------------------------------------------------------

    def _on_sticker_geometry_changed(self, sticker):
        """Trigger autosave when sticker geometry changes."""
        self._sticker_autosave_timer.start()

    def _refresh_editor(self) -> None:
        if not self.focused_float and self.active_floats:
            self.focused_float = self.active_floats[-1]
        if not self.focused_float:
            self.editor_target.setText("Ningún sticker activo — LAUNCH uno desde Library")
            return
        s = self.focused_float
        self.editor_target.setText(f"Editando: {Path(s.gif_path).name}")
        self.size_slider.blockSignals(True)
        self.size_slider.setValue(max(s.width(), s.height()))
        self.size_slider.blockSignals(False)
        self.size_label.setText(f"Size: {s.width()} × {s.height()}")
        self.editor_fps_slider.blockSignals(True)
        self.editor_fps_slider.setValue(s.fps)
        self.editor_fps_slider.blockSignals(False)
        self.editor_fps_label.setText(f"FPS: {s.fps}")

    def _on_editor_size(self, v: int) -> None:
        self.size_label.setText(f"Size: {v} × {v}")
        if self.focused_float:
            self.focused_float.set_sticker_size(v, v)
            self.schedule_autosave()

    def _on_editor_fps(self, v: int) -> None:
        self.editor_fps_label.setText(f"FPS: {v}")
        if self.focused_float:
            self.focused_float.set_fps(v)
            self.schedule_autosave()

    def _apply_editor(self) -> None:
        if not self.focused_float:
            return
        v = self.size_slider.value()
        self.focused_float.set_sticker_size(v, v)
        self.focused_float.set_fps(self.editor_fps_slider.value())
        self.schedule_autosave()
        self._refresh_editor()

    # -- install ------------------------------------------------------------

    def _sync_install_button(self) -> None:
        ver = installed_version()
        if ver is None:
            self.install_btn.setText("Instalar en el escritorio")
            self.install_btn.setEnabled(True)
            self.install_status.setText("Aún no instalada como app de escritorio.")
        elif version_tuple(ver) >= version_tuple(APP_VERSION):
            self.install_btn.setText("Ya está en su última versión")
            self.install_btn.setEnabled(True)  # still opens dialog
            self.install_status.setText(f"Instalada v{ver} en {INSTALL_DIR}")
        else:
            self.install_btn.setText(f"Actualizar a {APP_VERSION}")
            self.install_btn.setEnabled(True)
            self.install_status.setText(f"Instalada v{ver} · disponible {APP_VERSION}")

    def _open_installer(self) -> None:
        dlg = InstallerDialog(self)
        dlg.exec()
        self._sync_install_button()

    # -- window chrome ------------------------------------------------------

    def _title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def _title_move(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def _load_window_geometry(self) -> dict:
        """Cargar posición y tamaño de la ventana desde la sesión."""
        try:
            if "window_geometry" in self.session:
                return self.session["window_geometry"]
        except (KeyError, TypeError):
            pass
        return {"x": 100, "y": 100, "width": WINDOW_W, "height": WINDOW_H}

    def _save_window_geometry(self) -> None:
        """Guardar posición y tamaño de la ventana en la sesión."""
        geo = self.geometry()
        self.session["window_geometry"] = {
            "x": geo.x(),
            "y": geo.y(),
            "width": geo.width(),
            "height": geo.height()
        }
        save_session(self.session)

    def _restore_window_geometry(self) -> None:
        """Restaurar posición y tamaño de la ventana."""
        geo = self._window_geometry
        self.setGeometry(geo["x"], geo["y"], geo["width"], geo["height"])

    def closeEvent(self, event):
        self._save_window_geometry()
        self._flush_autosave()
        for sticker in list(self.active_floats):
            if sticker.movie:
                sticker.movie.stop()
            sticker.close()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_USE_NATIVE_WINDOWS", "1")
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)
    app.setStyle("Fusion")
    
    # Enable high DPI scaling (compatible with PyQt6)
    # For PyQt6, we use environment variables and Qt flags
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_USE_NATIVE_WINDOWS"] = "1"
    
    ensure_data_dir()
    # Verificar si está instalado
    if not _is_installed():
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle(f"{APP_NAME} - No instalado")
        msg.setText(f"{APP_NAME} debe estar instalado para ejecutarse.\n\nPor favor, ejecuta el instalador primero.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        return 1
    
    hub = StickaEngineHub()
    hub.show()
    return app.exec()





def _auto_install() -> None:
    """Auto-instala la aplicacion en la primera ejecucion."""
    try:
        # Crear directorio de instalacion
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo de version
        with open(INSTALL_META, "w", encoding="utf-8") as f:
            json.dump({"version": APP_VERSION, "name": APP_NAME}, f, indent=2)
        
        # Crear acceso directo en el escritorio
        _create_desktop_shortcut()
        
    except Exception as e:
        print(f"Auto-install error: {e}")


def _create_desktop_shortcut() -> None:
    """Crea acceso directo en el escritorio."""
    try:
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        lnk = desktop / f"{APP_NAME}.lnk"
        
        # Crear script PowerShell para el acceso directo
        ps = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{lnk}"); '
            f'$s.TargetPath = "{sys.executable}"; '
            f'$s.WorkingDirectory = "{Path(sys.executable).parent}"; '
            f'$s.Description = "{APP_NAME} v{APP_VERSION}"; '
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=False,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        print(f"Shortcut error: {e}")


if __name__ == "__main__":
    sys.exit(main())

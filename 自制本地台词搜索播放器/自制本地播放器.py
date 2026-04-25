import os
import re
import json
import csv
import shlex
import time
import uuid
import sys
import traceback
import urllib.parse
import urllib.request
import ssl
import shutil
import subprocess
import concurrent.futures
import threading
os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] = ""   # 临时禁用硬件解码，避免崩溃
# 如果你想强制软件解码，可以保持为空
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ==================== 【视频解码深度优化】 ====================
os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] = ""
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"          # 强制使用 ffmpeg 后端
os.environ["QT_MULTIMEDIA_BACKEND"] = "ffmpeg"

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer, QPoint
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QTextCursor, QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QListWidget, QTabWidget,
    QSplitter, QGroupBox, QFormLayout, QComboBox, QCheckBox, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSlider, QTextEdit, QTextBrowser,
    QMenu, QDialog, QDialogButtonBox, QProgressBar, QListWidgetItem, QInputDialog,
    QTreeWidget, QTreeWidgetItem, QColorDialog, QFontDialog, QGraphicsDropShadowEffect, QFrame
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

# ==================== 外部补丁优先加载：主题包 / 字体设置 ====================
import importlib.util
_CURRENT_SCRIPT_DIR = Path(__file__).resolve().parent

def _load_external_py_module(module_tag: str, filename_candidates: list[str]):
    for name in filename_candidates:
        try:
            path = _CURRENT_SCRIPT_DIR / name
            if not path.exists():
                continue
            spec = importlib.util.spec_from_file_location(module_tag, str(path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                import sys as _sys
                _sys.modules[module_tag] = mod
                spec.loader.exec_module(mod)
                return mod
        except Exception:
            continue
    return None

_font_patch_mod = _load_external_py_module('wzxs_font_patch', [
    '本地模式_字体设置补丁.py',
    '本地模式_字体设置补丁(2).py',
])

if _font_patch_mod is not None and hasattr(_font_patch_mod, 'LocalFontSettingsMixin'):
    LocalFontSettingsMixin = _font_patch_mod.LocalFontSettingsMixin
else:
    class LocalFontSettingsMixin:
        """占位基类。真正的字体设置逻辑由 MainWindow 内部方法提供。"""
        pass

_theme_pack_mod = _load_external_py_module('wzxs_theme_pack', [
    'ai_analysis_theme_pack_66.py',
    'ai_analysis_theme_pack_66_fix2.py',
])

if _theme_pack_mod is not None:
    AIAnalysisWorkbench = getattr(_theme_pack_mod, 'AIAnalysisWorkbench', QWidget)
    ai_pack_apply_theme = getattr(_theme_pack_mod, 'apply_theme', lambda widget, theme_name, palette_name='': None)
    list_theme_names = getattr(_theme_pack_mod, 'list_theme_names', lambda: list(THEMES.keys()) if 'THEMES' in globals() else ['默认'])
    list_palette_names = getattr(_theme_pack_mod, 'list_palette_names', lambda: ['默认'])
else:
    class AIAnalysisWorkbench(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            lay = QVBoxLayout(self)
            lay.setContentsMargins(8, 8, 8, 8)
            lay.setSpacing(8)
            self.input_box = QPlainTextEdit()
            self.input_box.setPlaceholderText('输入要分析的英文、句子或片段…')
            self.output_box = QPlainTextEdit()
            self.output_box.setPlaceholderText('这里显示分析结果（当前为内置基础版面板）…')
            lay.addWidget(self.input_box)
            lay.addWidget(self.output_box)

    def ai_pack_apply_theme(widget, theme_name, palette_name=''):
        return

    def list_theme_names():
        return list(THEMES.keys()) if 'THEMES' in globals() else ['默认']

    def list_palette_names():
        return ['默认']

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None

APP_TITLE = "文转小秘书 · 统一学习工作台（重做版）"
BASE_DIR = Path(__file__).resolve().parent

def get_user_app_dir() -> Path:
    app_name = "文转小秘书"
    candidates = []
    if os.name == "nt":
        for env_name in ("APPDATA", "LOCALAPPDATA"):
            raw = os.getenv(env_name, "").strip()
            if raw:
                candidates.append(Path(raw) / app_name)
    home = Path.home()
    candidates.extend([
        home / ".wenzhuan_xiaomishu",
        home / "AppData" / "Roaming" / app_name,
        BASE_DIR / "data",
    ])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            try:
                probe.unlink()
            except Exception:
                pass
            return candidate
        except Exception:
            continue
    return BASE_DIR / "data"

USER_APP_DIR = get_user_app_dir()
DATA_DIR = USER_APP_DIR
SETTINGS_PATH = DATA_DIR / "learning_workspace_settings.json"
DOWNLOAD_DIR = DATA_DIR / "downloads"
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm"}
SUB_EXTS = {".srt", ".ass"}
SEARCH_RESULT_COLUMNS = ["剧集/来源", "时间", "英文", "中文", "视频/URL", "备注"]

DEFAULT_LINK_TAGS = {
    "AI": {
        "ChatGPT": "https://chatgpt.com/",
        "Claude": "https://claude.ai/",
        "通义千问": "https://qianwen.aliyun.com/",
        "元宝": "https://yuanbao.tencent.com/"
    },
    "词典": {
        "Cambridge": "https://dictionary.cambridge.org/",
        "Longman": "https://www.ldoceonline.com/",
        "Ozdic": "https://ozdic.com/",
        "Bing词典": "https://cn.bing.com/dict/"
    },
    "台词视频": {
        "PlayPhrase": "https://www.playphrase.me/",
        "YouGlish": "https://youglish.com/",
        "Yarn": "https://yarn.co/"
    },
    "学习工具": {
        "BBC English": "https://www.bbc.co.uk/learningenglish/",
        "British Council": "https://learnenglish.britishcouncil.org/free-resources"
    }
}

THEMES = {
    "曜石金奢": dict(
        bg="#0b0d12",
        bg_alt="#121722",
        card="#141924",
        card_soft="#1b2230",
        input="#101722",
        header="#171f2b",
        border="#2b3546",
        splitter="#263140",
        text="#eef2f8",
        text_muted="#9ba8bd",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #cfae68, stop:1 #f3d69a)",
        accent2="#e8c983",
        accent3="#9f7b38",
        selection="#d6b36f"
    ),
    "深海钛蓝": dict(
        bg="#07131b",
        bg_alt="#0d1c28",
        card="#102231",
        card_soft="#153043",
        input="#0d1f2d",
        header="#11293a",
        border="#23445d",
        splitter="#1b3d56",
        text="#edf7ff",
        text_muted="#93b6cb",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #2fb7ff, stop:1 #6fe3ff)",
        accent2="#66d8ff",
        accent3="#1a88b8",
        selection="#2fa9e1"
    ),
    "云锦鎏金": dict(
        bg="#f5f1e8",
        bg_alt="#efe7d8",
        card="#fffaf1",
        card_soft="#fbf3e5",
        input="#fffdf8",
        header="#efe4d1",
        border="#d7c2a1",
        splitter="#d2bc98",
        text="#3d3428",
        text_muted="#7d6d58",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #b78a3c, stop:1 #d8b56e)",
        accent2="#c9a256",
        accent3="#8f6927",
        selection="#bb8f41"
    ),
    "午夜酒红": dict(
        bg="#140c13",
        bg_alt="#1d1018",
        card="#21121c",
        card_soft="#2a1621",
        input="#1a1118",
        header="#2a1520",
        border="#4c2b38",
        splitter="#422431",
        text="#f7edf2",
        text_muted="#caa6b7",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #9e375e, stop:1 #df7d9f)",
        accent2="#d26b90",
        accent3="#7f274a",
        selection="#b44a73"
    ),
    "极夜银翼": dict(
        bg="#0e1014",
        bg_alt="#161a22",
        card="#1a1f29",
        card_soft="#232a36",
        input="#141922",
        header="#1d2430",
        border="#394556",
        splitter="#313b4b",
        text="#edf1f8",
        text_muted="#a8b1c0",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #8d9bb0, stop:1 #d7e1ef)",
        accent2="#c0cede",
        accent3="#738094",
        selection="#97a6bb"
    ),
    "奶油樱花房": dict(
        bg="#f9f4fb", bg_alt="#f4edf8", card="#fffafe", card_soft="#fff7fd", input="#ffffff", header="#f2e8f7",
        border="#e9d9f0", splitter="#e3d3eb", text="#5c4c67", text_muted="#8d7b98",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #caa3dc, stop:1 #e8c8f3)", accent2="#b98fd0", accent3="#9a70b6", selection="#c597df"
    ),
    "影院暗幕模式": dict(
        bg="#14161b", bg_alt="#1b1e25", card="#1c1f27", card_soft="#242935", input="#171b22", header="#20242d",
        border="#333948", splitter="#2c3340", text="#e8edf7", text_muted="#98a2b5",
        accent="qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6ea8ff, stop:1 #91c0ff)", accent2="#4d86dc", accent3="#3a6db6", selection="#5e9eff"
    ),
}




def normalize_ui_scale_text(value) -> str:
    try:
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return "100%"
            return v if v.endswith("%") else f"{v}%"
        if isinstance(value, (int, float)):
            iv = int(value)
            return f"{iv}%"
    except Exception:
        pass
    return "100%"

def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    safe_mkdir(DATA_DIR)
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(data: dict):
    safe_mkdir(DATA_DIR)
    tmp_path = SETTINGS_PATH.with_suffix(SETTINGS_PATH.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass
    os.replace(tmp_path, SETTINGS_PATH)


def make_uid(*parts: Any) -> str:
    raw = "|".join(str(x) for x in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def parse_srt_timestamp(ts: str) -> float:
    hms, ms = ts.split(",")
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def strip_ass_tags(text: str) -> str:
    text = re.sub(r"\{.*?\}", "", text)
    return text.replace(r"\N", "\n").strip()


def split_en_zh(text: str) -> Tuple[str, str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines:
        return "", ""
    if len(lines) == 1:
        s = lines[0]
        if re.search(r"[\u4e00-\u9fff]", s):
            return "", s
        return s, ""
    en_parts, zh_parts = [], []
    for ln in lines:
        has_en = bool(re.search(r"[A-Za-z]", ln))
        has_zh = bool(re.search(r"[\u4e00-\u9fff]", ln))
        if has_en and not has_zh:
            en_parts.append(ln)
        elif has_zh and not has_en:
            zh_parts.append(ln)
        elif has_en:
            en_parts.append(ln)
        else:
            zh_parts.append(ln)
    if not en_parts:
        en_parts = [lines[0]]
    if not zh_parts and len(lines) > 1:
        zh_parts = lines[1:]
    return " ".join(en_parts).strip(), " ".join(zh_parts).strip()


def parse_srt(path: Path) -> List[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    items = []
    for block in blocks:
        lines = [x for x in block.split("\n") if x.strip()]
        if len(lines) < 2:
            continue
        if re.match(r"^\d+$", lines[0].strip()):
            lines = lines[1:]
        if not lines:
            continue
        m = re.match(r"(\d\d:\d\d:\d\d,\d{3})\s*-->\s*(\d\d:\d\d:\d\d,\d{3})", lines[0].strip())
        if not m:
            continue
        body = "\n".join(lines[1:])
        en, zh = split_en_zh(body)
        items.append({
            "start": parse_srt_timestamp(m.group(1)),
            "end": parse_srt_timestamp(m.group(2)),
            "text": body.strip(),
            "en": en,
            "zh": zh,
        })
    return items


def parse_ass(path: Path) -> List[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
    items = []
    for line in text.splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        start_s, end_s, body = parts[1], parts[2], parts[9]
        def ass_ts_to_sec(ts: str) -> float:
            h, m, rest = ts.split(":")
            s, cs = rest.split(".")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0
        clean = strip_ass_tags(body)
        en, zh = split_en_zh(clean)
        items.append({
            "start": ass_ts_to_sec(start_s),
            "end": ass_ts_to_sec(end_s),
            "text": clean,
            "en": en,
            "zh": zh,
        })
    return items


def extract_season_episode(name: str) -> tuple[str, str]:
    patterns = [
        r"[Ss](\d{1,2})[Ee](\d{1,2})",
        r"(\d{1,2})x(\d{1,2})",
        r"第(\d{1,2})季.*?第(\d{1,2})集",
    ]
    for p in patterns:
        m = re.search(p, name)
        if m:
            return m.group(1).zfill(2), m.group(2).zfill(2)
    return "", ""


@dataclass
class LearningItem:
    uid: str
    source_type: str
    subtitle_text: str
    start_time: float
    end_time: float
    video_path: str = ""
    subtitle_path: str = ""
    video_url: str = ""
    cache_path: str = ""
    show_name: str = ""
    season_hint: str = ""
    episode_hint: str = ""
    en: str = ""
    zh: str = ""
    checked: bool = False
    selected: bool = False
    in_playlist: bool = False
    note: str = ""
    word_style: Dict[str, Any] = field(default_factory=dict)
    ai_target: str = ""
    downloaded: bool = False
    added_index: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AITarget:
    name: str
    kind: str = "generic"
    endpoint: str = ""
    method: str = "POST"
    headers_json: str = "{}"
    enabled: bool = True


@dataclass
class VocabularyEntry:
    word: str
    source_uid: str
    source_text: str
    note: str = ""
    color: str = "#5c4c67"
    font_family: str = "Microsoft YaHei"


def default_network_profiles() -> List[dict]:
    return [
        {
            "name": "PlayPhrase Token直登",
            "kind": "playphrase_token",
            "endpoint": "https://www.playphrase.me/api/v1/phrases/search",
            "method": "GET",
            "enabled": True,
            "is_default": True,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "https://www.playphrase.me/",
            "proxy": "",
            "note": "推荐：直接填写 Token 即可使用。",
        },
        {
            "name": "PlayPhrase 免费网页",
            "kind": "playphrase_free",
            "endpoint": "https://www.playphrase.me/#/search?q={query}",
            "method": "GET",
            "enabled": True,
            "is_default": False,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "https://www.playphrase.me/",
            "proxy": "",
            "note": "免登录网页入口模式。",
        },
        {
            "name": "PlayPhrase 登录增强",
            "kind": "playphrase_auth",
            "endpoint": "https://www.playphrase.me/api/v1/phrases/search",
            "method": "GET",
            "enabled": False,
            "is_default": False,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "https://www.playphrase.me/",
            "proxy": "",
            "note": "需要 Token / Cookie / CSRF 的增强模式。",
        },
        {
            "name": "自定义接口",
            "kind": "generic_api",
            "endpoint": "",
            "method": "GET",
            "enabled": False,
            "is_default": False,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "",
            "proxy": "",
            "note": "通用 JSON API。",
        },
        {
            "name": "网页直连",
            "kind": "direct_web",
            "endpoint": "https://www.example.com/search?q={query}",
            "method": "GET",
            "enabled": False,
            "is_default": False,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "",
            "proxy": "",
            "note": "不做 API 解析，直接生成网页入口。",
        },
    ]


class AppState:

    def __init__(self):
        self.current_selected_uid: Optional[str] = None
        self.current_playing_uid: Optional[str] = None
        self.playlist: List[LearningItem] = []
        self.play_mode: str = "slice"  # slice / video / full
        self.loop_mode: str = "single"  # single / list / all
        self.loop_count: int = 1
        self.order_mode: str = "playlist"  # playlist / add
        self.ai_target: str = ""
        self.global_add_counter: int = 0


class ToggleSelectionTable(QTableWidget):
    def mousePressEvent(self, event):
        idx = self.indexAt(event.pos())
        row = idx.row()
        mods = event.modifiers()
        if row >= 0 and not (mods & Qt.ControlModifier) and not (mods & Qt.ShiftModifier):
            selected = sorted({x.row() for x in self.selectionModel().selectedRows()}) if self.selectionModel() else []
            if len(selected) == 1 and selected[0] == row:
                self.clearSelection()
                self.clearFocus()
                event.accept()
                return
        super().mousePressEvent(event)


class EscapableVideoWidget(QVideoWidget):
    escapePressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escapePressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class ClickableSlider(QSlider):
    jumpTo = Signal(int)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.orientation() == Qt.Horizontal:
                span = max(1, self.width())
                ratio = max(0.0, min(float(event.position().x()) / span, 1.0))
            else:
                span = max(1, self.height())
                ratio = max(0.0, min(1.0 - float(event.position().y()) / span, 1.0))
            value = int(self.minimum() + (self.maximum() - self.minimum()) * ratio)
            self.setValue(value)
            self.jumpTo.emit(value)
        super().mousePressEvent(event)


class FloatingSubtitleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_offset = None
        self._current_style = {}
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)
        self.en_label = QLabel('')
        self.en_label.setWordWrap(True)
        self.en_label.setAlignment(Qt.AlignCenter)
        self.zh_label = QLabel('')
        self.zh_label.setWordWrap(True)
        self.zh_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.en_label)
        lay.addWidget(self.zh_label)
        self.resize(900, 120)
        self.apply_style({})

    def _color_to_rgba(self, color_hex: str, opacity_percent: int = 100) -> str:
        color = QColor(color_hex or '#101218')
        alpha = max(0, min(255, int(round(255 * max(0, min(100, int(opacity_percent or 0))) / 100.0))))
        return f'rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})'

    def _apply_effect(self, label, color_hex: str, blur: int = 0, offset: int = 0):
        blur = max(0, int(blur or 0))
        if blur <= 0:
            label.setGraphicsEffect(None)
            return
        effect = QGraphicsDropShadowEffect(label)
        effect.setBlurRadius(blur)
        effect.setColor(QColor(color_hex or '#000000'))
        effect.setOffset(int(offset or 0), int(offset or 0))
        label.setGraphicsEffect(effect)

    def apply_style(self, style: dict):
        merged = {
            'family': 'Microsoft YaHei',
            'en_size': 20,
            'zh_size': 16,
            'en_color': '#ffffff',
            'zh_color': '#d8e6ff',
            'backdrop_color': '#101218',
            'backdrop_opacity': 72,
            'shadow_color': '#000000',
            'shadow_blur': 24,
            'shadow_offset': 2,
            'glow_color': '#000000',
            'glow_blur': 8,
        }
        if isinstance(style, dict):
            merged.update(style)
        self._current_style = merged
        curtain = self._color_to_rgba(merged.get('backdrop_color') or '#101218', int(merged.get('backdrop_opacity', 72) or 72))
        self.setStyleSheet(f"QWidget {{ background-color: {curtain}; border: 1px solid rgba(255,255,255,35); border-radius: 14px; }} QLabel {{ background: transparent; }}")
        self.en_label.setStyleSheet(f"font-family: '{merged.get('family') or 'Microsoft YaHei'}'; font-size: {int(merged.get('en_size', 20) or 20)}px; font-weight: 700; color: {merged.get('en_color') or '#ffffff'}; background: transparent;")
        self.zh_label.setStyleSheet(f"font-family: '{merged.get('family') or 'Microsoft YaHei'}'; font-size: {int(merged.get('zh_size', 16) or 16)}px; color: {merged.get('zh_color') or '#d8e6ff'}; background: transparent;")
        effect_blur = max(int(merged.get('shadow_blur', 24) or 0), int(merged.get('glow_blur', 8) or 0))
        effect_color = merged.get('shadow_color') if int(merged.get('shadow_blur', 24) or 0) > 0 else merged.get('glow_color')
        effect_offset = int(merged.get('shadow_offset', 2) or 0) if int(merged.get('shadow_blur', 24) or 0) > 0 else 0
        self._apply_effect(self.en_label, effect_color, effect_blur, effect_offset)
        self._apply_effect(self.zh_label, effect_color, effect_blur, effect_offset)

    def set_texts(self, en: str, zh: str, show_zh: bool = True):
        self.en_label.setText((en or '').strip())
        self.zh_label.setText((zh or '').strip())
        self.zh_label.setVisible(bool(show_zh and (zh or '').strip()))
        self.adjustSize()
        self.setMinimumWidth(520)
        self.resize(min(max(self.width(), 620), 980), min(max(self.height(), 88), 260))
    
    def reset_to_default(self):
        parent = self.parentWidget()
        if parent is None:
            return
        pw = max(1, parent.width())
        ph = max(1, parent.height())
        w = min(max(int(pw * 0.78), 620), 980)
        h = min(max(self.height(), 96), 260)
        x = max(12, int((pw - w) / 2))
        y = max(12, ph - h - 100)          # 增加底部安全距离，防止被学习区挤压
        self.setGeometry(x, y, w, h)
        self.raise_()


    def _clamp_move(self, target):
        parent = self.parentWidget()
        if parent is None:
            return target
        x = max(0, min(target.x(), max(0, parent.width() - self.width())))
        y = max(0, min(target.y(), max(0, parent.height() - self.height())))
        return QPoint(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.position().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            target = self.mapToParent(event.position().toPoint() - self._drag_offset)
            self.move(self._clamp_move(target))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)
class ScanWorker(QThread):
    finished_ok = Signal(list, list)
    failed = Signal(str)

    def __init__(self, roots: List[str]):
        super().__init__()
        self.roots = roots

    def run(self):
        try:
            items: List[LearningItem] = []
            unmatched: List[str] = []
            for root in self.roots:
                root_path = Path(root)
                if not root_path.exists():
                    unmatched.append(f"根目录不存在: {root}")
                    continue
                for dirpath, _, filenames in os.walk(root):
                    files = [Path(dirpath) / x for x in filenames]
                    videos = {f.stem: f for f in files if f.suffix.lower() in VIDEO_EXTS}
                    subs = {f.stem: f for f in files if f.suffix.lower() in SUB_EXTS}
                    matched_subs = set()
                    for stem, vf in videos.items():
                        sf = subs.get(stem)
                        if not sf:
                            unmatched.append(f"未配对视频: {vf}")
                            continue
                        matched_subs.add(stem)
                        season, episode = extract_season_episode(vf.name)
                        try:
                            cue_rows = parse_srt(sf) if sf.suffix.lower() == '.srt' else parse_ass(sf)
                        except Exception as e:
                            unmatched.append(f"字幕解析失败: {sf} | {e}")
                            continue
                        show_name = root_path.name
                        for idx, row in enumerate(cue_rows, 1):
                            text_body = row.get('text', '') or row.get('en', '') or row.get('zh', '')
                            items.append(LearningItem(
                                uid=make_uid(str(vf), str(sf), row.get('start', 0.0), row.get('end', 0.0), text_body, idx),
                                source_type='local',
                                subtitle_text=text_body,
                                start_time=float(row.get('start', 0.0) or 0.0),
                                end_time=float(row.get('end', 0.0) or 0.0),
                                video_path=str(vf),
                                subtitle_path=str(sf),
                                show_name=show_name,
                                season_hint=season,
                                episode_hint=episode,
                                en=row.get('en', ''),
                                zh=row.get('zh', ''),
                                extra={'stem': stem, 'cue_index': idx},
                            ))
                    for stem, sf in subs.items():
                        if stem not in matched_subs and stem not in videos:
                            unmatched.append(f"未配对字幕: {sf}")
            self.finished_ok.emit(items, unmatched)
        except Exception:
            self.failed.emit(traceback.format_exc())


class LocalSearchWorker(QThread):
    finished_ok = Signal(list)
    failed = Signal(str)

    def __init__(self, library: List[LearningItem], keyword: str, path_filter: str = '', limit: int = 0, sort_mode: str = '文件名'):
        super().__init__()
        self.library = library
        self.keyword = (keyword or '').strip().lower()
        self.path_filter = (path_filter or '').strip().lower()
        self.limit = int(limit or 0)
        self.sort_mode = sort_mode or '文件名'

    def run(self):
        try:
            hits: List[LearningItem] = []
            for item in self.library:
                hay = ' '.join([
                    item.subtitle_text or '', item.en or '', item.zh or '',
                    item.show_name or '', item.video_path or '', item.subtitle_path or ''
                ]).lower()
                if self.keyword and self.keyword not in hay:
                    continue
                if self.path_filter:
                    path_hay = ' '.join([item.video_path or '', item.subtitle_path or '', item.show_name or '']).lower()
                    if self.path_filter not in path_hay:
                        continue
                hits.append(item)

            if self.sort_mode == '时间':
                hits.sort(key=lambda x: ((x.video_path or ''), float(x.start_time), float(x.end_time)))
            elif self.sort_mode == '匹配度':
                def score(it: LearningItem):
                    target = ' '.join([it.subtitle_text or '', it.en or '', it.zh or '']).lower()
                    exact = 1 if self.keyword and self.keyword in target else 0
                    pos = target.find(self.keyword) if self.keyword else -1
                    pos = 10**9 if pos < 0 else pos
                    return (-exact, pos, len(target))
                hits.sort(key=score)
            else:
                hits.sort(key=lambda x: ((Path(x.video_path).name if x.video_path else ''), float(x.start_time), float(x.end_time)))

            if self.limit > 0:
                hits = hits[:self.limit]
            self.finished_ok.emit(hits)
        except Exception:
            self.failed.emit(traceback.format_exc())


class OnlineSearchWorker(QThread):
    finished_ok = Signal(list, str)
    failed = Signal(str)

    def __init__(self, keyword: str, settings: dict, limit: int = 20):
        super().__init__()
        self.keyword = (keyword or '').strip()
        self.settings = dict(settings or {})
        self.limit = int(limit or 20)

    def run(self):
        try:
            kind = (self.settings.get('online_search_kind', 'generic_api') or 'generic_api').strip()
            endpoint = (self.settings.get('online_search_endpoint', '') or '').strip()

            if kind == 'direct_web':
                url = endpoint or ''
                if '{query}' in url:
                    url = url.replace('{query}', urllib.parse.quote(self.keyword))
                elif url:
                    url += ('&' if '?' in url else '?') + urllib.parse.urlencode({'q': self.keyword})
                else:
                    url = f"https://www.playphrase.me/api/v1/phrases/search?q={urllib.parse.quote(self.keyword)}"

                if not url:
                    self.finished_ok.emit([], '未配置网页直连模板。')
                    return

                item = LearningItem(
                    uid=make_uid('online-web', url, self.keyword),
                    source_type='online',
                    subtitle_text=self.keyword,
                    start_time=0.0,
                    end_time=0.0,
                    video_url=url,
                    show_name=self.settings.get('online_profile_name', '网页直连'),
                    en=self.keyword,
                    zh='',
                    extra={'direct_web': True},
                )
                self.finished_ok.emit([item], f'网页直连模式：已生成入口 → {url}')
                return

            # 下面是原来的其他逻辑（playphrase_free、generic_api 等）
            if kind == 'playphrase_free':
                url = f"https://www.playphrase.me/#/search?q={urllib.parse.quote(self.keyword)}"
                item = LearningItem(
                    uid=make_uid('playphrase-free-web', url, self.keyword),
                    source_type='online',
                    subtitle_text=self.keyword,
                    start_time=0.0,
                    end_time=0.0,
                    video_url=url,
                    show_name='PlayPhrase 免费网页入口',
                    en=self.keyword,
                    zh='',
                    extra={'direct_web': True, 'free_web': True},
                )
                self.finished_ok.emit([item], f'PlayPhrase 免费网页入口：{url}')
                return

            raw_endpoint = endpoint
            method = (self.settings.get('online_search_method', 'GET') or 'GET').upper()
            endpoints = [x.strip() for x in re.split(r"[|\n]+", raw_endpoint or "") if x.strip()]

            if not endpoints:
                self.finished_ok.emit([], '未配置联网搜索端点。请先到配置中心填写。')
                return

            last_err = None
            for ep in endpoints:
                try:
                    payload = self._make_request(ep, method, self.keyword, kind)
                    items = self._parse_results(payload, ep)
                    if items:
                        self.finished_ok.emit(items, f"联网搜索完成：{len(items)} 条（配置：{self.settings.get('online_profile_name', '')}，端点：{ep}）")
                        return
                    last_err = RuntimeError('接口返回为空')
                except Exception as e:
                    last_err = e

            # 所有 API 都失败时，回退到网页直连
            url = f"https://www.playphrase.me/api/v1/phrases/search?q={urllib.parse.quote(self.keyword)}"
            item = LearningItem(uid=make_uid('playphrase-fallback', url, self.keyword), source_type='online', subtitle_text=self.keyword,
                                start_time=0.0, end_time=0.0, video_url=url,
                                show_name=self.settings.get('online_profile_name', 'PlayPhrase'), en=self.keyword, zh='',
                                extra={'direct_web': True, 'fallback': True})
            self.finished_ok.emit([item], '接口不可用：已回退为网页入口结果，可先查阅或加入下载队列。')
            return

        except Exception:
            self.failed.emit(traceback.format_exc())

    def _build_headers(self) -> dict:
        headers = {'Accept': 'application/json, text/plain, */*'}
        ua = (self.settings.get('user_agent', '') or '').strip()
        if ua:
            headers['User-Agent'] = ua
        referer = (self.settings.get('referer', '') or '').strip()
        if referer:
            headers['Referer'] = referer
        token = (self.settings.get('token', '') or '').strip()
        if token:
            headers['Authorization'] = f'Token {token}' if not token.lower().startswith('token ') else token
        cookie = (self.settings.get('cookie', '') or '').strip()
        if cookie:
            headers['Cookie'] = cookie
        csrf = (self.settings.get('csrf', '') or '').strip()
        if csrf:
            headers['X-CSRFToken'] = csrf
        return headers

    def _make_request(self, endpoint: str, method: str, keyword: str, kind: str):
        headers = self._build_headers()
        timeout = int(self.settings.get('online_timeout', 25) or 25)
        data = None
        url = endpoint
        if kind.startswith('playphrase') or kind == 'playphrase_token':
            params = {'q': keyword, 'limit': self.limit, 'language': 'en', 'platform': 'desktop safari', 'skip': 0}
        else:
            params = {'q': keyword, 'limit': self.limit}
        if method == 'GET':
            url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
        else:
            headers.setdefault('Content-Type', 'application/json')
            data = json.dumps(params, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        proxy = (self.settings.get('proxy', '') or '').strip()
        opener = None
        if proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
        ctx = ssl._create_unverified_context()
        if opener:
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8', errors='ignore')
        else:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode('utf-8', errors='ignore')
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def _parse_results(self, payload, endpoint: str) -> List[LearningItem]:
        data = payload
        if isinstance(data, dict):
            for key in ['results', 'items', 'data', 'phrases', 'matches']:
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
            else:
                data = []
        if not isinstance(data, list):
            data = []
        out: List[LearningItem] = []
        for idx, row in enumerate(data[: max(self.limit, 1)], 1):
            if not isinstance(row, dict):
                continue
            text_body = row.get('text') or row.get('subtitle') or row.get('sentence') or row.get('phrase') or row.get('body') or ''
            en = row.get('en') or text_body
            zh = row.get('zh') or row.get('translation') or row.get('cn') or ''
            start = float(row.get('start') or row.get('time') or row.get('position') or 0.0)
            end = float(row.get('end') or (start + 3.0))
            video_url = row.get('video_url') or row.get('video') or row.get('url') or row.get('clip_url') or ''
            show_name = row.get('show_name') or row.get('source') or row.get('title') or self.settings.get('online_profile_name', '联网结果')
            uid = make_uid(endpoint, video_url, start, end, text_body, idx)
            out.append(LearningItem(
                uid=uid,
                source_type='online',
                subtitle_text=text_body,
                start_time=start,
                end_time=end,
                video_url=video_url,
                show_name=show_name,
                en=en,
                zh=zh,
                extra=row,
            ))
        return out


class AITaskWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, texts: List[str], target: AITarget, settings: dict):
        super().__init__()
        self.texts = texts
        self.target = target
        self.settings = settings

    def run(self):
        try:
            body_text = "\n".join(self.texts)
            if not self.target.endpoint:
                self.finished_ok.emit(f"[未配置端点] 已组合 {len(self.texts)} 条内容，目标：{self.target.name}\n\n{body_text}")
                return
            headers = {}
            try:
                headers = json.loads(self.target.headers_json or "{}")
            except Exception:
                headers = {}
            method = (self.target.method or "POST").upper()
            timeout = int(self.settings.get("ai_timeout", 60) or 60)
            payload = {"target": self.target.name, "text": body_text, "items": self.texts}
            data = None
            url = self.target.endpoint
            if method == "GET":
                url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"q": body_text})
            else:
                headers.setdefault("Content-Type", "application/json")
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            self.finished_ok.emit(raw)
        except Exception as e:
            self.failed.emit(traceback.format_exc() or str(e))


class DownloadWorker(QThread):
    log = Signal(str)
    progress = Signal(int, int, int, str)
    done_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, tasks: List[dict], out_dir: str, max_workers: int = 3):
        super().__init__()
        self.tasks = tasks
        self.out_dir = out_dir
        self.max_workers = max(1, min(10, int(max_workers or 1)))
        self._stop = False
        self._lock = threading.Lock()

    def stop(self):
        self._stop = True

    def _download_one(self, index: int, task: dict):
        if self._stop:
            return {"status": "stopped", "name": task.get("name", "") or f"download_{index}", "index": index}
        url = task.get("url", "").strip()
        name = task.get("name", "") or f"download_{index}"
        ext = task.get("ext", "") or Path(urllib.parse.urlparse(url).path).suffix or ".bin"
        ext = ext if str(ext).startswith(".") else f".{ext}"
        safe_name = re.sub(r'[\/:*?"<>|]+', '_', name).strip() or f"download_{index}"
        out_path = Path(self.out_dir) / f"{safe_name}{ext}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            self.log.emit(f"开始下载：{safe_name}")
            context = ssl.create_default_context()
            try:
                opener = urllib.request.urlopen(req, timeout=120, context=context)
            except TypeError:
                opener = urllib.request.urlopen(req, timeout=120)
            except Exception:
                context = ssl._create_unverified_context()
                opener = urllib.request.urlopen(req, timeout=120, context=context)
            with opener as resp, open(out_path, "wb") as f:
                while True:
                    if self._stop:
                        break
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
            if self._stop:
                try:
                    if out_path.exists():
                        out_path.unlink()
                except Exception:
                    pass
                return {"status": "stopped", "name": safe_name, "index": index}
            return {"status": "ok", "name": safe_name, "path": str(out_path), "index": index}
        except Exception as e:
            return {"status": "fail", "name": safe_name, "url": url, "error": str(e), "index": index}

    def run(self):
        try:
            safe_mkdir(Path(self.out_dir))
            total = len(self.tasks)
            if total <= 0:
                self.done_ok.emit({"total": 0, "success": 0, "failed": 0, "failed_items": [], "stopped": False})
                return
            ok = fail = done = 0
            failed_items = []
            self.log.emit(f"批量下载开始：共 {total} 项，线程数 {self.max_workers}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                futures = [ex.submit(self._download_one, idx, task) for idx, task in enumerate(self.tasks, 1)]
                for fut in concurrent.futures.as_completed(futures):
                    res = fut.result()
                    done += 1
                    name = res.get("name", "")
                    if res.get("status") == "ok":
                        ok += 1
                        self.log.emit(f"完成：{name}")
                    elif res.get("status") == "fail":
                        fail += 1
                        failed_items.append(res)
                        self.log.emit(f"失败：{name}\n{res.get('error', '')}")

                    else:
                        self.log.emit(f"停止：{name}")
                    pct = int(done * 100 / max(total, 1))
                    self.progress.emit(done, total, pct, name)
                    if self._stop:
                        break
            self.done_ok.emit({"total": total, "success": ok, "failed": fail, "failed_items": failed_items, "stopped": self._stop})
        except Exception as e:
            self.failed.emit(traceback.format_exc() or str(e))


class TranslateLineWorker(QThread):
    finished_ok = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, cache_key: str, text: str, engine: str):
        super().__init__()
        self.cache_key = cache_key
        self.text = (text or "").strip()
        self.engine = engine

    def run(self):
        try:
            result = translate_text(self.text, self.engine) if self.text else ""
            self.finished_ok.emit(self.cache_key, result)
        except Exception as e:
            self.failed.emit(self.cache_key, str(e))


def kill_process_tree(proc: subprocess.Popen):
    if proc is None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def query_gpu_memory_mb() -> Optional[int]:
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return None
    try:
        result = subprocess.run(
            [nvidia_smi, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return None
        lines = [x.strip() for x in result.stdout.splitlines() if x.strip()]
        if not lines:
            return None
        return int(lines[0])
    except Exception:
        return None


def wait_gpu_release(log_cb=None, target_mb: int = 800, max_wait: float = 24.0, poll: float = 0.5):
    used = query_gpu_memory_mb()
    if used is None:
        time.sleep(1.0)
        return
    if log_cb:
        log_cb(f"检测显存释放：当前 {used} MB，目标 ≤ {target_mb} MB。")
    start = time.time()
    last_logged = None
    while time.time() - start < max_wait:
        used = query_gpu_memory_mb()
        if used is None:
            break
        if used <= target_mb:
            if log_cb:
                log_cb(f"显存已回落到 {used} MB，继续下一条。")
            return
        if log_cb and (last_logged is None or abs(used - last_logged) >= 100):
            log_cb(f"等待显存释放中：当前 {used} MB ...")
            last_logged = used
        time.sleep(poll)
    if log_cb:
        used = query_gpu_memory_mb()
        if used is not None:
            log_cb(f"等待超时，当前显存约 {used} MB，继续执行。")
    time.sleep(0.8)





class BatchSrtWorker(QThread):
    log = Signal(str)
    progress = Signal(int, int, int, str)
    done_ok = Signal(dict)
    failed = Signal(str)

    def __init__(self, exe_path: str, folder: str, model: str, model_path: str, language: str, vad: bool,
                 enhance: bool, save_same_dir: bool, out_dir: str, extra_args: str,
                 skip_existing: bool, overwrite_existing: bool, threads: int):
        super().__init__()
        self.exe_path = exe_path
        self.folder = folder
        self.model = model
        self.model_path = model_path
        self.language = language
        self.vad = vad
        self.enhance = enhance
        self.save_same_dir = save_same_dir
        self.out_dir = out_dir
        self.extra_args = extra_args
        self.skip_existing = skip_existing
        self.overwrite_existing = overwrite_existing
        self.threads = max(1, min(10, threads))
        self._cancel = False
        self._proc_lock = threading.Lock()
        self._active_procs: set = set()

    def cancel(self):
        self._cancel = True
        with self._proc_lock:
            for p in list(self._active_procs):
                kill_process_tree(p)

    def build_cmd(self, input_path: Path, output_dir: Path, model_name: Optional[str] = None, enhance_override: Optional[bool] = None) -> List[str]:
        use_model = model_name or self.model
        use_enhance = self.enhance if enhance_override is None else enhance_override
        cmd = [self.exe_path, str(input_path), "--model", use_model, "--output_format", "srt"]
        if self.model_path.strip():
            cmd += ["--model_dir", self.model_path.strip()]
        if self.language and self.language != "auto":
            cmd += ["--language", self.language]
        if self.vad:
            cmd += ["--vad_filter", "True"]
        if use_enhance:
            cmd += ["--demucs", "True"]
        if output_dir:
            cmd += ["--output_dir", str(output_dir)]
        if self.extra_args.strip():
            extra = shlex.split(self.extra_args.strip())
            if not use_enhance:
                filtered = []
                skip_next = False
                for tok in extra:
                    if skip_next:
                        skip_next = False
                        continue
                    low = tok.lower()
                    if low == "--demucs":
                        skip_next = True
                        continue
                    if low == "true":
                        continue
                    filtered.append(tok)
                extra = filtered
            cmd += extra
        return cmd

    def target_srt(self, video: Path, output_dir: Path) -> Path:
        return output_dir / f"{video.stem}.srt"

    def _post_process_cooldown(self, log_lines: List[str], gpu_target_mb: int):
        wait_gpu_release(log_cb=log_lines.append, target_mb=gpu_target_mb)
        cooldown = 1.5
        log_lines.append(f"显存释放检测完成，额外延迟 {cooldown:.1f} 秒后再启动下一条。")
        time.sleep(cooldown)

    def _run_external_once(self, cmd: List[str], video_name: str, gpu_target_mb: int) -> Tuple[int, List[str]]:
        logs: List[str] = ["执行命令: " + " ".join(shlex.quote(x) for x in cmd)]
        if self._cancel:
            return -999, logs + ["用户已取消"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        with self._proc_lock:
            self._active_procs.add(proc)
        try:
            if proc.stdout is not None:
                for line in proc.stdout:
                    if self._cancel:
                        logs.append("用户取消，终止当前转换进程。")
                        kill_process_tree(proc)
                        return -999, logs
                    logs.append(f"[{video_name}] {line.rstrip()}")
            rc = proc.wait()
        finally:
            with self._proc_lock:
                self._active_procs.discard(proc)
        self._post_process_cooldown(logs, gpu_target_mb=gpu_target_mb)
        return rc, logs

    def process_one(self, video: Path) -> dict:
        target_dir = video.parent if self.save_same_dir else Path(self.out_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        existing_srt = self.target_srt(video, target_dir)
        if existing_srt.exists():
            if self.skip_existing:
                return {"status": "skip", "file": video.name, "log": [f"跳过已有字幕: {existing_srt}"]}
            if not self.overwrite_existing:
                return {"status": "skip", "file": video.name, "log": [f"保留已有字幕，未覆盖: {existing_srt}"]}

        logs = [
            "----------------------------------------------------------",
            "字幕由 Whisper AI 创建。",
            "PotPlayer 不参与 Whisper AI 转换。",
            "因此，如果翻译错误或结果异常，请联系引擎开发人员。",
            "----------------------------------------------------------",
            f"开始处理: {video}",
            "----------------------------------------------------------",
            "开始转换（严格串行安全模式）",
            "----------------------------------------------------------",
        ]
        if self._cancel:
            return {"status": "cancel", "file": video.name, "log": logs + ["用户已取消"]}

        gpu_target_mb = 900 if self.enhance else 700
        cmd = self.build_cmd(video, target_dir)
        rc, run_logs = self._run_external_once(cmd, video.name, gpu_target_mb=gpu_target_mb)
        logs.extend(run_logs)

        if self._cancel or rc == -999:
            return {"status": "cancel", "file": video.name, "log": logs}
        if rc != 0:
            logs.append(f"退出码 {rc}")
            safe_retry = (self.model.startswith("large") or self.enhance) and not self._cancel
            if safe_retry:
                logs.append("主转换失败，自动进入安全重试：model=medium，关闭增强。")
                retry_cmd = self.build_cmd(video, target_dir, model_name="medium", enhance_override=False)
                rc2, retry_logs = self._run_external_once(retry_cmd, video.name, gpu_target_mb=650)
                logs.extend("[retry] " + x if not x.startswith("[") else x for x in retry_logs)
                if self._cancel or rc2 == -999:
                    return {"status": "cancel", "file": video.name, "log": logs}
                if rc2 == 0:
                    logs += ["----------------------------------------------------------", "安全重试成功", "----------------------------------------------------------"]
                    return {"status": "ok", "file": video.name, "log": logs}
                logs.append(f"安全重试仍失败，退出码 {rc2}")
            return {"status": "fail", "file": video.name, "rc": rc, "log": logs}

        logs += ["----------------------------------------------------------", "转换完成", "----------------------------------------------------------"]
        return {"status": "ok", "file": video.name, "log": logs}

    def run(self):
        try:
            folder = Path(self.folder)
            if not folder.exists():
                raise FileNotFoundError(f'目录不存在: {folder}')
            videos = sorted([p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in VIDEO_EXTS], key=lambda x: str(x).lower())
            total = len(videos)
            if total <= 0:
                raise RuntimeError('未找到可处理的视频文件。')

            success_files = []
            skipped_files = []
            failed_files = []

            for idx, video in enumerate(videos, 1):
                if self._cancel:
                    break
                pct_before = int((idx - 1) * 100 / total) if total else 0
                self.progress.emit(idx - 1, total, pct_before, video.name)
                result = self.process_one(video)
                for line in result.get('log', []) or []:
                    try:
                        self.log.emit(str(line))
                    except Exception:
                        pass

                status = result.get('status')
                if status == 'ok':
                    success_files.append(video.name)
                elif status == 'skip':
                    skipped_files.append(video.name)
                elif status == 'cancel':
                    break
                else:
                    failed_files.append({'file': video.name, 'rc': result.get('rc', -1)})

                pct_after = int(idx * 100 / total) if total else 100
                self.progress.emit(idx, total, pct_after, video.name)

            summary = {
                'total': total,
                'success': len(success_files),
                'skipped': len(skipped_files),
                'failed': len(failed_files),
                'failed_files': failed_files,
                'cancelled': self._cancel,
            }
            self.done_ok.emit(summary)
        except Exception:
            self.failed.emit(traceback.format_exc())

def translate_text(text: str, engine: str = "MyMemory 免费", timeout: int = 10) -> str:
    text = (text or "").strip()
    if not text or engine in ("无翻译", ""):
        return ""
    try:
        if engine == "LibreTranslate 免费":
            payload = json.dumps({"q": text, "source": "en", "target": "zh", "format": "text"}).encode("utf-8")
            req = urllib.request.Request(
                "https://libretranslate.de/translate",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return data.get("translatedText", "")
        q = urllib.parse.urlencode({"q": text, "langpair": "en|zh-CN"})
        url = f"https://api.mymemory.translated.net/get?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return data.get("responseData", {}).get("translatedText", "")
    except Exception:
        return ""


class WordActionDialog(QDialog):
    add_vocab = Signal(str, str)
    send_ai = Signal(str)
    lookup_requested = Signal(str)

    def __init__(self, sentence: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("词 / 句操作")
        self.resize(700, 340)
        lay = QVBoxLayout(self)
        hint = QLabel("双击搜索结果后进入这里：可选词、复制、查词、加入生词本、发送 AI。")
        lay.addWidget(hint)
        self.editor = QTextEdit()
        self.editor.setPlainText(sentence)
        lay.addWidget(self.editor, 1)
        row = QHBoxLayout()
        self.selected_preview = QLabel("当前选中：")
        copy_btn = QPushButton("复制选中")
        dict_btn = QPushButton("查词（内部词典）")
        vocab_btn = QPushButton("加入生词本")
        ai_btn = QPushButton("发送到 AI")
        for w in [copy_btn, dict_btn, vocab_btn, ai_btn]:
            row.addWidget(w)
        row.addStretch()
        lay.addLayout(row)
        lay.addWidget(self.selected_preview)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        lay.addWidget(btns)
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        self.editor.copyAvailable.connect(lambda ok: self.selected_preview.setText(f"当前选中：{self.current_text()}" if ok else "当前选中："))
        copy_btn.clicked.connect(self.copy_selected)
        dict_btn.clicked.connect(self.open_dict)
        vocab_btn.clicked.connect(self.add_to_vocab)
        ai_btn.clicked.connect(self.send_to_ai_clicked)

    def current_text(self) -> str:
        txt = self.editor.textCursor().selectedText().strip()
        if txt:
            return txt
        text, ok = QInputDialog.getText(self, "输入目标词", "未选中文本，请手动输入词或短语：")
        return text.strip() if ok else ""

    def copy_selected(self):
        txt = self.current_text()
        if txt:
            QApplication.clipboard().setText(txt)

    def open_dict(self):
        txt = self.current_text()
        if txt:
            self.lookup_requested.emit(txt)

    def add_to_vocab(self):
        txt = self.current_text()
        if txt:
            self.add_vocab.emit(txt, self.editor.toPlainText())

    def send_to_ai_clicked(self):
        txt = self.current_text()
        if txt:
            self.send_ai.emit(txt)


class EmbeddedWebView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("输入网址或由系统自动填入")
        self.go_btn = QPushButton("打开")
        top = QHBoxLayout()
        top.addWidget(self.url_bar, 1)
        top.addWidget(self.go_btn)
        lay.addLayout(top)
        if QWebEngineView is not None:
            self.browser = QWebEngineView()
            self.go_btn.clicked.connect(lambda: self.load_url(self.url_bar.text().strip()))
        else:
            self.browser = QTextBrowser()
            self.browser.setOpenExternalLinks(False)
            self.go_btn.clicked.connect(lambda: self.load_url(self.url_bar.text().strip()))
        lay.addWidget(self.browser, 1)

    def load_url(self, url: str):
        if not url:
            return
        self.url_bar.setText(url)
        if QWebEngineView is not None:
            self.browser.setUrl(QUrl(url))
        else:
            try:
                self.browser.setSource(QUrl(url))
            except Exception:
                self.browser.setPlainText(f"当前环境未启用 WebEngine，无法完整内嵌打开：\n{url}")




class VerticalDragHandle(QWidget):
    valueChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 220
        self._maximum = 900
        self._value = 360
        self._drag_origin_y = None
        self._drag_origin_value = None

        self.setCursor(Qt.SizeVerCursor)
        self.setToolTip("上下拖动这里只调整学习区高度")
        self.setFixedWidth(22)
        self.setMinimumHeight(180)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # 创建子控件
        self.track = QFrame(self)
        self.track.setObjectName("learningHeightTrack")

        self.thumb = QFrame(self.track)
        self.thumb.setObjectName("learningHeightThumb")

        # 使用更安全的样式表写法（推荐方式）
        self.setStyleSheet("""
            QFrame#learningHeightTrack {
                background: rgba(255, 255, 255, 0.16);
                border: 1px solid rgba(255, 255, 255, 0.28);
                border-radius: 8px;
            }
            QFrame#learningHeightThumb {
                background: rgba(45, 155, 255, 0.95);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.45);
            }
        """)

    # 下面是原来的拖动逻辑，保持不变
    def setRange(self, minimum: int, maximum: int):
        self._minimum = int(minimum)
        self._maximum = max(int(maximum), self._minimum + 1)
        self.setValue(self._value)

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def value(self):
        return self._value

    def setValue(self, value: int):
        value = max(self._minimum, min(self._maximum, int(value)))
        changed = value != self._value
        self._value = value
        self._update_thumb()
        if changed and not self.signalsBlocked():
            self.valueChanged.emit(self._value)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.track.setGeometry(int((self.width() - 12) / 2), 6, 12, max(24, self.height() - 12))
        self._update_thumb()

    def _thumb_height(self):
        return max(36, min(64, int(self.track.height() * 0.22)))

    def _update_thumb(self):
        if self.track.height() <= 0:
            return
        thumb_h = self._thumb_height()
        span = max(1, self.track.height() - thumb_h)
        ratio = 0.0 if self._maximum <= self._minimum else (self._value - self._minimum) / float(self._maximum - self._minimum)
        y = int((1.0 - ratio) * span)
        self.thumb.setGeometry(0, y, self.track.width(), thumb_h)
        self.thumb.raise_()

    def _position_to_value(self, y: int) -> int:
        thumb_h = self._thumb_height()
        span = max(1, self.track.height() - thumb_h)
        local_y = max(0, min(span, y - self.track.y() - int(thumb_h / 2)))
        ratio = 1.0 - (local_y / float(span))
        return int(round(self._minimum + ratio * (self._maximum - self._minimum)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_origin_y = event.globalPosition().toPoint().y()
            self._drag_origin_value = self._value
            self.setValue(self._position_to_value(event.position().toPoint().y()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin_y is not None and event.buttons() & Qt.LeftButton:
            self.setValue(self._position_to_value(event.position().toPoint().y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin_y = None
        self._drag_origin_value = None
        super().mouseReleaseEvent(event)

    def setRange(self, minimum: int, maximum: int):
        self._minimum = int(minimum)
        self._maximum = max(int(maximum), self._minimum + 1)
        self.setValue(self._value)

    def minimum(self):
        return self._minimum

    def maximum(self):
        return self._maximum

    def value(self):
        return self._value

    def setValue(self, value: int):
        value = max(self._minimum, min(self._maximum, int(value)))
        changed = value != self._value
        self._value = value
        self._update_thumb()
        if changed and not self.signalsBlocked():
            self.valueChanged.emit(self._value)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.track.setGeometry(int((self.width() - 12) / 2), 6, 12, max(24, self.height() - 12))
        self._update_thumb()

    def _thumb_height(self):
        return max(36, min(64, int(self.track.height() * 0.22)))

    def _update_thumb(self):
        if self.track.height() <= 0:
            return
        thumb_h = self._thumb_height()
        span = max(1, self.track.height() - thumb_h)
        ratio = 0.0 if self._maximum <= self._minimum else (self._value - self._minimum) / float(self._maximum - self._minimum)
        y = int((1.0 - ratio) * span)
        self.thumb.setGeometry(0, y, self.track.width(), thumb_h)
        self.thumb.raise_()

    def _position_to_value(self, y: int) -> int:
        thumb_h = self._thumb_height()
        span = max(1, self.track.height() - thumb_h)
        local_y = max(0, min(span, y - self.track.y() - int(thumb_h / 2)))
        ratio = 1.0 - (local_y / float(span))
        return int(round(self._minimum + ratio * (self._maximum - self._minimum)))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_origin_y = event.globalPosition().toPoint().y()
            self._drag_origin_value = self._value
            self.setValue(self._position_to_value(event.position().toPoint().y()))
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_origin_y is not None and event.buttons() & Qt.LeftButton:
            self.setValue(self._position_to_value(event.position().toPoint().y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_origin_y = None
        self._drag_origin_value = None
        super().mouseReleaseEvent(event)

class ShortcutSettingsDialog(QDialog):
    def __init__(self, shortcut_map: Dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("快捷键设置面板")
        self.resize(620, 420)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("你可以直接修改快捷键文本，例如 Up / Ctrl+F / Space。ESC 仍由视频控件兜底处理。"))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["功能", "快捷键"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.table, 1)
        labels = [
            ("上一个样本", "sample_prev"),
            ("下一个样本", "sample_next"),
            ("上一句", "sentence_prev"),
            ("下一句", "sentence_next"),
            ("播放/暂停", "toggle_play"),
            ("聚焦搜索框", "focus_search"),
            ("恢复布局", "restore_layout"),
            ("全屏/退出全屏", "toggle_fullscreen"),
            ("下一个主题", "cycle_theme_next"),
            ("上一个主题", "cycle_theme_prev"),
            ("下一个配色", "cycle_palette_next"),
            ("上一个配色", "cycle_palette_prev"),
            ("字幕显示：单", "subtitle_single"),
            ("字幕显示：双", "subtitle_dual"),
            ("字幕显示：无", "subtitle_none"),
            ("截图", "take_screenshot"),
            ("录制", "record_placeholder"),
            ("隐藏底部学习区", "toggle_bottom_learning"),
            ("隐藏顶部按钮区", "toggle_top_bar"),
            ("隐藏学习提示", "toggle_learning_hint"),
            ("显示/隐藏搜索结果区", "toggle_search_results"),
            ("显示/隐藏播放列表区", "toggle_playlist_panel"),
            ("显示/隐藏进度条", "toggle_progress_bar"),
            ("显示/隐藏控制按钮栏", "toggle_control_buttons"),
            ("显示/隐藏学习动作栏", "toggle_learning_actions"),
            ("显示/隐藏文本面板", "toggle_text_panel"),
            ("打开快捷键面板", "shortcut_settings_panel"),
            ("改变播放速度", "change_speed"),
            ("句子跳转 +1", "jump_sentence_next"),
            ("句子跳转 -1", "jump_sentence_prev"),
        ]
        for label, key in labels:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(shortcut_map.get(key, "")))
            self.table.item(row, 0).setData(Qt.UserRole, key)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_shortcuts(self) -> Dict[str, str]:
        result = {}
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).data(Qt.UserRole)
            val = self.table.item(row, 1).text().strip()
            if key:
                result[key] = val
        return result


class MainWindow(QMainWindow, LocalFontSettingsMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1860, 1080)
        self.settings = load_settings()
        # 【重要修复】保存设置后强制重新加载并应用主题和配色
        saved_theme = self.settings.get("theme_name", "曜石金奢").strip()
        saved_palette = self.settings.get("palette_name", "").strip()
        print(f"[INIT-LOAD] 从配置文件读取 → 主题: {saved_theme} | 配色: {saved_palette}")
        self.local_font_settings = self.settings.get("local_font_settings", {})
        self.state = AppState()
        self.local_library: List[LearningItem] = []
        self.local_results: List[LearningItem] = []
        self.online_results: List[LearningItem] = []
        self.notes_store: Dict[str, str] = {}
        self.notes_records: Dict[str, dict] = {}
        self.vocab_store: List[VocabularyEntry] = []
        self.current_subs: List[dict] = []
        self.current_item: Optional[LearningItem] = None
        self.current_segment_end_ms = -1
        self.subtitle_display_mode = self.settings.get("subtitle_display_mode", "dual")
        self.floating_subtitle_enabled = bool(self.settings.get("floating_subtitle_enabled", False))
        self._player_slider_was_playing = False
        self._is_user_seeking = False
        self._last_subtitle_key = None
        self.translate_workers: Dict[str, TranslateLineWorker] = {}
        self.line_translation_cache: Dict[str, str] = {}
        self.ai_targets: List[AITarget] = self._load_ai_targets()
        self.network_profiles: List[dict] = self._load_network_profiles()
        self._network_profile_sync_guard = False
        self.learning_mode_visible = True
        self.pending_download_cleanup: List[Path] = []
        self._rendering_tables = False
        self._shortcut_objects: List[QShortcut] = []
        self.search_visible_columns = self.settings.get("search_visible_columns", {name: True for name in SEARCH_RESULT_COLUMNS})

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio)

        self._load_persistent_stores()
        self._build_ui()
        self.apply_theme(self.settings.get("theme_name", "曜石金奢"))
        self._load_settings_to_ui()
        # 【修复初始化】确保设置正确加载
        self._settings_dirty = False
        if not hasattr(self, 'active_network_profile'):
            self.active_network_profile = None
        self._bind_player()
        self._register_shortcuts()
        try:
            self.apply_local_font_settings_to_widgets()
        except Exception:
            pass
        try:
            if hasattr(self, 'cfg_theme_info'):
                self.cfg_theme_info.setText(f"当前主题：{self.settings.get('theme_name', '')}")
            if hasattr(self, 'cfg_palette_info'):
                self.cfg_palette_info.setText(f"当前配色：{self.settings.get('palette_name', '')}")
            if hasattr(self, 'config_status_label'):
                self.config_status_label.setText(f"已应用主题：{self.settings.get('theme_name', '')} / {self.settings.get('palette_name', '')}")
        except Exception:
            pass
        try:
            self.apply_subtitle_style_settings()
        except Exception:
            pass

        # ====================== 【最终强制修复 - 加在这里】 ======================
        # 确保所有控件创建完成后，强制加载保存的主题和配色
        QTimer.singleShot(100, self.force_reload_theme_and_palette)
        # ============================================================================
        # 【重要新增】确保配色、播放次数等控件变化时能自动保存
        important_widgets = [
            getattr(self, 'palette_combo', None),
            getattr(self, 'loop_count_spin', None),
            getattr(self, 'loop_mode_combo', None),
            getattr(self, 'play_speed_combo', None),
            getattr(self, 'theme_combo', None),
            getattr(self, 'online_profile_combo', None),
        ]
        for w in important_widgets:
            if w is None:
                continue
            try:
                if hasattr(w, 'currentTextChanged'):
                    w.currentTextChanged.connect(self.schedule_settings_autosave)
                if hasattr(w, 'valueChanged'):
                    w.valueChanged.connect(self.schedule_settings_autosave)
                if hasattr(w, 'toggled') or hasattr(w, 'stateChanged'):
                    if hasattr(w, 'toggled'):
                        w.toggled.connect(self.schedule_settings_autosave)
                    if hasattr(w, 'stateChanged'):
                        w.stateChanged.connect(self.schedule_settings_autosave)
            except Exception:
                pass
    # ---------- setup ----------
    def _bind_player(self):
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.errorOccurred.connect(lambda err, msg: self.append_log(f"播放器错误：{msg}"))

    def on_ui_scale_changed(self, value: str):
        scale_text = normalize_ui_scale_text(value)
        m = re.match(r"^(\d{1,3})%$", scale_text)
        percent = int(m.group(1)) if m else 100
        percent = max(40, min(300, percent))
        scale_text = f"{percent}%"
        try:
            if getattr(self, "ui_scale_combo", None) is not None and self.ui_scale_combo.currentText() != scale_text:
                old_block = self.ui_scale_combo.blockSignals(True)
                self.ui_scale_combo.setCurrentText(scale_text)
                self.ui_scale_combo.blockSignals(old_block)
        except Exception:
            pass
        self.settings["ui_scale_percent"] = scale_text
        try:
            app = QApplication.instance()
            if app is not None:
                font = app.font()
                base_pt = self.settings.get("_base_app_font_pt")
                if base_pt is None:
                    base_pt = font.pointSizeF() if font.pointSizeF() > 0 else 10.0
                    self.settings["_base_app_font_pt"] = base_pt
                font.setPointSizeF(float(base_pt) * percent / 100.0)
                app.setFont(font)
        except Exception:
            pass
        try:
            self._apply_ui_scale_stylesheet(percent)
        except Exception:
            pass
        try:
            if getattr(self, "config_status_label", None) is not None:
                self.config_status_label.setText(f"界面缩放已设置为 {scale_text}")
        except Exception:
            pass

    def _apply_ui_scale_stylesheet(self, percent: int = None):
        try:
            if percent is None:
                scale_text = normalize_ui_scale_text(self.settings.get("ui_scale_percent", "100%"))
                m = re.match(r"^(\d{1,3})%$", scale_text)
                percent = int(m.group(1)) if m else 100
            percent = max(40, min(300, int(percent)))
        except Exception:
            percent = 100
        base = max(11, int(round(13 * percent / 100.0)))
        small = max(10, int(round(12 * percent / 100.0)))
        large = max(13, int(round(15 * percent / 100.0)))
        ctrl_h = max(34, int(round(34 * percent / 100.0)))
        spin_h = max(34, int(round(34 * percent / 100.0)))
        pad_v = max(4, int(round(4 * percent / 100.0)))
        pad_h = max(8, int(round(8 * percent / 100.0)))
        block = f"""
/*__UI_SCALE_START__*/
QWidget {{ font-size: {base}px; }}
QPushButton, QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit, QTextBrowser, QListWidget, QTableWidget {{ font-size: {base}px; }}
QLineEdit, QComboBox, QAbstractSpinBox {{ min-height: {ctrl_h}px; padding: {pad_v}px {pad_h}px; }}
QPushButton {{ min-height: {ctrl_h}px; padding: {pad_v}px {pad_h}px; }}
QPlainTextEdit, QTextEdit, QTextBrowser {{ padding: {pad_v}px {pad_h}px; }}
QLabel {{ font-size: {base}px; }}
QGroupBox::title {{ font-size: {large}px; font-weight: 700; }}
QHeaderView::section {{ font-size: {small}px; }}
/*__UI_SCALE_END__*/
"""
        css = self.styleSheet() or ''
        css = re.sub(r"/\*__UI_SCALE_START__\*/.*?/\*__UI_SCALE_END__\*/", '', css, flags=re.S)
        self.setStyleSheet((css.rstrip() + "\n" + block).strip())

    def _iter_layout_widgets(self, layout):
        if layout is None:
            return
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                yield w
                continue
            sub = item.layout()
            if sub is not None:
                yield from self._iter_layout_widgets(sub)

    def _set_layout_widgets_visible(self, layout, visible: bool):
        for w in self._iter_layout_widgets(layout):
            w.setVisible(bool(visible))

    def _layout_widgets_visible(self, layout) -> bool:
        for w in self._iter_layout_widgets(layout):
            return w.isVisible()
        return True

    def _strip_style_marker(self, css: str, marker: str) -> str:
        css = css or ''
        return re.sub(rf"/\*__{re.escape(marker)}_START__\*/.*?/\*__{re.escape(marker)}_END__\*/", '', css, flags=re.S)

    def _apply_style_marker(self, widget, marker: str, body: str):
        if widget is None:
            return
        css = self._strip_style_marker(widget.styleSheet() or '', marker)
        body = (body or '').strip()
        if body:
            css = (css.rstrip() + f"\n/*__{marker}_START__*/\n{body}\n/*__{marker}_END__*/").strip()
        widget.setStyleSheet(css)

    def _font_section_targets(self, section: str):
        if section == 'all_widgets':
            return [w for w in self.findChildren(QWidget) if not isinstance(w, (QMenu, QDialog))]

        section = (section or '').strip()
        targets = []
        if section == 'search_options':
            roots = [getattr(self, 'local_result_table', None), getattr(self, 'local_result_status', None)]
            for root in roots:
                if root is None: continue
                targets.append(root)
                if hasattr(root, 'findChildren'):
                    targets.extend(root.findChildren(QWidget))
        elif section == 'playlist_options':
            roots = [getattr(self, 'playlist_table', None)]
            for root in roots:
                if root is None: continue
                targets.append(root)
                if hasattr(root, 'findChildren'):
                    targets.extend(root.findChildren(QWidget))
        elif section == 'play_options':
            roots = [getattr(self, 'player_group', None)]
            for root in roots:
                if root is None: continue
                targets.append(root)
                if hasattr(root, 'findChildren'):
                    targets.extend(root.findChildren(QWidget))
        elif section == 'learning_options':
            roots = [getattr(self, 'learning_group', None), getattr(self, 'sub_box', None)]
            excluded = {getattr(self, 'subtitle_browser', None), getattr(self, 'translation_browser', None), getattr(self, 'floating_subtitle', None)}
            for root in roots:
                if root is None: continue
                candidates = [root]
                if hasattr(root, 'findChildren'):
                    candidates.extend(root.findChildren(QWidget))
                for w in candidates:
                    if w in excluded: continue
                    targets.append(w)
        elif section == 'text_input_options':
            types = (QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QComboBox, QSpinBox)
            targets = [w for w in self.findChildren(QWidget) if isinstance(w, types)]
        elif section == 'button_options':
            targets = [w for w in self.findChildren(QPushButton)]
        else:
            roots = [getattr(self, section, None)]
            for root in roots:
                if root is None: continue
                targets.append(root)
                if hasattr(root, 'findChildren'):
                    targets.extend(root.findChildren(QWidget))

        seen = set()
        out = []
        for w in targets:
            if w is None: continue
            oid = id(w)
            if oid in seen: continue
            seen.add(oid)
            out.append(w)
        return out
 


    def _section_roots_for_font(self, section: str):
        mapping = {
            'search_options': [getattr(self, 'local_result_table', None)],
            'playlist_options': [getattr(self, 'playlist_table', None)],
            'play_options': [getattr(self, 'player_group', None)],
            'learning_options': [getattr(self, 'learning_group', None), getattr(self, 'sub_box', None)],
            'text_input_options': [self.centralWidget()] if self.centralWidget() is not None else [],
            'button_options': [self.centralWidget()] if self.centralWidget() is not None else [],
        }
        return [w for w in mapping.get(section, []) if w is not None]

    def _font_section_title(self, section: str) -> str:
        return {
            'search_options': '搜索列表',
            'playlist_options': '播放列表',
            'play_options': '播放区',
            'learning_options': '学习区',
            'text_input_options': '文本输入框',
            'button_options': '按钮文字',
        }.get(section, '字体 / 颜色设置')

    def _font_panel_sections(self):
        return [
            ('search_options', '搜索列表'),
            ('playlist_options', '播放列表'),
            ('play_options', '播放区'),
            ('learning_options', '学习区'),
        ]

    def _normalize_qfontdialog_result(self, result, fallback_font=None):
        """兼容不同 Qt 绑定下 QFontDialog.getFont 返回顺序差异。"""
        fallback = fallback_font if isinstance(fallback_font, QFont) else self.font()
        try:
            if isinstance(result, tuple) and len(result) >= 2:
                a, b = result[0], result[1]
                if isinstance(a, QFont) and isinstance(b, bool):
                    return a, b
                if isinstance(a, bool) and isinstance(b, QFont):
                    return b, a
                if isinstance(a, QFont):
                    return a, bool(b)
                if isinstance(b, QFont):
                    return b, bool(a)
            if isinstance(result, QFont):
                return result, True
        except Exception:
            pass
        return fallback, False

    def _clear_all_widgets_font_override(self):
        app_font = QApplication.font() if QApplication.instance() is not None else self.font()
        for w in self._font_section_targets('all_widgets'):
            try:
                w.setFont(app_font)
            except Exception:
                pass
            try:
                self._apply_style_marker(w, 'FONT_ALL_WIDGETS', '')
            except Exception:
                pass

    def open_font_style_control_panel(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('字体样式 / 颜色总面板')
        dialog.resize(1020, 720)
        root = QVBoxLayout(dialog)

        root.addWidget(QLabel('选择要设置的区域：'))

        global_btn = QPushButton('🌐 全局所有控件字体 / 颜色')
        global_btn.setStyleSheet('font-weight: bold; padding: 8px;')
        global_btn.clicked.connect(lambda: self.open_local_font_settings('all_widgets'))
        root.addWidget(global_btn)

        btn_layout = QHBoxLayout()
        for sec, title in self._font_panel_sections():
            btn = QPushButton(title)
            btn.clicked.connect(lambda checked=False, s=sec: self.open_local_font_settings(s))
            btn_layout.addWidget(btn)
        root.addLayout(btn_layout)

        extra_layout = QHBoxLayout()
        text_btn = QPushButton('文本输入框字体 / 颜色')
        text_btn.clicked.connect(lambda: self.open_local_font_settings('text_input_options'))
        btn_btn = QPushButton('按钮字体 / 颜色')
        btn_btn.clicked.connect(lambda: self.open_local_font_settings('button_options'))
        extra_layout.addWidget(text_btn)
        extra_layout.addWidget(btn_btn)
        root.addLayout(extra_layout)

        visibility_btn = QPushButton('🔄 显示 / 隐藏 面板（一键切换）')
        visibility_btn.setStyleSheet('font-weight: bold; font-size: 15px; padding: 12px; background: #2c7be5; color: white;')
        visibility_btn.clicked.connect(self.open_visibility_panel)
        root.addWidget(visibility_btn)

        subtitle_btn = QPushButton('字幕样式（单独设置）')
        subtitle_btn.clicked.connect(self.open_subtitle_style_settings)
        root.addWidget(subtitle_btn)

        root.addStretch()
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        btns.accepted.connect(lambda: self.save_all_settings(silent=False))
        btns.rejected.connect(dialog.reject)
        root.addWidget(btns)

        dialog.exec()

    def open_visibility_panel(self):
        """显示/隐藏 一键控制面板"""
        dialog = QDialog(self)
        dialog.setWindowTitle('界面元素 显示 / 隐藏')
        dialog.resize(720, 580)
        lay = QVBoxLayout(dialog)
        lay.setSpacing(15)

        lay.addWidget(QLabel('<b>点击按钮即可切换显示或隐藏状态：</b>'))

        items = [
            ('搜索结果区',          lambda: self.toggle_group_visibility('local_search_group')),
            ('播放列表区',          lambda: self.toggle_group_visibility('playlist_group')),
            ('顶部按钮工具栏',      self.toggle_top_toolbar),
            ('进度条',              self.toggle_progress_toolbar),
            ('播放控制按钮栏',      self.toggle_control_button_bar),
            ('学习动作按钮栏',      self.toggle_subtitle_action_bar),
            ('底部学习区',          self.toggle_bottom_learning),
            ('学习提示面板',        self.toggle_learning_hint_panel),
            ('播放区文本面板',      self.toggle_player_text_group),
            ('左侧工作区',          self.toggle_left_workspace),
        ]

        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (text, func) in enumerate(items):
            btn = QPushButton(text)
            btn.setMinimumHeight(48)
            btn.setStyleSheet('font-size: 15px; padding: 8px;')
            btn.clicked.connect(func)
            row = i // 2
            col = i % 2
            grid.addWidget(btn, row, col)

        lay.addLayout(grid)
        lay.addStretch()

        close_btn = QDialogButtonBox(QDialogButtonBox.Close)
        close_btn.rejected.connect(dialog.reject)
        lay.addWidget(close_btn)

        dialog.exec()

    def open_local_font_settings(self, section='play_options'):
        targets = self._font_section_targets(section)
        if not targets:
            QMessageBox.information(self, '字体设置', '当前区域暂时没有可设置的控件。')
            return

        current_info = (getattr(self, 'local_font_settings', {}) or {}).get(section, {}) if hasattr(self, 'local_font_settings') else {}
        current = targets[0].font() if targets else self.font()

        if isinstance(current_info, dict) and current_info.get('family'):
            current = QFont(current_info.get('family') or current.family())
            try:
                pt = float(current_info.get('pointSize') or 0)
                if pt > 0:
                    current.setPointSizeF(pt)
            except Exception:
                pass
            current.setBold(bool(current_info.get('bold', False)))
            current.setItalic(bool(current_info.get('italic', False)))

        if section == 'all_widgets':
            msg = QMessageBox(self)
            msg.setWindowTitle('全局字体 / 颜色')
            msg.setText('选择全局统一字体 / 颜色的操作：')
            set_btn = msg.addButton('选择字体 / 颜色', QMessageBox.AcceptRole)
            clear_btn = msg.addButton('无（重置全局统一）', QMessageBox.DestructiveRole)
            cancel_btn = msg.addButton('取消', QMessageBox.RejectRole)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == clear_btn:
                self.local_font_settings = getattr(self, 'local_font_settings', {}) or {}
                self.local_font_settings.pop('all_widgets', None)
                self.settings['local_font_settings'] = self.local_font_settings
                self._clear_all_widgets_font_override()
                self.apply_local_font_settings_to_widgets()
                self.save_all_settings(silent=True)
                QMessageBox.information(self, '字体设置', '已清除全局统一字体 / 颜色，恢复为非统一模式。')
                return
            if clicked in (cancel_btn, None) or clicked != set_btn:
                return

        font_result = QFontDialog.getFont(current, self, self._font_section_title(section))
        font, ok = self._normalize_qfontdialog_result(font_result, current)
        if not ok:
            return

        base_color = QColor((current_info or {}).get('color') or '#000000')
        chosen = QColorDialog.getColor(base_color, self, f"{self._font_section_title(section)}：选择颜色")

        self.local_font_settings = getattr(self, 'local_font_settings', {}) or {}
        info = {
            'family': font.family(),
            'pointSize': font.pointSizeF() if font.pointSizeF() > 0 else font.pointSize(),
            'bold': font.bold(),
            'italic': font.italic(),
        }
        if chosen.isValid():
            info['color'] = chosen.name()

        self.local_font_settings[section] = info
        self.settings['local_font_settings'] = self.local_font_settings
        self.apply_local_font_settings_to_widgets()
        self.schedule_settings_autosave()

    def apply_local_font_settings_to_widgets(self):
        cfg = getattr(self, 'local_font_settings', {}) or {}
        for section, info in cfg.items():
            targets = self._font_section_targets(section)
            if not targets or not isinstance(info, dict):
                continue
            font = QFont(info.get('family') or self.font().family())
            try:
                pt = float(info.get('pointSize') or 0)
                if pt > 0:
                    font.setPointSizeF(pt)
            except Exception:
                pass
            font.setBold(bool(info.get('bold', False)))
            font.setItalic(bool(info.get('italic', False)))
            color = (info.get('color') or '').strip()
            for w in targets:
                try:
                    w.setFont(font)
                except Exception:
                    pass
                try:
                    self._apply_style_marker(w, f'FONT_{section.upper()}', f'color: {color};' if color else '')
                except Exception:
                    pass
        try:
            self.apply_subtitle_style_settings()
        except Exception:
            pass

    def prompt_custom_ui_scale(self):
        current = normalize_ui_scale_text(self.ui_scale_combo.currentText() if hasattr(self, 'ui_scale_combo') else self.settings.get('ui_scale_percent', '100%'))
        m = re.match(r'^([0-9]{1,3})%$', current)
        value = int(m.group(1)) if m else 100
        value, ok = QInputDialog.getInt(self, '自定义缩放比例', '输入缩放百分比（40-300）：', value, 40, 300, 1)
        if ok and hasattr(self, 'ui_scale_combo'):
            self.ui_scale_combo.setCurrentText(f'{value}%')
            self.schedule_settings_autosave()

    def default_subtitle_style(self) -> dict:
        return {
            'family': 'Microsoft YaHei',
            'en_size': 18,
            'zh_size': 16,
            'en_color': '#f7f7f7',
            'zh_color': '#d8e6ff',
            'backdrop_color': '#101218',
            'backdrop_opacity': 72,
            'shadow_color': '#000000',
            'shadow_blur': 24,
            'shadow_offset': 2,
            'glow_color': '#000000',
            'glow_blur': 8,
        }


    def default_subtitle_style(self) -> dict:
        return {
            'family': 'Microsoft YaHei',
            'en_size': 20,
            'zh_size': 18,
            'en_color': '#ffffff',
            'zh_color': '#d8e6ff',
            'backdrop_color': '#101218',
            'backdrop_opacity': 75,
            'shadow_color': '#000000',
            'shadow_blur': 25,
            'shadow_offset': 2,
            'glow_color': '#000000',
            'glow_blur': 10,
        }

    def get_en_subtitle_style(self) -> dict:
        """原生英文字幕样式"""
        style = self.default_subtitle_style()
        saved = self.settings.get('en_subtitle_style', {}) or {}
        if isinstance(saved, dict):
            style.update(saved)
        return style

    def get_zh_subtitle_style(self) -> dict:
        """翻译中文字幕样式"""
        style = self.default_subtitle_style()
        saved = self.settings.get('zh_subtitle_style', {}) or {}
        if isinstance(saved, dict):
            style.update(saved)
        return style

    def open_subtitle_style_settings(self):
        """分离设置：原生英文字幕 和 翻译中文字幕"""
        dialog = QDialog(self)
        dialog.setWindowTitle("字幕样式设置（英文字幕 / 中文字幕 分离）")
        dialog.resize(1100, 680)
        root = QVBoxLayout(dialog)

        # 英文字幕设置
        en_box = QGroupBox("原生英文字幕样式")
        en_lay = QFormLayout(en_box)
        en_style = self.get_en_subtitle_style()

        en_font = QFont(en_style.get('family', 'Microsoft YaHei'))
        en_font.setPointSize(int(en_style.get('en_size', 20)))
        en_font_btn = QPushButton("选择英文字体")
        en_font_btn.clicked.connect(lambda: self._choose_sub_font(en_font, en_style, 'en_size', "英文字幕字体"))

        en_color_btn = QPushButton("英文字幕颜色")
        en_color_btn.clicked.connect(lambda: self._choose_sub_color(en_style, 'en_color', "英文字幕颜色"))

        en_shadow_btn = QPushButton("阴影 / 发光设置")
        en_shadow_btn.clicked.connect(lambda: self._choose_sub_effect(en_style, "英文字幕"))

        en_lay.addRow("字体", en_font_btn)
        en_lay.addRow("颜色", en_color_btn)
        en_lay.addRow("阴影/发光", en_shadow_btn)

        root.addWidget(en_box)

        # 中文字幕设置
        zh_box = QGroupBox("翻译中文字幕样式")
        zh_lay = QFormLayout(zh_box)
        zh_style = self.get_zh_subtitle_style()

        zh_font = QFont(zh_style.get('family', 'Microsoft YaHei'))
        zh_font.setPointSize(int(zh_style.get('zh_size', 18)))
        zh_font_btn = QPushButton("选择中文字体")
        zh_font_btn.clicked.connect(lambda: self._choose_sub_font(zh_font, zh_style, 'zh_size', "中文字幕字体"))

        zh_color_btn = QPushButton("中文字幕颜色")
        zh_color_btn.clicked.connect(lambda: self._choose_sub_color(zh_style, 'zh_color', "中文字幕颜色"))

        zh_shadow_btn = QPushButton("阴影 / 发光设置")
        zh_shadow_btn.clicked.connect(lambda: self._choose_sub_effect(zh_style, "中文字幕"))

        zh_lay.addRow("字体", zh_font_btn)
        zh_lay.addRow("颜色", zh_color_btn)
        zh_lay.addRow("阴影/发光", zh_shadow_btn)

        root.addWidget(zh_box)

        # 幕布（背景）
        backdrop_box = QGroupBox("幕布背景（共同）")
        backdrop_lay = QFormLayout(backdrop_box)
        backdrop_color_btn = QPushButton("幕布颜色")
        backdrop_color_btn.clicked.connect(lambda: self._choose_sub_color(en_style, 'backdrop_color', "幕布颜色"))
        opacity_spin = QSpinBox()
        opacity_spin.setRange(0, 100)
        opacity_spin.setValue(int(en_style.get('backdrop_opacity', 75)))
        backdrop_lay.addRow("幕布颜色", backdrop_color_btn)
        backdrop_lay.addRow("透明度 (%)", opacity_spin)
        root.addWidget(backdrop_box)

        # 保存按钮
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(lambda: (self._save_separate_subtitle_style(en_style, zh_style, opacity_spin.value()), dialog.accept()))
        btns.rejected.connect(dialog.reject)
        root.addWidget(btns)

        dialog.exec()

    def _choose_sub_font(self, font_obj, style_dict, size_key, title):
        base_font = font_obj if isinstance(font_obj, QFont) else QFont(style_dict.get('family', 'Microsoft YaHei'))
        font_result = QFontDialog.getFont(base_font, self, title)
        chosen_font, ok = self._normalize_qfontdialog_result(font_result, base_font)
        if ok:
            style_dict['family'] = chosen_font.family()
            if chosen_font.pointSize() > 0:
                style_dict[size_key] = chosen_font.pointSize()
            if isinstance(font_obj, QFont):
                font_obj.setFamily(chosen_font.family())
                if chosen_font.pointSize() > 0:
                    font_obj.setPointSize(chosen_font.pointSize())
            return chosen_font
        return font_obj

    def _choose_sub_color(self, style_dict, key, title):
        current = QColor(style_dict.get(key, '#ffffff'))
        chosen = QColorDialog.getColor(current, self, title)
        if chosen.isValid():
            style_dict[key] = chosen.name()

    def _choose_sub_effect(self, style_dict, title):
        # 简单实现：弹出输入框设置阴影和发光参数
        blur, ok = QInputDialog.getInt(self, f"{title} 阴影强度", "阴影模糊半径 (0-80):", int(style_dict.get('shadow_blur', 25)), 0, 80)
        if ok:
            style_dict['shadow_blur'] = blur
        offset, ok = QInputDialog.getInt(self, f"{title} 阴影偏移", "阴影偏移量 (0-20):", int(style_dict.get('shadow_offset', 2)), 0, 20)
        if ok:
            style_dict['shadow_offset'] = offset
        glow, ok = QInputDialog.getInt(self, f"{title} 发光强度", "发光模糊半径 (0-60):", int(style_dict.get('glow_blur', 10)), 0, 60)
        if ok:
            style_dict['glow_blur'] = glow

    def _save_separate_subtitle_style(self, en_style, zh_style, opacity):
        en_style = dict(en_style or {})
        zh_style = dict(zh_style or {})
        backdrop_color = en_style.get('backdrop_color') or zh_style.get('backdrop_color') or '#101218'
        opacity = int(opacity or 0)
        en_style['backdrop_color'] = backdrop_color
        zh_style['backdrop_color'] = backdrop_color
        en_style['backdrop_opacity'] = opacity
        zh_style['backdrop_opacity'] = opacity
        self.settings['en_subtitle_style'] = en_style
        self.settings['zh_subtitle_style'] = zh_style
        self.settings['subtitle_backdrop_opacity'] = opacity
        self.apply_subtitle_style_settings()
        self.save_all_settings(silent=True)
        QMessageBox.information(self, "保存成功", "英文字幕和中文字幕样式已分别保存！")

    def _color_to_rgba(self, color_hex: str, opacity_percent: int = 100) -> str:
        color = QColor(color_hex or '#000000')
        alpha = max(0, min(255, int(round(255 * max(0, min(100, int(opacity_percent))) / 100.0))))
        return f'rgba({color.red()}, {color.green()}, {color.blue()}, {alpha})'

    def _apply_text_effect(self, widget, color_hex: str, blur: int = 0, offset: int = 0):
        if widget is None:
            return
        blur = max(0, int(blur or 0))
        offset = int(offset or 0)
        if blur <= 0:
            widget.setGraphicsEffect(None)
            return
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setColor(QColor(color_hex or '#000000'))
        effect.setOffset(offset, offset)
        widget.setGraphicsEffect(effect)

    def apply_subtitle_style_settings(self):
        en_style = self.get_en_subtitle_style()
        zh_style = self.get_zh_subtitle_style()
        opacity = int(self.settings.get('subtitle_backdrop_opacity', 75))

        curtain = self._color_to_rgba(en_style.get('backdrop_color', '#101218'), opacity)

        # 原生英文字幕
        if hasattr(self, 'subtitle_browser'):
            font = QFont(en_style.get('family', 'Microsoft YaHei'))
            font.setPointSize(int(en_style.get('en_size', 20)))
            self.subtitle_browser.setFont(font)
            self.subtitle_browser.setStyleSheet(f"color: {en_style.get('en_color', '#ffffff')}; background: {curtain}; border-radius: 10px; padding: 8px;")
            self._apply_text_effect(self.subtitle_browser, en_style.get('shadow_color', '#000000'), int(en_style.get('shadow_blur', 25)), int(en_style.get('shadow_offset', 2)))

        # 翻译中文字幕
        if hasattr(self, 'translation_browser'):
            font = QFont(zh_style.get('family', 'Microsoft YaHei'))
            font.setPointSize(int(zh_style.get('zh_size', 18)))
            self.translation_browser.setFont(font)
            self.translation_browser.setStyleSheet(f"color: {zh_style.get('zh_color', '#d8e6ff')}; background: {curtain}; border-radius: 10px; padding: 8px;")
            self._apply_text_effect(self.translation_browser, zh_style.get('shadow_color', '#000000'), int(zh_style.get('shadow_blur', 25)), int(zh_style.get('shadow_offset', 2)))

        # 浮动字幕（保持兼容）
        if hasattr(self, 'floating_subtitle'):
            self.floating_subtitle.apply_style(en_style)   # 暂时共用英文字幕样式，可后续分离

    def _subtitle_line_count(self, text: str) -> int:
        raw = (text or '').replace('\r\n', '\n').strip()
        if not raw:
            return 1
        lines = [ln for ln in raw.split('\n') if ln.strip()]
        if not lines:
            return 1
        return max(1, min(3, len(lines)))

    def _set_text_box_line_height(self, widget, text: str, min_lines: int = 1, max_lines: int = 3):
        if widget is None:
            return
        lines = max(min_lines, min(max_lines, self._subtitle_line_count(text)))
        fm = widget.fontMetrics()
        base = fm.lineSpacing() * lines + 20
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            base += 12
        widget.setMinimumHeight(base)
        widget.setMaximumHeight(base)
        widget.setFixedHeight(base)

    def adjust_learning_area_widgets(self, en: str = '', zh: str = ''):
        if hasattr(self, 'subtitle_browser'):
            self._set_text_box_line_height(self.subtitle_browser, en, 1, 3)
        if hasattr(self, 'translation_browser'):
            self._set_text_box_line_height(self.translation_browser, zh or '', 1, 3)
        if hasattr(self, 'learning_panel'):
            hint_text = self.learning_panel.toPlainText() if hasattr(self.learning_panel, 'toPlainText') else ''
            self._set_text_box_line_height(self.learning_panel, hint_text, 1, 3)

    def toggle_learning_hint_panel(self):
        if hasattr(self, 'learning_panel'):
            visible = not self.learning_panel.isVisible()
            self.learning_panel.setVisible(visible)
            if hasattr(self, 'learning_hint_label'):
                self.learning_hint_label.setVisible(visible)
            self.settings['learning_panel_visible'] = visible
            self.adjust_learning_area_widgets(self.subtitle_browser.toPlainText() if hasattr(self, 'subtitle_browser') else '', self.translation_browser.toPlainText() if hasattr(self, 'translation_browser') else '')
            self.schedule_settings_autosave()

    def sync_learning_height_slider_from_splitter(self, *_args):
        if not hasattr(self, 'learning_height_slider') or not hasattr(self, 'right_splitter') or self.right_splitter.count() < 2:
            return
        sizes = self.right_splitter.sizes()
        if len(sizes) < 2:
            return
        value = int(sizes[1])
        self.learning_height_slider.blockSignals(True)
        self.learning_height_slider.setValue(max(self.learning_height_slider.minimum(), min(self.learning_height_slider.maximum(), value)))
        self.learning_height_slider.blockSignals(False)

    def on_learning_height_slider_changed(self, value: int):
        if not hasattr(self, 'right_splitter') or self.right_splitter.count() < 2:
            return
        sizes = self.right_splitter.sizes()
        total = sum(sizes) if sizes else self.right_splitter.height()
        bottom = max(240, min(int(value), max(240, total - 200)))  # 提高最小高度
        top = max(200, total - bottom)
        self.right_splitter.setSizes([top, bottom])
        self.settings['learning_zone_height'] = bottom
        self.schedule_settings_autosave()
        QTimer.singleShot(80, self.refresh_current_subtitle_displays)  # 刷新字幕位置

    def _register_shortcuts(self):
        for sc in getattr(self, "_shortcut_objects", []):
            try:
                sc.setEnabled(False)
                sc.deleteLater()
            except Exception:
                pass
        self._shortcut_objects = []
        shortcut_map = self.settings.get("shortcut_map", {
            "sample_prev": "Up",
            "sample_next": "Down",
            "sentence_prev": "Left",
            "sentence_next": "Right",
            "toggle_play": "Space",
            "focus_search": "Ctrl+F",
            "restore_layout": "Ctrl+0",
            "toggle_fullscreen": "F11",
            "cycle_theme_next": "Ctrl+T",
            "cycle_theme_prev": "Ctrl+Shift+T",
            "cycle_palette_next": "Ctrl+P",
            "cycle_palette_prev": "Ctrl+Shift+P",
            "subtitle_single": "Ctrl+1",
            "subtitle_dual": "Ctrl+2",
            "subtitle_none": "Ctrl+3",
            "take_screenshot": "Ctrl+Shift+S",
            "record_placeholder": "Ctrl+R",
            "toggle_bottom_learning": "Ctrl+L",
            "toggle_top_bar": "Ctrl+H",
            "toggle_learning_hint": "Ctrl+Shift+H",
            "toggle_search_results": "Ctrl+Shift+F",
            "toggle_playlist_panel": "Ctrl+Shift+P",
            "toggle_progress_bar": "Ctrl+Shift+J",
            "toggle_control_buttons": "Ctrl+Shift+K",
            "toggle_learning_actions": "Ctrl+Shift+A",
            "toggle_text_panel": "Ctrl+Shift+T",
            "shortcut_settings_panel": "Ctrl+Alt+K",
        })
        bindings = [
            (shortcut_map.get("sample_prev", "Up"), lambda: self.navigate_samples(-1)),
            (shortcut_map.get("sample_next", "Down"), lambda: self.navigate_samples(1)),
            (shortcut_map.get("sentence_prev", "Left"), lambda: self.jump_sentence(-1)),
            (shortcut_map.get("sentence_next", "Right"), lambda: self.jump_sentence(1)),
            (shortcut_map.get("toggle_play", "Space"), self.toggle_play_pause),
            (shortcut_map.get("focus_search", "Ctrl+F"), lambda: self.local_keyword_edit.setFocus()),
            (shortcut_map.get("restore_layout", "Ctrl+0"), self.restore_layouts),
            (shortcut_map.get("toggle_fullscreen", "F11"), self.toggle_fullscreen_shortcut),
            (shortcut_map.get("cycle_theme_next", "Ctrl+T"), self.cycle_theme_next),
            (shortcut_map.get("cycle_theme_prev", "Ctrl+Shift+T"), self.cycle_theme_prev),
            (shortcut_map.get("cycle_palette_next", "Ctrl+P"), self.cycle_palette_next),
            (shortcut_map.get("cycle_palette_prev", "Ctrl+Shift+P"), self.cycle_palette_prev),
            (shortcut_map.get("subtitle_single", "Ctrl+1"), lambda: self.set_subtitle_display_mode("single")),
            (shortcut_map.get("subtitle_dual", "Ctrl+2"), lambda: self.set_subtitle_display_mode("dual")),
            (shortcut_map.get("subtitle_none", "Ctrl+3"), lambda: self.set_subtitle_display_mode("none")),
            (shortcut_map.get("take_screenshot", "Ctrl+Shift+S"), self.take_screenshot),
            (shortcut_map.get("record_placeholder", "Ctrl+R"), self.show_record_placeholder),
            (shortcut_map.get("toggle_bottom_learning", "Ctrl+L"), self.toggle_bottom_learning),
            (shortcut_map.get("toggle_top_bar", "Ctrl+H"), self.toggle_top_toolbar),
            (shortcut_map.get("toggle_learning_hint", "Ctrl+Shift+H"), self.toggle_learning_hint_panel),
            (shortcut_map.get("toggle_search_results", "Ctrl+Shift+F"), lambda: self.toggle_group_visibility("local_search_group")),
            (shortcut_map.get("toggle_playlist_panel", "Ctrl+Shift+P"), lambda: self.toggle_group_visibility("playlist_group")),
            (shortcut_map.get("toggle_progress_bar", "Ctrl+Shift+J"), self.toggle_progress_toolbar),
            (shortcut_map.get("toggle_control_buttons", "Ctrl+Shift+K"), self.toggle_control_button_bar),
            (shortcut_map.get("toggle_learning_actions", "Ctrl+Shift+A"), self.toggle_subtitle_action_bar),
            (shortcut_map.get("toggle_text_panel", "Ctrl+Shift+T"), self.toggle_player_text_group),
            (shortcut_map.get("shortcut_settings_panel", "Ctrl+Alt+K"), self.show_shortcut_settings),
        ]
        for seq, callback in bindings:
            if not seq:
                continue
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(callback)
            self._shortcut_objects.append(sc)


    def _notes_output_dir(self) -> Path:
        raw = (self.settings.get("notes_output_dir", str(DATA_DIR / "notes")) or str(DATA_DIR / "notes")).strip()
        p = Path(raw)
        safe_mkdir(p)
        return p

    def _vocab_output_dir(self) -> Path:
        raw = (self.settings.get("vocab_output_dir", str(DATA_DIR / "vocab")) or str(DATA_DIR / "vocab")).strip()
        p = Path(raw)
        safe_mkdir(p)
        return p

    def _notes_store_path(self) -> Path:
        return self._notes_output_dir() / "学习笔记.json"

    def _vocab_store_path(self) -> Path:
        return self._vocab_output_dir() / "生词本.json"

    def _load_persistent_stores(self):
        try:
            np = self._notes_store_path()
            if np.exists():
                raw = json.loads(np.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, dict) and item.get('uid'):
                            self.notes_records[item['uid']] = item
                            self.notes_store[item['uid']] = item.get('note', '')
        except Exception:
            pass
        try:
            vp = self._vocab_store_path()
            if vp.exists():
                raw = json.loads(vp.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    store = []
                    for item in raw:
                        if isinstance(item, dict):
                            try:
                                store.append(VocabularyEntry(**item))
                            except Exception:
                                pass
                    self.vocab_store = store
        except Exception:
            self.vocab_store = []

    def _save_notes_store(self):
        self._notes_store_path().write_text(json.dumps(list(self.notes_records.values()), ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_vocab_store(self):
        self._vocab_store_path().write_text(json.dumps([asdict(x) for x in self.vocab_store], ensure_ascii=False, indent=2), encoding="utf-8")

    def _sync_item_notes_from_store(self, items: List[LearningItem]):
        for item in items:
            if item.uid in self.notes_store:
                item.note = self.notes_store.get(item.uid, "")

    def _load_ai_targets(self) -> List[AITarget]:
        raw = self.settings.get("ai_targets", [])
        targets = []
        if isinstance(raw, list):
            for item in raw:
                try:
                    targets.append(AITarget(**item))
                except Exception:
                    pass
        if not targets:
            targets = [AITarget(name="默认 AI", endpoint="", method="POST", headers_json="{}", enabled=True)]
        return targets

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.local_tab = QWidget()
        self.online_tab = QWidget()
        self.ai_tab = QWidget()
        self.notes_tab = QWidget()
        self.vocab_tab = QWidget()
        self.download_tab = QWidget()
        self.batch_srt_tab = QWidget()
        self.dict_tab = QWidget()
        self.config_tab = QWidget()

        self.tabs.addTab(self.local_tab, "本地模式")
        self.tabs.addTab(self.online_tab, "联网模式")
        self.tabs.addTab(self.ai_tab, "AI互动")
        self.tabs.addTab(self.notes_tab, "学习笔记")
        self.tabs.addTab(self.vocab_tab, "生词本")
        self.tabs.addTab(self.download_tab, "批量下载")
        self.tabs.addTab(self.batch_srt_tab, "批量转SRT")
        self.tabs.addTab(self.dict_tab, "查词来源")
        self.tabs.addTab(self.config_tab, "配置中心")

        self._build_local_tab()
        self._build_online_tab()
        self._build_ai_tab()
        self._build_notes_tab()
        self._build_vocab_tab()
        self._build_download_tab()
        self._build_batch_srt_tab()
        self._build_dict_tab()
        self._build_config_tab()

    # ---------- local tab ----------
    def _build_local_tab(self):
        outer = QVBoxLayout(self.local_tab)

        title_row = QHBoxLayout()
        title = QLabel("统一学习工作台 · 本地模式")
        title.setStyleSheet("font-size:22px; font-weight:800; padding:4px;")
        subtitle = QLabel("搜索结果负责筛选与分发；播放列表负责播放方式；视频区只做学习载体。")
        title_row.addWidget(title)
        title_row.addWidget(subtitle)
        title_row.addStretch()
        self.ui_scale_combo = QComboBox()
        self.ui_scale_combo.setEditable(True)
        self.ui_scale_combo.addItems(["60%", "70%", "80%", "90%", "100%", "110%", "120%", "130%", "150%", "180%", "200%"])
        self.ui_scale_combo.setCurrentText(normalize_ui_scale_text(self.settings.get("ui_scale_percent", "100%")))
        self.ui_scale_combo.setMaximumWidth(90)
        self.save_settings_btn = QPushButton("保存设置")
        self.settings_btn = QPushButton("设置 ▾")
        title_row.addWidget(QLabel("缩放"))
        title_row.addWidget(self.ui_scale_combo)
        title_row.addWidget(self.save_settings_btn)
        title_row.addWidget(self.settings_btn)
        outer.addLayout(title_row)

        source_box = QGroupBox("本地数据源")
        source_l = QVBoxLayout(source_box)
        path_row = QHBoxLayout()
        self.add_root_btn = QPushButton("添加路径")
        self.remove_root_btn = QPushButton("删除路径")
        self.clear_root_btn = QPushButton("清空路径")
        self.scan_btn = QPushButton("递归扫描字幕库")
        for b in [self.add_root_btn, self.remove_root_btn, self.clear_root_btn, self.scan_btn]:
            path_row.addWidget(b)
        path_row.addStretch()
        source_l.addLayout(path_row)
        self.root_list = QListWidget()
        self.root_list.setMaximumHeight(88)
        source_l.addWidget(self.root_list)
        self.path_info = QLabel("尚未扫描本地字幕库。")
        source_l.addWidget(self.path_info)
        self.source_toggle_btn = QPushButton("折叠数据源")
        self.source_toggle_btn.setCheckable(True)
        path_row.addWidget(self.source_toggle_btn)
        self.local_outer_splitter = QSplitter(Qt.Vertical)
        self.local_outer_splitter.setChildrenCollapsible(False)
        self.local_outer_splitter.setHandleWidth(10)
        self.local_outer_splitter.addWidget(source_box)

        self.local_splitter = QSplitter(Qt.Horizontal)
        self.local_splitter.setChildrenCollapsible(True)
        self.local_splitter.setHandleWidth(14)
        self.local_splitter.setOpaqueResize(False)
        self.local_outer_splitter.addWidget(self.local_splitter)
        outer.addWidget(self.local_outer_splitter, 1)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left.setMinimumWidth(0)
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setChildrenCollapsible(True)
        self.left_splitter.setHandleWidth(10)
        left_l.addWidget(self.left_splitter)
        self.local_splitter.addWidget(left)
        if self.local_splitter.count() >= 2:
            try:
                self.local_splitter.setCollapsible(0, True)
                self.local_splitter.setCollapsible(1, False)
            except Exception:
                pass

        search_box = QGroupBox("搜索结果区（信息筛选 / 动作分发）")
        search_box.setMinimumHeight(0)
        search_l = QVBoxLayout(search_box)
        form = QGridLayout()
        self.local_keyword_edit = QLineEdit(); self.local_keyword_edit.setPlaceholderText("输入关键词 / 句子片段"); self.local_keyword_edit.setMinimumWidth(280)
        self.local_path_filter_edit = QLineEdit(); self.local_path_filter_edit.setPlaceholderText("路径过滤（可选）"); self.local_path_filter_edit.setMinimumWidth(260)
        self.local_search_btn = QPushButton("搜索")
        form.addWidget(QLabel("关键词"), 0, 0); form.addWidget(self.local_keyword_edit, 0, 1, 1, 3)
        form.addWidget(QLabel("路径过滤"), 1, 0); form.addWidget(self.local_path_filter_edit, 1, 1, 1, 2); form.addWidget(self.local_search_btn, 1, 3)
        search_l.addLayout(form)

        btns = QHBoxLayout()
        self.local_result_select_all_btn = QPushButton("全选")
        self.local_result_invert_btn = QPushButton("反选")
        self.local_result_clear_btn = QPushButton("清空")
        self.local_result_sort_combo = QComboBox(); self.local_result_sort_combo.addItems(["文件名", "时间", "匹配度"])
        self.local_result_limit_edit = QLineEdit(); self.local_result_limit_edit.setPlaceholderText("显示条数 空=全部"); self.local_result_limit_edit.setMinimumWidth(140)
        self.local_result_limit_edit.setMaximumWidth(160)
        self.local_add_playlist_btn = QPushButton("加入播放列表")
        self.local_copy_btn = QPushButton("复制选中项")
        self.local_note_btn = QPushButton("加入笔记")
        self.local_ai_btn = QPushButton("发送AI")
        self.local_search_options_btn = QPushButton("搜索选项 ▾")
        for w in [self.local_result_select_all_btn, self.local_result_invert_btn, self.local_result_clear_btn, QLabel("排序"), self.local_result_sort_combo, self.local_result_limit_edit, self.local_add_playlist_btn, self.local_search_options_btn]:
            btns.addWidget(w)
        btns.addStretch()
        search_l.addLayout(btns)
        self.local_result_table = self._create_item_table(show_show=True)
        self.local_search_options_btn.setMenu(self._build_search_menu())
        self.local_search_group = search_box
        self.search_group = search_box
        self.search_result_table = self.local_result_table
        self.search_edit = self.local_keyword_edit
        self.search_sort_combo = self.local_result_sort_combo
        self.search_limit_spin = self.local_result_limit_edit
        self.local_result_status = QLabel("搜索结果：0 条")
        self.local_result_status.setObjectName("localResultStatusLabel")
        self.search_status_label = self.local_result_status
        search_l.addWidget(self.local_result_table, 1)
        search_l.addWidget(self.local_result_status)
        self.apply_search_column_visibility()
        self.left_splitter.addWidget(search_box)
        if self.left_splitter.count() >= 2:
            try:
                self.left_splitter.setCollapsible(0, True)
                self.left_splitter.setCollapsible(1, True)
            except Exception:
                pass

        playlist_box = QGroupBox("播放列表区（学习集合 / 播放方式）")
        playlist_box.setMinimumHeight(0)
        playlist_l = QVBoxLayout(playlist_box)
        pbtns = QHBoxLayout()
        self.playlist_select_all_btn = QPushButton("全选")
        self.playlist_invert_btn = QPushButton("反选")
        self.playlist_clear_btn = QPushButton("清空")
        self.play_slice_btn = QPushButton("播放切片")
        self.play_video_btn = QPushButton("播放视频")
        self.full_view_btn = QPushButton("全屏观影")
        self.playlist_options_btn = QPushButton("播放列表选项 ▾")
        for w in [self.playlist_select_all_btn, self.playlist_invert_btn, self.playlist_clear_btn, self.play_slice_btn, self.play_video_btn, self.full_view_btn, self.playlist_options_btn]:
            pbtns.addWidget(w)
        pbtns.addStretch()
        playlist_l.addLayout(pbtns)
        self.playlist_table = self._create_item_table(show_show=True)
        self.playlist_options_btn.setMenu(self._build_playlist_menu())
        self.playlist_group = playlist_box
        self.playlist_play_btn = self.play_slice_btn
        playlist_l.addWidget(self.playlist_table, 1)
        self.left_splitter.addWidget(playlist_box)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right.setMinimumWidth(240)
        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.setChildrenCollapsible(False)
        self.right_splitter.setHandleWidth(10)
        right_l.addWidget(self.right_splitter)
        self.local_splitter.addWidget(right)
        self.local_splitter.setStretchFactor(0, 0)
        self.local_splitter.setStretchFactor(1, 1)
        self.local_splitter.setSizes([520, 1320])

        video_box = QGroupBox("播放区")
        self.player_group = video_box
        video_l = QVBoxLayout(video_box)
        topbar = QHBoxLayout()
        self.top_toolbar = QWidget()
        self.video_topbar_layout = topbar
        self.theme_combo = QComboBox(); self.theme_combo.addItems(list_theme_names())
        self.palette_combo = QComboBox(); self.palette_combo.addItems(list_palette_names())
        self.loop_mode_combo = QComboBox(); self.loop_mode_combo.addItems(["single", "list", "all"])
        self.loop_count_spin = QSpinBox(); self.loop_count_spin.setRange(1, 999); self.loop_count_spin.setValue(1); self.loop_count_spin.setMinimumWidth(112); self.loop_count_spin.setMaximumWidth(140)
        self.play_speed_combo = QComboBox(); self.play_speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.play_options_btn = QPushButton("播放选项 ▾")
        self.play_options_btn.setMenu(self._build_play_menu())
        self.left_collapse_btn = QPushButton("收起左侧")
        self.fullscreen_btn = QPushButton("全屏")
        self.restore_layout_btn = QPushButton("恢复布局")
        self.play_status_label = QLabel("当前策略：尚未开始播放")
        for w in [QLabel("主题"), self.theme_combo, QLabel("配色"), self.palette_combo, QLabel("循环模式"), self.loop_mode_combo, QLabel("次数"), self.loop_count_spin, QLabel("速度"), self.play_speed_combo, self.play_options_btn, self.left_collapse_btn, self.fullscreen_btn, self.restore_layout_btn, self.play_status_label]:
            topbar.addWidget(w)
        topbar.addStretch()
        video_l.addLayout(topbar)
        self.top_toolbar_layout = topbar

        self.video_widget = EscapableVideoWidget()
        self.video_widget.setMinimumHeight(380)
        self.video_widget.escapePressed.connect(self.exit_fullscreen)
        self.player.setVideoOutput(self.video_widget)
        video_l.addWidget(self.video_widget, 1)
        self.floating_subtitle = FloatingSubtitleWidget(self.video_widget)
        self.floating_subtitle.hide()
        self.floating_subtitle.raise_()

        progress = QHBoxLayout()
        self.pos_label = QLabel("00:00")
        self.player_slider = ClickableSlider(Qt.Horizontal); self.player_slider.setRange(0, 0)
        self.dur_label = QLabel("00:00")
        progress.addWidget(self.pos_label)
        progress.addWidget(self.player_slider, 1)
        progress.addWidget(self.dur_label)
        video_l.addLayout(progress)
        self.progress_layout = progress
        self.right_splitter.addWidget(video_box)

        control_box = QGroupBox("播放控制 / 学习模式")
        self.learning_group = control_box
        control_wrap = QHBoxLayout(control_box)
        control_l = QVBoxLayout()
        control_wrap.addLayout(control_l, 1)
        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("上一个")
        self.play_pause_btn = QPushButton("播放/暂停")
        self.next_btn = QPushButton("下一个")
        self.clip_btn = QPushButton("剪辑工作台")
        self.learning_btn = QPushButton("学习模式")
        self.view_mode_combo = QComboBox(); self.view_mode_combo.addItems(["听译模式", "沉浸式播放", "AI搜索模式"])
        for w in [self.prev_btn, self.play_pause_btn, self.next_btn, self.clip_btn, self.learning_btn, QLabel("观看模式"), self.view_mode_combo]:
            btn_row.addWidget(w)
        btn_row.addStretch()
        control_l.addLayout(btn_row)
        self.control_button_layout = btn_row

        sub_box = QGroupBox("字幕 / 翻译 / 学习动作")
        sub_l = QVBoxLayout(sub_box)
        self.sub_box = sub_box
        sub_btns = QHBoxLayout()
        self.copy_line_btn = QPushButton("复制台词")
        self.copy_trans_btn = QPushButton("复制翻译")
        self.lookup_btn = QPushButton("查词")
        self.vocab_btn = QPushButton("加入生词本")
        self.note_btn = QPushButton("加入笔记")
        for w in [self.copy_line_btn, self.copy_trans_btn, self.lookup_btn, self.vocab_btn, self.note_btn]:
            sub_btns.addWidget(w)
        sub_btns.addStretch()
        sub_l.addLayout(sub_btns)
        self.subtitle_action_layout = sub_btns
        self.player_text_group = sub_box
        self.subtitle_label = QLabel("当前台词")
        self.translation_label = QLabel("翻译 / 备注")
        self.learning_hint_label = QLabel("学习提示")
        self.subtitle_browser = QTextEdit(); self.subtitle_browser.setReadOnly(True)
        self.subtitle_en_label = self.subtitle_browser
        self.translation_browser = QPlainTextEdit(); self.translation_browser.setReadOnly(True)
        self.subtitle_zh_label = self.translation_browser
        self.learning_panel = QPlainTextEdit(); self.learning_panel.setReadOnly(True)
        self.study_panel = self.learning_panel
        self.learning_panel.setPlainText("学习模式说明：\n- 上下方向键：切换样本\n- 左右方向键：按句子切换\n- 勾选优先参与批量操作，无勾选时退回行选中项。")
        sub_l.addWidget(self.subtitle_label)
        sub_l.addWidget(self.subtitle_browser)
        sub_l.addWidget(self.translation_label)
        sub_l.addWidget(self.translation_browser)
        sub_l.addWidget(self.learning_hint_label)
        sub_l.addWidget(self.learning_panel)
        control_l.addWidget(sub_box, 1)
        self.learning_height_slider = VerticalDragHandle()
        self.learning_height_slider.setRange(220, 900)
        self.learning_height_slider.setValue(360)
        control_wrap.addWidget(self.learning_height_slider)
        self.right_splitter.addWidget(control_box)

        self.settings_btn.setMenu(self._build_global_settings_menu())
        self.restore_layouts()
        self.adjust_learning_area_widgets(self.subtitle_browser.toPlainText(), self.translation_browser.toPlainText())
        self._connect_local_signals()

    def _build_global_settings_menu(self):
        menu = QMenu(self)
        save_act = QAction('保存设置', self)
        save_act.triggered.connect(lambda: self.save_all_settings(silent=False))
        menu.addAction(save_act)
        scale_act = QAction('自定义缩放比例…', self)
        scale_act.triggered.connect(self.prompt_custom_ui_scale)
        menu.addAction(scale_act)
        menu.addSeparator()
        theme_menu = menu.addMenu('主题')
        for n in list_theme_names():
            act = QAction(n, self)
            act.triggered.connect(lambda checked=False, name=n: self.theme_combo.setCurrentText(name))
            theme_menu.addAction(act)
        pal_menu = menu.addMenu('配色')
        for n in list_palette_names():
            act = QAction(n, self)
            act.triggered.connect(lambda checked=False, name=n: self.palette_combo.setCurrentText(name))
            pal_menu.addAction(act)
        menu.addSeparator()
        font_menu = menu.addMenu('字体样式 / 颜色')
        actions = [
            ('四大区域字体总面板', self.open_font_style_control_panel),
            ('文本输入框字体 / 颜色', lambda: self.open_local_font_settings('text_input_options')),
            ('按钮字体 / 颜色', lambda: self.open_local_font_settings('button_options')),
            ('字幕样式', self.open_subtitle_style_settings),
        ]
        for title, cb in actions:
            act = QAction(title, self)
            act.triggered.connect(cb)
            font_menu.addAction(act)
        shortcut_act = QAction('快捷键设置面板', self)
        shortcut_act.triggered.connect(self.show_shortcut_settings)
        menu.addAction(shortcut_act)
        view_menu = menu.addMenu('显示 / 隐藏')
        view_actions = [
            ('数据源区', lambda: self.source_toggle_btn.click() if hasattr(self, 'source_toggle_btn') else None),
            ('搜索结果区', lambda: self.toggle_group_visibility('local_search_group')),
            ('播放列表区', lambda: self.toggle_group_visibility('playlist_group')),
            ('播放区顶部按钮', self.toggle_top_toolbar),
            ('播放区进度栏', self.toggle_progress_toolbar),
            ('播放控制按钮栏', self.toggle_control_button_bar),
            ('学习动作按钮栏', self.toggle_subtitle_action_bar),
            ('台词翻译区', self.toggle_player_text_group),
            ('学习提示', self.toggle_learning_hint_panel),
            ('底部学习区', self.toggle_bottom_learning),
        ]
        for title, cb in view_actions:
            act = QAction(title, self)
            act.triggered.connect(cb)
            view_menu.addAction(act)
        return menu

    def _build_play_menu(self):
        menu = QMenu(self)
        act_short_cfg = QAction("快捷键设置面板", self)
        act_short_cfg.triggered.connect(self.show_shortcut_settings)
        menu.addAction(act_short_cfg)
        act_short = QAction("快捷键提示", self)
        act_short.triggered.connect(self.show_shortcuts)
        menu.addAction(act_short)
        menu.addSeparator()
        for title, cb in [
            ("四大区域字体总面板", self.open_font_style_control_panel),
            ("文本输入框字体 / 颜色", lambda: self.open_local_font_settings("text_input_options")),
            ("按钮字体 / 颜色", lambda: self.open_local_font_settings("button_options")),
            ("字幕样式", self.open_subtitle_style_settings),
            ("自定义缩放比例…", self.prompt_custom_ui_scale),
        ]:
            act = QAction(title, self)
            act.triggered.connect(cb)
            menu.addAction(act)
        menu.addSeparator()
        actions = [
            ("切换浮动字幕", self.toggle_floating_subtitle),
            ("重置浮动字幕位置", self.reset_floating_subtitle_position),
            ("隐藏学习提示", self.toggle_learning_hint_panel),
        ]
        for title, cb in actions:
            act = QAction(title, self)
            act.triggered.connect(cb)
            menu.addAction(act)
        return menu

    def _create_item_table(self, show_show: bool = True) -> ToggleSelectionTable:
        table = ToggleSelectionTable(0, 7 if show_show else 6)
        headers = ["勾", "剧集/来源", "时间", "英文", "中文", "视频/URL", "备注"] if show_show else ["勾", "时间", "英文", "中文", "视频/URL", "备注"]
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return table

    def render_items_to_table(self, table: QTableWidget, items: List[LearningItem], show_show: bool = True):
        self._rendering_tables = True
        table.blockSignals(True)
        table.setRowCount(0)
        rows_to_select = []
        for item in items:
            row = table.rowCount()
            table.insertRow(row)
            values = []
            values.append("☑" if item.checked else "☐")
            if show_show:
                values.append(item.show_name or ("在线结果" if item.source_type == "online" else ""))
            values.append(f"{self.format_seconds(item.start_time)} ~ {self.format_seconds(item.end_time)}")
            values.append((item.en or item.subtitle_text or "")[:180])
            values.append((item.zh or "")[:120])
            values.append(Path(item.video_path).name if item.video_path else (item.video_url or ""))
            values.append((item.note or "")[:120])
            for col, val in enumerate(values):
                q = QTableWidgetItem(val)
                q.setData(Qt.UserRole, item.uid)
                if col == 0:
                    q.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, q)
            if item.selected:
                rows_to_select.append(row)
        table.clearSelection()
        for row in rows_to_select:
            table.selectRow(row)
        table.blockSignals(False)
        self.update_table_playing_highlight(table, items)
        self._rendering_tables = False

    def update_table_playing_highlight(self, table: QTableWidget, items: List[LearningItem]):
        playing = self.state.current_playing_uid
        selected = self.state.current_selected_uid
        for row in range(table.rowCount()):
            uid = table.item(row, 0).data(Qt.UserRole)
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if not item:
                    continue
                if uid == playing:
                    item.setBackground(QColor("#fff1a8"))
                elif uid == selected:
                    item.setBackground(QColor("#e6f3ff"))
                else:
                    item.setBackground(QColor("transparent"))

    def update_all_tables(self):
        self.render_items_to_table(self.local_result_table, self.local_results, True)
        self.render_items_to_table(self.online_result_table, self.online_results, True)
        self.render_items_to_table(self.playlist_table, self.state.playlist, True)
        self.apply_search_column_visibility()
        self.refresh_notes_table()
        self.refresh_vocab_table()

    def get_table_selected_rows(self, table: QTableWidget) -> List[int]:
        if not table.selectionModel():
            return []
        return sorted({idx.row() for idx in table.selectionModel().selectedRows()})

    def on_table_selection_changed(self, table: QTableWidget, items: List[LearningItem], is_playlist: bool):
        if self._rendering_tables:
            return
        selected_rows = self.get_table_selected_rows(table)
        for idx, item in enumerate(items):
            item.selected = idx in selected_rows
        if selected_rows:
            self.state.current_selected_uid = items[selected_rows[0]].uid
        else:
            self.state.current_selected_uid = None
        self.update_table_playing_highlight(self.local_result_table, self.local_results)
        self.update_table_playing_highlight(self.online_result_table, self.online_results)
        self.update_table_playing_highlight(self.playlist_table, self.state.playlist)
        if is_playlist and selected_rows:
            item = items[selected_rows[0]]
            self.append_learning_message(f"当前选中：{item.en or item.subtitle_text}")

    def on_table_cell_clicked(self, table: QTableWidget, items: List[LearningItem], row: int, col: int):
        if self._rendering_tables:
            return
        if 0 <= row < len(items) and col == 0:
            items[row].checked = not items[row].checked
            item = table.item(row, 0)
            if item:
                item.setText("☑" if items[row].checked else "☐")
            self.update_table_playing_highlight(self.local_result_table, self.local_results)
            self.update_table_playing_highlight(self.online_result_table, self.online_results)
            self.update_table_playing_highlight(self.playlist_table, self.state.playlist)

    def set_checked_for_table(self, table: QTableWidget, items: List[LearningItem], value: bool):
        for item in items:
            item.checked = value
        self.update_all_tables()

    def invert_checked_for_table(self, table: QTableWidget, items: List[LearningItem]):
        for item in items:
            item.checked = not item.checked
        self.update_all_tables()

    def resolve_action_items(self, items: List[LearningItem], table: QTableWidget) -> List[LearningItem]:
        checked = [x for x in items if x.checked]
        if checked:
            return checked
        rows = self.get_table_selected_rows(table)
        return [items[r] for r in rows if 0 <= r < len(items)]


    def clear_playlist(self):
        for item in self.state.playlist:
            item.in_playlist = False
            item.checked = False
            item.selected = False
        self.state.playlist = []
        self.state.current_playing = None
        self.update_all_tables()
        self.update_status_banner()

    def add_items_to_playlist(self, items: List[LearningItem]):
        added = 0
        for item in items:
            if not item.in_playlist:
                item.in_playlist = True
                self.state.global_add_counter += 1
                item.added_index = self.state.global_add_counter
                self.state.playlist.append(item)
                added += 1
        self.update_all_tables()
        QMessageBox.information(self, "加入播放列表", f"已加入 {added} 条。")

    def copy_items_text(self, items: List[LearningItem]):
        if not items:
            QMessageBox.information(self, "提示", "没有可复制的对象")
            return
        text = "\n".join(x.en or x.subtitle_text for x in items)
        QApplication.clipboard().setText(text)
        self.append_learning_message(f"已复制 {len(items)} 条内容。")

    def add_note_to_items(self, items: List[LearningItem]):
        if not items:
            QMessageBox.information(self, "提示", "没有可写入备注的对象")
            return
        note, ok = QInputDialog.getMultiLineText(self, "写入备注", "输入备注（短语/台词备注会同步）：")
        if not ok:
            return
        for item in items:
            item.note = note
            self.notes_store[item.uid] = note
            self.notes_records[item.uid] = {
                "uid": item.uid,
                "source": item.show_name or item.source_type,
                "time": self.format_seconds(item.start_time),
                "text": item.en or item.subtitle_text,
                "note": note,
            }
        self._save_notes_store()
        self.update_all_tables()
        self.refresh_notes_table()

    def send_items_to_ai(self, items: List[LearningItem]):
        if not items:
            QMessageBox.information(self, "提示", "没有可发送到 AI 的对象")
            return
        limit = min(len(items), self.ai_send_limit_spin.value())
        texts = [(x.en or x.subtitle_text) for x in items[:limit]]
        merged = "\n".join(texts)
        self.tabs.setCurrentWidget(self.ai_tab)
        self.ai_input_preview.setPlainText(merged)
        self.append_log(f"已将 {limit} 条内容写入 AI 发送预览区。")

    def open_word_action_dialog(self, item: LearningItem):
        dlg = WordActionDialog(item.en or item.subtitle_text, self)
        dlg.add_vocab.connect(lambda word, sent: self.add_vocab_entry(word, sent))
        dlg.send_ai.connect(lambda txt: self.send_text_to_ai(txt))
        dlg.lookup_requested.connect(self.open_internal_dictionary_tabs)
        dlg.exec()

    def add_vocab_entry(self, word: str, sentence: str):
        if not word:
            return
        self.vocab_store.append(VocabularyEntry(word=word, source_uid=self.current_item.uid if self.current_item else "", source_text=sentence))
        self._save_vocab_store()
        self.refresh_vocab_table()
        self.tabs.setCurrentWidget(self.vocab_tab)

    def send_text_to_ai(self, text: str):
        self.tabs.setCurrentWidget(self.ai_tab)
        self.ai_input_preview.setPlainText(text)

    def append_log(self, text: str):
        stamp = time.strftime("[%H:%M:%S] ")
        self.online_log.appendPlainText(stamp + text)
        self.download_log.appendPlainText(stamp + text)
        self.batch_log.appendPlainText(stamp + text)

    def append_learning_message(self, text: str):
        self.learning_panel.appendPlainText(text)

    def format_seconds(self, sec: float) -> str:
        sec = max(0, int(sec))
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # ---------- local actions ----------
    def add_root_path(self):
        d = QFileDialog.getExistingDirectory(self, "选择根目录")
        if d and d not in [self.root_list.item(i).text() for i in range(self.root_list.count())]:
            self.root_list.addItem(d)

    def remove_selected_root(self):
        row = self.root_list.currentRow()
        if row >= 0:
            self.root_list.takeItem(row)

    def clear_all_roots(self):
        self.root_list.clear()

    def scan_paths(self):
        roots = [self.root_list.item(i).text() for i in range(self.root_list.count())]
        if not roots:
            QMessageBox.warning(self, "提示", "请先添加至少一个根目录")
            return
        self.scan_btn.setEnabled(False)
        self.scan_worker = ScanWorker(roots)
        self.scan_worker.finished_ok.connect(self.on_scan_done)
        self.scan_worker.failed.connect(self.on_scan_failed)
        self.scan_worker.start()

    def on_scan_done(self, items: list, unmatched: list):
        self.scan_btn.setEnabled(True)
        self._sync_item_notes_from_store(items)
        self.local_library = items
        self.path_info.setText(f"已扫描到 {len(items)} 条本地样本；未配对 {len(unmatched)} 项。")
        QMessageBox.information(self, "扫描完成", f"本地字幕库样本：{len(items)}\n未配对：{len(unmatched)}")

    def on_scan_failed(self, msg: str):
        self.scan_btn.setEnabled(True)
        QMessageBox.critical(self, "扫描失败", msg)

    def start_local_search(self):
        if not self.local_library:
            QMessageBox.warning(self, "提示", "请先扫描本地字幕库")
            return
        keyword = self.local_keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
        limit = int(self.local_result_limit_edit.text().strip() or 0) if self.local_result_limit_edit.text().strip().isdigit() else 0
        self.local_search_btn.setEnabled(False)
        self.local_search_worker = LocalSearchWorker(self.local_library, keyword, self.local_path_filter_edit.text(), limit, self.local_result_sort_combo.currentText())
        self.local_search_worker.finished_ok.connect(self.on_local_search_done)
        self.local_search_worker.failed.connect(self.on_local_search_failed)
        self.local_search_worker.start()

    def on_local_search_done(self, hits: list):
        self.local_search_btn.setEnabled(True)
        self.local_results = hits
        self.update_all_tables()
        self.append_log(f"本地搜索完成：{len(hits)} 条")

    def on_local_search_failed(self, msg: str):
        self.local_search_btn.setEnabled(True)
        QMessageBox.critical(self, "本地搜索失败", msg)

    def clear_local_results(self):
        self.local_results = []
        self.update_all_tables()

    # ---------- online actions ----------
    def start_online_search(self):
        keyword = self.online_keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入联网搜索词")
            return
        self.save_all_settings(silent=True)
        self.online_search_btn.setEnabled(False)
        self.online_worker = OnlineSearchWorker(keyword, self.collect_settings_snapshot(), self.online_limit_spin.value())
        self.online_worker.finished_ok.connect(self.on_online_search_done)
        self.online_worker.failed.connect(self.on_online_search_failed)
        self.online_worker.start()

    def on_online_search_done(self, items: list, hint: str):
        self.online_search_btn.setEnabled(True)
        self._sync_item_notes_from_store(items)
        self.online_results = items
        self.update_all_tables()
        self.online_log.appendPlainText(hint)

    def on_online_search_failed(self, msg: str):
        self.online_search_btn.setEnabled(True)
        QMessageBox.critical(self, "联网搜索失败", msg)

    def clear_online_results(self):
        self.online_results = []
        self.update_all_tables()

    def add_online_items_to_download_queue(self):
        items = self.resolve_action_items(self.online_results, self.online_result_table)
        if not items:
            QMessageBox.information(self, "提示", "没有可加入下载队列的联网结果")
            return
        added = 0
        for item in items:
            url = item.video_url or item.extra.get("video-url") or item.extra.get("url") or ""
            if not url:
                continue
            self._append_download_task({"name": self._safe_filename(item.show_name or item.en or item.subtitle_text)[:80], "url": url})
            added += 1
            if item.cache_path:
                self.pending_download_cleanup.append(Path(item.cache_path))
        QMessageBox.information(self, "下载队列", f"已加入 {added} 条下载任务。")
        self.tabs.setCurrentWidget(self.download_tab)

    # ---------- AI actions ----------
    def populate_ai_target_table(self):
        if not hasattr(self, "ai_target_table"):
            return
        self.ai_target_table.blockSignals(True)
        self.ai_target_table.setRowCount(0)
        for target in self.ai_targets:
            r = self.ai_target_table.rowCount()
            self.ai_target_table.insertRow(r)
            self.ai_target_table.setItem(r, 0, QTableWidgetItem(target.name or ""))
            self.ai_target_table.setItem(r, 1, QTableWidgetItem(target.kind or "generic"))
            self.ai_target_table.setItem(r, 2, QTableWidgetItem(target.endpoint or ""))
            self.ai_target_table.setItem(r, 3, QTableWidgetItem((target.method or "POST").upper()))
            self.ai_target_table.setItem(r, 4, QTableWidgetItem("是" if bool(target.enabled) else "否"))
        self.ai_target_table.blockSignals(False)
        if self.ai_target_table.rowCount() > 0 and not self.get_table_selected_rows(self.ai_target_table):
            self.ai_target_table.selectRow(0)
        self.on_ai_target_row_changed()

    def add_ai_target_row(self):
        self.ai_targets.append(AITarget(name=f"对象{len(self.ai_targets)+1}", kind="generic", endpoint="", method="POST", headers_json="{}", enabled=True))
        self.populate_ai_target_table()
        row = self.ai_target_table.rowCount() - 1 if hasattr(self, "ai_target_table") else -1
        if row >= 0:
            self.ai_target_table.selectRow(row)
        self.refresh_ai_target_combo()
        self._set_config_status("已新增 AI 对象")

    def remove_ai_target_row(self):
        rows = self.get_table_selected_rows(self.ai_target_table) if hasattr(self, "ai_target_table") else []
        if not rows:
            return
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self.ai_targets):
                self.ai_targets.pop(row)
        if not self.ai_targets:
            self.ai_targets = [AITarget(name="默认 AI", endpoint="", method="POST", headers_json="{}", enabled=True)]
        self.populate_ai_target_table()
        self.refresh_ai_target_combo()
        self._set_config_status("已删除 AI 对象")

    def on_ai_target_row_changed(self):
        if not hasattr(self, "ai_target_table"):
            return
        rows = self.get_table_selected_rows(self.ai_target_table)
        if not rows:
            try:
                self.ai_headers_edit.blockSignals(True)
                self.ai_headers_edit.setPlainText("")
                self.ai_headers_edit.blockSignals(False)
            except Exception:
                pass
            return
        idx = rows[0]
        if 0 <= idx < len(self.ai_targets):
            target = self.ai_targets[idx]
            try:
                self.ai_headers_edit.blockSignals(True)
                self.ai_headers_edit.setPlainText(target.headers_json or "{}")
                self.ai_headers_edit.blockSignals(False)
            except Exception:
                pass

    def pull_ai_targets_from_table(self, silent: bool = False):
        if hasattr(self, "ai_target_table"):
            new_targets = []
            for r in range(self.ai_target_table.rowCount()):
                def cell(col):
                    it = self.ai_target_table.item(r, col)
                    return it.text().strip() if it else ""
                enabled_text = cell(4)
                enabled = enabled_text in ("是", "true", "True", "1", "yes", "YES")
                headers_json = "{}"
                sel_rows = self.get_table_selected_rows(self.ai_target_table)
                if sel_rows and sel_rows[0] == r and hasattr(self, "ai_headers_edit"):
                    headers_json = self.ai_headers_edit.toPlainText().strip() or "{}"
                elif r < len(self.ai_targets):
                    headers_json = self.ai_targets[r].headers_json or "{}"
                new_targets.append(AITarget(
                    name=cell(0) or f"对象{r+1}",
                    kind=cell(1) or "generic",
                    endpoint=cell(2),
                    method=(cell(3) or "POST").upper(),
                    headers_json=headers_json,
                    enabled=enabled,
                ))
            self.ai_targets = new_targets or [AITarget(name="默认 AI", endpoint="", method="POST", headers_json="{}", enabled=True)]
        self.refresh_ai_target_combo()
        if not silent:
            self._set_config_status("AI 接收对象已刷新到运行中")

    def refresh_ai_target_combo(self):
        if not hasattr(self, "ai_target_combo"):
            return
        self.ai_target_combo.blockSignals(True)
        self.ai_target_combo.clear()
        for t in self.ai_targets:
            if t.enabled:
                self.ai_target_combo.addItem(t.name)
        self.ai_target_combo.blockSignals(False)

    def send_preview_to_ai(self):
        text = self.ai_input_preview.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "提示", "发送预览区为空")
            return
        target_name = self.ai_target_combo.currentText().strip()
        target = next((t for t in self.ai_targets if t.name == target_name), None)
        if not target:
            QMessageBox.warning(self, "提示", "请先配置接收 AI 对象")
            return
        texts = [x for x in text.splitlines() if x.strip()][:self.ai_send_limit_spin.value()]
        self.ai_send_btn.setEnabled(False)
        self.ai_worker = AITaskWorker(texts, target, self.collect_settings_snapshot())
        self.ai_worker.finished_ok.connect(self.on_ai_finished)
        self.ai_worker.failed.connect(self.on_ai_failed)
        self.ai_worker.start()

    def on_ai_finished(self, text: str):
        self.ai_send_btn.setEnabled(True)
        self.ai_output.setPlainText(text)

    def on_ai_failed(self, msg: str):
        self.ai_send_btn.setEnabled(True)
        QMessageBox.critical(self, "AI 请求失败", msg)

    def show_ai_target_examples(self):
        msg = (
            "AI接收对象案例：\n\n"
            "1. 通用 JSON 接口\n名称：本地AI\n类型：generic\n端点：http://127.0.0.1:8000/api/chat\n方法：POST\n请求头：{\"Content-Type\": \"application/json\"}\n\n"
            "2. 需要鉴权的接口\n名称：企业AI\n类型：generic\n端点：https://example.com/api/chat\n方法：POST\n请求头：{\"Authorization\": \"Bearer 你的Key\", \"Content-Type\": \"application/json\"}\n\n"
            "3. 调试模式\n端点留空时，发送按钮会先把组合文本作为预览结果，便于测试链路。"
        )
        QMessageBox.information(self, "AI接收对象案例", msg)


    def pick_note_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择学习笔记输出目录", self.notes_dir_edit.text().strip() if hasattr(self, "notes_dir_edit") else str(self._notes_output_dir()))
        if not d:
            return
        Path(d).mkdir(parents=True, exist_ok=True)
        if hasattr(self, "notes_dir_edit"):
            self.notes_dir_edit.setText(d)
        self.settings["notes_output_dir"] = d
        self.save_all_settings(silent=True)

    def pick_vocab_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择生词本输出目录", self.vocab_dir_edit.text().strip() if hasattr(self, "vocab_dir_edit") else str(self._vocab_output_dir()))
        if not d:
            return
        Path(d).mkdir(parents=True, exist_ok=True)
        if hasattr(self, "vocab_dir_edit"):
            self.vocab_dir_edit.setText(d)
        self.settings["vocab_output_dir"] = d
        self.save_all_settings(silent=True)

    def _open_note_editor(self, record: Optional[dict] = None):
        record = record or {}
        dlg = QDialog(self)
        dlg.setWindowTitle("学习笔记编辑")
        dlg.resize(720, 420)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()
        source_edit = QLineEdit(record.get("source", self.current_item.show_name if self.current_item else ""))
        time_edit = QLineEdit(record.get("time", self.format_seconds(self.current_item.start_time) if self.current_item else ""))
        text_edit = QTextEdit()
        text_edit.setPlainText(record.get("text", (self.current_item.en or self.current_item.subtitle_text) if self.current_item else ""))
        note_edit = QTextEdit()
        note_edit.setPlainText(record.get("note", ""))
        form.addRow("来源", source_edit)
        form.addRow("时间", time_edit)
        form.addRow("台词", text_edit)
        form.addRow("备注", note_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec() != QDialog.Accepted:
            return None
        uid = record.get("uid") or (self.current_item.uid if self.current_item else uuid.uuid4().hex)
        return {
            "uid": uid,
            "source": source_edit.text().strip(),
            "time": time_edit.text().strip(),
            "text": text_edit.toPlainText().strip(),
            "note": note_edit.toPlainText().strip(),
        }

    def open_note_editor_from_tab(self):
        rec = self._open_note_editor()
        if not rec:
            return
        self.notes_records[rec["uid"]] = rec
        self.notes_store[rec["uid"]] = rec.get("note", "")
        for item in self.local_library + self.local_results + self.online_results + self.state.playlist:
            if item.uid == rec["uid"]:
                item.note = rec.get("note", "")
        self._save_notes_store()
        self.refresh_notes_table()
        self.update_all_tables()

    def edit_selected_note(self):
        rows = self.get_table_selected_rows(self.notes_table)
        if not rows:
            QMessageBox.information(self, "提示", "请先选中一条笔记")
            return
        uid = self.notes_table.item(rows[0], 0).data(Qt.UserRole)
        rec = self.notes_records.get(uid)
        if not rec:
            QMessageBox.warning(self, "提示", "未找到对应笔记")
            return
        new_rec = self._open_note_editor(rec)
        if not new_rec:
            return
        self.notes_records[uid] = new_rec
        self.notes_store[uid] = new_rec.get("note", "")
        for item in self.local_library + self.local_results + self.online_results + self.state.playlist:
            if item.uid == uid:
                item.note = new_rec.get("note", "")
        self._save_notes_store()
        self.refresh_notes_table()
        self.update_all_tables()

    def _open_vocab_editor_dialog(self, entry: Optional[VocabularyEntry] = None):
        entry = entry or VocabularyEntry(word="", source_uid=self.current_item.uid if self.current_item else "", source_text=(self.current_item.en or self.current_item.subtitle_text) if self.current_item else "")
        dlg = QDialog(self)
        dlg.setWindowTitle("生词本编辑")
        dlg.resize(640, 360)
        lay = QVBoxLayout(dlg)
        form = QFormLayout()
        word_edit = QLineEdit(entry.word)
        source_edit = QTextEdit()
        source_edit.setPlainText(entry.source_text)
        note_edit = QTextEdit()
        note_edit.setPlainText(entry.note)
        form.addRow("单词/短语", word_edit)
        form.addRow("来源台词", source_edit)
        form.addRow("备注", note_edit)
        lay.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec() != QDialog.Accepted:
            return None
        return VocabularyEntry(
            word=word_edit.text().strip(),
            source_uid=entry.source_uid,
            source_text=source_edit.toPlainText().strip(),
            note=note_edit.toPlainText().strip(),
            color=entry.color,
            font_family=entry.font_family,
        )

    def open_vocab_editor(self):
        rec = self._open_vocab_editor_dialog()
        if not rec or not rec.word:
            return
        self.vocab_store.append(rec)
        self._save_vocab_store()
        self.refresh_vocab_table()

    def edit_selected_vocab(self):
        rows = self.get_table_selected_rows(self.vocab_table)
        if not rows:
            QMessageBox.information(self, "提示", "请先选中一条生词")
            return
        idx_item = self.vocab_table.item(rows[0], 0)
        idx = idx_item.data(Qt.UserRole) if idx_item else None
        if not isinstance(idx, int) or not (0 <= idx < len(self.vocab_store)):
            QMessageBox.warning(self, "提示", "未找到对应生词")
            return
        new_rec = self._open_vocab_editor_dialog(self.vocab_store[idx])
        if not new_rec or not new_rec.word:
            return
        self.vocab_store[idx] = new_rec
        self._save_vocab_store()
        self.refresh_vocab_table()

    def change_selected_vocab_style(self):
        rows = self.get_table_selected_rows(self.vocab_table)
        if not rows:
            QMessageBox.information(self, "提示", "请先选中一条生词")
            return
        idx_item = self.vocab_table.item(rows[0], 0)
        idx = idx_item.data(Qt.UserRole) if idx_item else None
        if not isinstance(idx, int) or not (0 <= idx < len(self.vocab_store)):
            QMessageBox.warning(self, "提示", "未找到对应生词")
            return
        entry = self.vocab_store[idx]
        color = QColorDialog.getColor(QColor(entry.color or "#5c4c67"), self, "选择文字颜色")
        if color.isValid():
            entry.color = color.name()
        font_result = QFontDialog.getFont(self)
        font, ok = self._normalize_qfontdialog_result(font_result, self.font())
        if ok:
            entry.font_family = font.family()
        self.vocab_store[idx] = entry
        self._save_vocab_store()
        self.refresh_vocab_table()

    # ---------- notes / vocab ----------
    def refresh_notes_table(self):
        query = self.notes_search_edit.text().strip().lower() if hasattr(self, "notes_search_edit") else ""
        values = list(self.notes_records.values())
        self.notes_table.setRowCount(0)
        for rec in values:
            hay = " ".join([rec.get("source", ""), rec.get("time", ""), rec.get("text", ""), rec.get("note", "")]).lower()
            if query and query not in hay:
                continue
            r = self.notes_table.rowCount()
            self.notes_table.insertRow(r)
            vals = [rec.get("source", ""), rec.get("time", ""), rec.get("text", ""), rec.get("note", "")]
            for c, v in enumerate(vals):
                q = QTableWidgetItem(v)
                q.setData(Qt.UserRole, rec.get("uid", ""))
                self.notes_table.setItem(r, c, q)

    def export_notes(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出笔记", str(self._notes_output_dir() / "学习笔记.txt"), "Text (*.txt)")
        if not path:
            return
        lines = []
        for row in range(self.notes_table.rowCount()):
            vals = [self.notes_table.item(row, c).text() for c in range(self.notes_table.columnCount())]
            lines.append("	".join(vals))
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        QMessageBox.information(self, "导出完成", path)

    def delete_selected_notes(self):
        rows = self.get_table_selected_rows(self.notes_table)
        uids = [self.notes_table.item(r, 0).data(Qt.UserRole) for r in rows]
        for uid in uids:
            self.notes_records.pop(uid, None)
            self.notes_store.pop(uid, None)
        for item in self.local_results + self.online_results + self.state.playlist:
            if item.uid in uids:
                item.note = ""
        self._save_notes_store()
        self.refresh_notes_table()
        self.update_all_tables()

    def refresh_vocab_table(self):
        query = self.vocab_search_edit.text().strip().lower() if hasattr(self, "vocab_search_edit") else ""
        self.vocab_table.setRowCount(0)
        for idx, entry in enumerate(self.vocab_store):
            hay = " ".join([entry.word, entry.source_text, entry.note, entry.color, entry.font_family]).lower()
            if query and query not in hay:
                continue
            r = self.vocab_table.rowCount()
            self.vocab_table.insertRow(r)
            vals = [entry.word, entry.source_text, entry.note, entry.color, entry.font_family]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setForeground(QColor(entry.color or '#5c4c67'))
                item.setData(Qt.UserRole, idx)
                self.vocab_table.setItem(r, c, item)

    def export_vocab(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出生词本", str(self._vocab_output_dir() / "生词本.txt"), "Text (*.txt)")
        if not path:
            return
        lines = []
        for e in self.vocab_store:
            lines.append("	".join([e.word, e.source_text, e.note, e.color, e.font_family]))
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        QMessageBox.information(self, "导出完成", path)

    def delete_selected_vocab(self):
        rows = self.get_table_selected_rows(self.vocab_table)
        idxs = sorted({self.vocab_table.item(r, 0).data(Qt.UserRole) for r in rows if self.vocab_table.item(r, 0)}, reverse=True)
        for idx in idxs:
            if isinstance(idx, int) and 0 <= idx < len(self.vocab_store):
                self.vocab_store.pop(idx)
        self._save_vocab_store()
        self.refresh_vocab_table()

    def resolve_checked_playlist_items(self) -> List[LearningItem]:
        return [x for x in self.state.playlist if x.checked]

    def resolve_selected_playlist_items(self) -> List[LearningItem]:
        rows = self.get_table_selected_rows(self.playlist_table)
        return [self.state.playlist[r] for r in rows if 0 <= r < len(self.state.playlist)]

    def _sort_play_items(self, items: List[LearningItem]) -> List[LearningItem]:
        if self.state.order_mode == "add":
            return sorted(items, key=lambda x: x.added_index)
        playlist_index = {item.uid: idx for idx, item in enumerate(self.state.playlist)}
        return sorted(items, key=lambda x: playlist_index.get(x.uid, 10**9))

    def build_sequence(self, action_mode: str) -> List[Tuple[LearningItem, str]]:
        checked = self.resolve_checked_playlist_items()
        selected = self.resolve_selected_playlist_items()
        loop_mode = self.loop_mode_combo.currentText()
        count = self.loop_count_spin.value()
        seq: List[Tuple[LearningItem, str]] = []
        if action_mode == "full":
            target = selected[0] if selected else (self.state.playlist[0] if self.state.playlist else None)
            return [(target, "full")] if target else []

        if loop_mode == "all":
            base = list(self.state.playlist)
        elif checked:
            base = self._sort_play_items(checked)
        elif selected:
            base = self._sort_play_items(selected)
        elif self.state.playlist:
            base = [self.state.playlist[0]] if loop_mode == "single" else list(self.state.playlist)
        else:
            base = []

        if loop_mode == "single":
            target = base[0] if base else None
            if target:
                for _ in range(count):
                    seq.append((target, action_mode))
        else:
            for item in base:
                for _ in range(count):
                    seq.append((item, action_mode))
        return seq

    def start_playlist_play(self, action_mode: str):
        self.state.play_mode = action_mode
        seq = self.build_sequence(action_mode)
        if not seq:
            QMessageBox.information(self, "提示", "没有可播放的内容")
            return
        self.play_sequence = seq
        self.play_sequence_index = 0
        self.update_play_status_label(action_mode)
        self.play_sequence_item(seq[0][0], seq[0][1])

    def start_full_view(self):
        self.state.play_mode = "full"
        seq = self.build_sequence("full")
        if not seq:
            QMessageBox.information(self, "提示", "请先在播放列表选择一个视频")
            return
        self.play_sequence = seq
        self.play_sequence_index = 0
        self.update_play_status_label("full")
        self.play_sequence_item(seq[0][0], "full")
        self.enter_fullscreen()

    def play_single_playlist_item(self, row: int):
        if not (0 <= row < len(self.state.playlist)):
            return
        item = self.state.playlist[row]
        self.state.play_mode = "video"
        self.update_play_status_label("selected")
        self.play_sequence = [(item, "video")]
        self.play_sequence_index = 0
        self.play_sequence_item(item, "video")

    def play_sequence_item(self, item: LearningItem, mode: str):
        if not item:
            return
        self.state.current_playing_uid = item.uid
        self.current_item = item
        self._last_subtitle_key = None
        self.update_all_tables()
        self.load_item_subtitles(item)
        if item.source_type == "local":
            self.play_local_item(item, mode)
        else:
            self.play_online_item(item, mode)
        zh = item.zh or self.line_translation_cache.get(item.en or "", "")
        if not zh and (item.en or "").strip():
            self.request_line_translation(item.en or "")
        self.subtitle_browser.setPlainText(item.en or item.subtitle_text)
        self.translation_browser.setPlainText(zh or item.note or "")
        self.update_floating_subtitle(item.en or item.subtitle_text or "", zh or item.note or "")
        QTimer.singleShot(260, lambda: self.refresh_current_subtitle_displays(force=True))

    def play_local_item(self, item: LearningItem, mode: str):
        vp = Path(item.video_path)
        if not vp.exists():
            QMessageBox.warning(self, "提示", f"视频不存在：\n{vp}")
            return
        self.player.setSource(QUrl.fromLocalFile(str(vp)))
        start_ms = 0 if mode == "full" else int(item.start_time * 1000)
        self.current_segment_end_ms = int(item.end_time * 1000) if mode == "slice" else -1
        self.player.play()
        QTimer.singleShot(200, lambda: self.player.setPosition(start_ms))

    def play_online_item(self, item: LearningItem, mode: str):
        if item.video_url:
            self.player.setSource(QUrl(item.video_url))
            start_ms = 0 if mode == "full" else int(item.start_time * 1000)
            self.current_segment_end_ms = int(item.end_time * 1000) if mode == "slice" else -1
            self.player.play()
            QTimer.singleShot(300, lambda: self.player.setPosition(start_ms))
            return
        QMessageBox.information(self, "提示", "当前在线结果没有可播放的视频 URL，可先加入下载队列。")

    def play_next_sequence_item(self):
        if not hasattr(self, "play_sequence") or not self.play_sequence:
            return
        self.play_sequence_index += 1
        if self.play_sequence_index >= len(self.play_sequence):
            self.player.pause()
            self.current_segment_end_ms = -1
            return
        item, mode = self.play_sequence[self.play_sequence_index]
        self.play_sequence_item(item, mode)

    def on_player_position_changed(self, pos: int):
        self.pos_label.setText(self.format_seconds(pos / 1000))
        if not getattr(self, "_is_user_seeking", False) and not self.player_slider.isSliderDown():
            self.player_slider.setValue(pos)
        self.refresh_current_subtitle_displays(pos)
        if self.current_segment_end_ms > 0 and pos >= self.current_segment_end_ms:
            self.player.pause()
            self.current_segment_end_ms = -1
            QTimer.singleShot(120, self.play_next_sequence_item)

    def on_player_duration_changed(self, dur: int):
        self.player_slider.setRange(0, max(0, dur))
        self.dur_label.setText(self.format_seconds(dur / 1000))

    def on_player_slider_pressed(self):
        self._is_user_seeking = True
        self._player_slider_was_playing = self.player.playbackState() == QMediaPlayer.PlayingState
        if self._player_slider_was_playing:
            self.player.pause()

    def on_player_slider_moved(self, value: int):
        try:
            value = int(value)
        except Exception:
            value = int(self.player_slider.value())
        self.player.setPosition(value)
        self.pos_label.setText(self.format_seconds(value / 1000))
        self.refresh_current_subtitle_displays(value, force=True)

    def on_player_slider_released(self):
        value = int(self.player_slider.value())
        self.player.setPosition(value)
        self.pos_label.setText(self.format_seconds(value / 1000))
        self.refresh_current_subtitle_displays(value, force=True)
        self._is_user_seeking = False
        if self._player_slider_was_playing:
            QTimer.singleShot(0, self.player.play)
        self._player_slider_was_playing = False

    def _find_subtitle_row_for_position(self, pos_ms: int = None) -> Optional[dict]:
        if not self.current_subs:
            return None
        if pos_ms is None:
            pos_ms = self.player.position()
        pos = max(0.0, float(pos_ms) / 1000.0)
        candidate = None
        for row in self.current_subs:
            st = float(row.get("start", 0.0) or 0.0)
            ed = float(row.get("end", st) or st)
            if st <= pos <= ed:
                return row
            if st <= pos:
                candidate = row
            elif pos < st:
                break
        return candidate

    def refresh_current_subtitle_displays(self, pos_ms: int = None, force: bool = False):
        row = self._find_subtitle_row_for_position(pos_ms)
        en = ''
        zh = ''
        if row:
            en = (row.get("en") or row.get("text") or '').strip()
            zh = (row.get("zh") or '').strip()
            if not zh and en:
                zh = self.line_translation_cache.get(en, '')
                if not zh:
                    self.request_line_translation(en)
            key = (row.get("start"), row.get("end"), en, zh)
        else:
            key = None
            if self.current_item is not None:
                en = (self.current_item.en or self.current_item.subtitle_text or '').strip()
                zh = (self.current_item.zh or self.current_item.note or self.line_translation_cache.get(en, '') or '').strip()
        if not force and key == self._last_subtitle_key:
            return
        self._last_subtitle_key = key
        self.subtitle_browser.setPlainText(en)
        self.translation_browser.setPlainText(zh)
        self.adjust_learning_area_widgets(en, zh)
        self.update_floating_subtitle(en, zh)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_next_sequence_item()

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def enter_fullscreen(self):
        self.video_widget.setFullScreen(True)
        self.video_widget.setFocus()

    def exit_fullscreen(self):
        self.video_widget.setFullScreen(False)
        self.activateWindow()

    def toggle_fullscreen_shortcut(self):
        try:
            if self.video_widget.isFullScreen():
                self.exit_fullscreen()
            else:
                self.enter_fullscreen()
        except Exception:
            self.enter_fullscreen()

    def _cycle_combo(self, combo, step: int = 1):
        try:
            if combo is None:
                return
            total = combo.count()
            if total <= 0:
                return
            idx = combo.currentIndex()
            combo.setCurrentIndex((idx + step) % total)
        except Exception:
            pass

    def cycle_theme(self):
        self.cycle_theme_next()

    def cycle_theme_next(self):
        self._cycle_combo(getattr(self, 'theme_combo', None), 1)

    def cycle_theme_prev(self):
        self._cycle_combo(getattr(self, 'theme_combo', None), -1)

    def cycle_palette_next(self):
        self._cycle_combo(getattr(self, 'palette_combo', None), 1)

    def cycle_palette_prev(self):
        self._cycle_combo(getattr(self, 'palette_combo', None), -1)

    def set_subtitle_display_mode(self, mode: str):
        mode = (mode or 'dual').strip().lower()
        if mode not in ('single', 'dual', 'none'):
            mode = 'dual'
        self.subtitle_display_mode = mode
        if mode == 'single':
            self.subtitle_browser.setVisible(True)
            self.translation_browser.setVisible(False)
        elif mode == 'none':
            self.subtitle_browser.setVisible(False)
            self.translation_browser.setVisible(False)
        else:
            self.subtitle_browser.setVisible(True)
            self.translation_browser.setVisible(True)
        self.settings['subtitle_display_mode'] = mode
        self.schedule_settings_autosave()
        self.refresh_current_subtitle_displays(force=True)

    def is_top_toolbar_visible(self) -> bool:
        return self._layout_widgets_visible(getattr(self, 'top_toolbar_layout', None))

    def is_progress_toolbar_visible(self) -> bool:
        return self._layout_widgets_visible(getattr(self, 'progress_layout', None))

    def is_control_button_bar_visible(self) -> bool:
        return self._layout_widgets_visible(getattr(self, 'control_button_layout', None))

    def is_subtitle_action_bar_visible(self) -> bool:
        return self._layout_widgets_visible(getattr(self, 'subtitle_action_layout', None))

    def is_player_text_group_visible(self) -> bool:
        return getattr(self, 'player_text_group', None).isVisible() if hasattr(self, 'player_text_group') else True

    def is_bottom_learning_visible(self) -> bool:
        try:
            return self.right_splitter.widget(1).isVisible()
        except Exception:
            return True

    def toggle_top_toolbar(self):
        self._set_layout_widgets_visible(getattr(self, 'top_toolbar_layout', None), not self.is_top_toolbar_visible())
        self.schedule_settings_autosave()

    def toggle_progress_toolbar(self):
        self._set_layout_widgets_visible(getattr(self, 'progress_layout', None), not self.is_progress_toolbar_visible())
        self.schedule_settings_autosave()

    def toggle_control_button_bar(self):
        self._set_layout_widgets_visible(getattr(self, 'control_button_layout', None), not self.is_control_button_bar_visible())
        self.schedule_settings_autosave()

    def toggle_subtitle_action_bar(self):
        self._set_layout_widgets_visible(getattr(self, 'subtitle_action_layout', None), not self.is_subtitle_action_bar_visible())
        self.schedule_settings_autosave()

    def toggle_player_text_group(self):
        if hasattr(self, 'player_text_group'):
            self.player_text_group.setVisible(not self.player_text_group.isVisible())
            self.schedule_settings_autosave()

    def toggle_group_visibility(self, attr_name: str):
        widget = getattr(self, attr_name, None)
        if widget is not None:
            widget.setVisible(not widget.isVisible())
            self.schedule_settings_autosave()

    def toggle_bottom_learning(self):
        try:
            widget = self.right_splitter.widget(1)
            widget.setVisible(not widget.isVisible())
            self.schedule_settings_autosave()
        except Exception:
            pass

    def update_floating_subtitle(self, en: str, zh: str):
        if not hasattr(self, 'floating_subtitle'):
            return
        show_zh = self.subtitle_display_mode == 'dual'
        self.floating_subtitle.set_texts(en or '', zh or '', show_zh=show_zh)
        if self.floating_subtitle_enabled and (en or zh):
            if self.floating_subtitle.geometry().width() <= 1:
                self.floating_subtitle.reset_to_default()
            self.floating_subtitle.show()
            self.floating_subtitle.raise_()
        elif not self.floating_subtitle_enabled:
            self.floating_subtitle.hide()

    def toggle_floating_subtitle(self):
        self.floating_subtitle_enabled = not bool(getattr(self, 'floating_subtitle_enabled', False))
        self.settings['floating_subtitle_enabled'] = self.floating_subtitle_enabled
        self.schedule_settings_autosave()
        if self.floating_subtitle_enabled:
            self.apply_saved_floating_subtitle_state()
            self.refresh_current_subtitle_displays(force=True)
        else:
            self.floating_subtitle.hide()

    def reset_floating_subtitle_position(self):
        if hasattr(self, 'floating_subtitle'):
            self.floating_subtitle.reset_to_default()
            self.floating_subtitle.raise_()

    def show_record_placeholder(self):
        QMessageBox.information(self, '录制', '录制功能已预留接口，后续接入 ffmpeg 即可。')

    def toggle_local_source_box(self):
        collapsed = self.source_toggle_btn.isChecked()
        source_widget = self.local_outer_splitter.widget(0)
        source_widget.setVisible(not collapsed)
        self.source_toggle_btn.setText("展开数据源" if collapsed else "折叠数据源")
        self.schedule_settings_autosave()
        QTimer.singleShot(0, self.restore_layouts)

    def change_playback_speed(self, text: str):
        try:
            rate = float(text.lower().replace('x', '').strip())
        except Exception:
            rate = 1.0
        self.player.setPlaybackRate(rate)
        self.append_learning_message(f"播放速度已切换为 {rate:.2f}x")

    def clear_dictionary_tabs(self):
        self.dict_browser_tabs.clear()

    def get_dictionary_sources(self) -> List[str]:
        sources = []
        for edit in [self.dict_source_edit_1, self.dict_source_edit_2, self.dict_source_edit_3]:
            txt = edit.text().strip()
            if txt:
                sources.append(txt)
        return sources

    def format_dictionary_url(self, base_url: str, query: str) -> str:
        q = urllib.parse.quote(query.strip())
        if '{query}' in base_url:
            return base_url.replace('{query}', q)
        if base_url.endswith('/'):
            return base_url + q
        return base_url + (('&' if '?' in base_url else '/') + q if q else '')

    def open_internal_dictionary_tabs(self, query: str):
        query = (query or '').strip()
        if not query:
            return
        self.tabs.setCurrentWidget(self.dict_tab)
        self.dict_query_edit.setText(query)
        self.clear_dictionary_tabs()
        sources = self.get_dictionary_sources()[:3]
        if not sources:
            QMessageBox.information(self, '提示', '请先在“查词来源”标签页设置词典网址。')
            return
        for idx, base in enumerate(sources, 1):
            url = self.format_dictionary_url(base, query)
            view = EmbeddedWebView()
            view.load_url(url)
            title = f"词典{idx}: {query}"
            self.dict_browser_tabs.addTab(view, title)
        self.dict_browser_tabs.setCurrentIndex(0)

    def toggle_left_workspace(self):
        if not hasattr(self, "local_splitter"):
            return
        sizes = self.local_splitter.sizes()
        left_size = sizes[0] if sizes else 0
        if left_size > 30:
            self._last_left_sizes = sizes
            self.local_splitter.setSizes([0, sum(sizes) if sizes else 1000])
            if hasattr(self, "left_collapse_btn"):
                self.left_collapse_btn.setText("展开左侧")
        else:
            sizes = getattr(self, "_last_left_sizes", [760, 1080])
            self.local_splitter.setSizes(sizes)
            if hasattr(self, "left_collapse_btn"):
                self.left_collapse_btn.setText("收起左侧")

    def _sync_left_collapse_button(self, *args):
        if not hasattr(self, "local_splitter") or not hasattr(self, "left_collapse_btn"):
            return
        sizes = self.local_splitter.sizes()
        left_size = sizes[0] if sizes else 0
        self.left_collapse_btn.setText("展开左侧" if left_size <= 30 else "收起左侧")

    def restore_layouts(self):
        if hasattr(self, 'local_outer_splitter'):
            if self.local_outer_splitter.widget(0).isVisible():
                self.local_outer_splitter.setSizes([160, 740])
            else:
                self.local_outer_splitter.setSizes([0, 900])
        self.local_splitter.setSizes([520, 1320])
        if hasattr(self, "left_collapse_btn"):
            self.left_collapse_btn.setText("收起左侧")
        self.left_splitter.setSizes([430, 330])
        self.right_splitter.setSizes([520, 380])
        if hasattr(self, 'sub_learning_splitter'):
            self.sub_learning_splitter.setSizes([150, 120, 120])

    def apply_saved_splitter_sizes(self):
        for attr, key in [("local_outer_splitter", "local_outer_splitter_sizes"), ("local_splitter", "local_splitter_sizes"), ("left_splitter", "left_splitter_sizes"), ("right_splitter", "right_splitter_sizes")]:
            splitter = getattr(self, attr, None)
            sizes = self.settings.get(key)
            if splitter is not None and isinstance(sizes, list) and sizes:
                try:
                    splitter.setSizes([int(x) for x in sizes])
                except Exception:
                    pass

    def apply_saved_floating_subtitle_state(self):
        if not hasattr(self, 'floating_subtitle'):
            return
        geo = self.settings.get('floating_subtitle_geometry')
        if isinstance(geo, list) and len(geo) == 4:
            try:
                self.floating_subtitle.setGeometry(int(geo[0]), int(geo[1]), int(max(320, geo[2])), int(max(70, geo[3])))
            except Exception:
                self.floating_subtitle.reset_to_default()
        else:
            self.floating_subtitle.reset_to_default()
        if self.floating_subtitle_enabled:
            self.refresh_current_subtitle_displays(force=True)
        else:
            self.floating_subtitle.hide()

    def apply_saved_ui_state(self):
        if hasattr(self, 'source_toggle_btn') and hasattr(self, 'local_outer_splitter'):
            collapsed = bool(self.settings.get('source_collapsed', False))
            self.source_toggle_btn.blockSignals(True)
            self.source_toggle_btn.setChecked(collapsed)
            self.source_toggle_btn.blockSignals(False)
            source_widget = self.local_outer_splitter.widget(0)
            if source_widget is not None:
                source_widget.setVisible(not collapsed)
            self.source_toggle_btn.setText('展开数据源' if collapsed else '折叠数据源')
        target_top = bool(self.settings.get('top_toolbar_visible', True))
        if self.is_top_toolbar_visible() != target_top:
            self.toggle_top_toolbar()
        target_progress = bool(self.settings.get('progress_bar_visible', True))
        if self.is_progress_toolbar_visible() != target_progress:
            self.toggle_progress_toolbar()
        target_control = bool(self.settings.get('control_button_bar_visible', True))
        if self.is_control_button_bar_visible() != target_control:
            self.toggle_control_button_bar()
        target_actions = bool(self.settings.get('subtitle_action_bar_visible', True))
        if self.is_subtitle_action_bar_visible() != target_actions:
            self.toggle_subtitle_action_bar()
        target_text = bool(self.settings.get('player_text_group_visible', True))
        if self.is_player_text_group_visible() != target_text:
            self.toggle_player_text_group()
        target_bottom = bool(self.settings.get('bottom_learning_visible', True))
        if self.is_bottom_learning_visible() != target_bottom:
            self.toggle_bottom_learning()
        self.learning_mode_visible = bool(self.settings.get('learning_panel_visible', True))
        if hasattr(self, 'learning_panel'):
            self.learning_panel.setVisible(self.learning_mode_visible)
        if hasattr(self, 'learning_hint_label'):
            self.learning_hint_label.setVisible(self.learning_mode_visible)
        self.apply_saved_splitter_sizes()
        if hasattr(self, 'right_splitter') and self.right_splitter.count() > 1:
            saved_height = int(self.settings.get('learning_zone_height', 0) or 0)
            if saved_height > 0:
                sizes = self.right_splitter.sizes()
                total = sum(sizes) if sizes else self.right_splitter.height()
                if total <= 0:
                    total = max(700, self.right_splitter.height())
                bottom = max(220, min(saved_height, max(220, total - 180)))
                self.right_splitter.setSizes([max(180, total - bottom), bottom])
            self.sync_learning_height_slider_from_splitter()
        self.adjust_learning_area_widgets(self.subtitle_browser.toPlainText() if hasattr(self, 'subtitle_browser') else '', self.translation_browser.toPlainText() if hasattr(self, 'translation_browser') else '')
        self.set_subtitle_display_mode(self.settings.get('subtitle_display_mode', getattr(self, 'subtitle_display_mode', 'dual')))
        self.apply_saved_floating_subtitle_state()
        self._sync_left_collapse_button()

    def show_shortcut_settings(self):
        shortcut_map = self.settings.get("shortcut_map", {
            "sample_prev": "Up",
            "sample_next": "Down",
            "sentence_prev": "Left",
            "sentence_next": "Right",
            "toggle_play": "Space",
            "focus_search": "Ctrl+F",
            "restore_layout": "Ctrl+0",
            "toggle_fullscreen": "F11",
            "cycle_theme_next": "Ctrl+T",
            "cycle_theme_prev": "Ctrl+Shift+T",
            "cycle_palette_next": "Ctrl+P",
            "cycle_palette_prev": "Ctrl+Shift+P",
            "subtitle_single": "Ctrl+1",
            "subtitle_dual": "Ctrl+2",
            "subtitle_none": "Ctrl+3",
            "take_screenshot": "Ctrl+Shift+S",
            "record_placeholder": "Ctrl+R",
            "toggle_bottom_learning": "Ctrl+L",
            "toggle_top_bar": "Ctrl+H",
            "toggle_learning_hint": "Ctrl+Shift+H",
            "toggle_search_results": "Ctrl+Shift+F",
            "toggle_playlist_panel": "Ctrl+Shift+P",
            "toggle_progress_bar": "Ctrl+Shift+J",
            "toggle_control_buttons": "Ctrl+Shift+K",
            "toggle_learning_actions": "Ctrl+Shift+A",
            "toggle_text_panel": "Ctrl+Shift+T",
            "shortcut_settings_panel": "Ctrl+Alt+K",
        })
        dlg = ShortcutSettingsDialog(shortcut_map, self)
        if dlg.exec() == QDialog.Accepted:
            new_map = dlg.get_shortcuts()
            self.settings["shortcut_map"] = new_map
            self._register_shortcuts()
            try:
                self.save_all_settings(silent=True)
            except Exception:
                pass
            QMessageBox.information(self, "快捷键设置", "快捷键已保存并立即生效。")

    def show_shortcuts(self):
        QMessageBox.information(self, "快捷键说明", "上下方向键：切换样本\n左右方向键：按句子切换\nSpace：播放/暂停\nCtrl+F：聚焦搜索框\nCtrl+0：恢复布局\nF11：全屏/退出全屏\nCtrl+T：切换主题\nCtrl+1/2/3：字幕单/双/无\nCtrl+Shift+S：截图\nCtrl+R：录制占位\nCtrl+L：隐藏底部学习区\nCtrl+H：隐藏顶部按钮区\nCtrl+Shift+H：隐藏学习提示\nCtrl+Shift+F：显示/隐藏搜索结果区\nCtrl+Shift+P：显示/隐藏播放列表区\nCtrl+Shift+J：显示/隐藏进度栏\nCtrl+Shift+K：显示/隐藏播放控制按钮\nCtrl+Shift+A：显示/隐藏学习动作按钮\nCtrl+Shift+T：显示/隐藏台词翻译区\nCtrl+Alt+K：打开快捷键设置面板\nEsc：退出全屏")

    def toggle_subtitle_panel(self):
        self.subtitle_browser.setVisible(not self.subtitle_browser.isVisible())
        self.translation_browser.setVisible(not self.translation_browser.isVisible())

    def take_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存截图", str(BASE_DIR / "screenshot.png"), "PNG (*.png)")
        if not path:
            return
        pix = self.video_widget.grab()
        pix.save(path)
        QMessageBox.information(self, "截图完成", path)

    def toggle_learning_panel(self):
        self.learning_mode_visible = not self.learning_mode_visible
        self.learning_panel.setVisible(self.learning_mode_visible)
        self.settings['learning_panel_visible'] = self.learning_mode_visible
        self.schedule_settings_autosave()

    def load_item_subtitles(self, item: LearningItem):
        self.current_subs = []
        if item.subtitle_path and Path(item.subtitle_path).exists():
            sp = Path(item.subtitle_path)
            self.current_subs = parse_srt(sp) if sp.suffix.lower() == ".srt" else parse_ass(sp)

    def find_current_sentence_index(self) -> int:
        if not self.current_subs:
            return -1
        pos = self.player.position() / 1000.0
        for idx, row in enumerate(self.current_subs):
            if row["start"] <= pos <= row["end"]:
                return idx
        starts = [row["start"] for row in self.current_subs]
        for idx, st in enumerate(starts):
            if pos < st:
                return max(0, idx - 1)
        return len(self.current_subs) - 1

    def jump_sentence(self, delta: int):
        if not self.current_subs:
            return
        idx = self.find_current_sentence_index()
        if idx < 0:
            idx = 0
        idx = max(0, min(len(self.current_subs) - 1, idx + delta))
        target = self.current_subs[idx]
        self.player.setPosition(int(target["start"] * 1000))
        self.refresh_current_subtitle_displays(int(target["start"] * 1000), force=True)

    def navigate_samples(self, delta: int):
        source_items = self.resolve_checked_playlist_items()
        if not source_items:
            source_items = self.resolve_selected_playlist_items()
        if not source_items:
            return
        source_items = self._sort_play_items(source_items)
        current_uid = self.state.current_selected_uid or (source_items[0].uid if source_items else None)
        index = next((i for i, x in enumerate(source_items) if x.uid == current_uid), 0)
        index = max(0, min(len(source_items) - 1, index + delta))
        target = source_items[index]
        self.state.current_selected_uid = target.uid
        self.select_item_in_playlist(target.uid)
        self.append_learning_message(f"导航到：{target.en or target.subtitle_text}")
        self.update_all_tables()

    def select_item_in_playlist(self, uid: str):
        self.playlist_table.clearSelection()
        for row in range(self.playlist_table.rowCount()):
            if self.playlist_table.item(row, 0).data(Qt.UserRole) == uid:
                self.playlist_table.selectRow(row)
                break

    def lookup_current_text(self):
        txt = (self.subtitle_browser.textCursor().selectedText() or self.subtitle_browser.toPlainText()).strip()
        if not txt:
            return
        self.open_internal_dictionary_tabs(txt.split()[0])

    def add_current_to_vocab(self):
        txt = (self.subtitle_browser.textCursor().selectedText() or self.subtitle_browser.toPlainText()).strip()
        if not txt:
            return
        self.add_vocab_entry(txt.split()[0], self.subtitle_browser.toPlainText())

    def request_line_translation(self, text: str):
        key = text.strip()
        if not key or key in self.line_translation_cache or key in self.translate_workers:
            return
        worker = TranslateLineWorker(key, key, "MyMemory 免费")
        self.translate_workers[key] = worker
        worker.finished_ok.connect(self.on_line_translated)
        worker.failed.connect(self.on_line_translate_failed)
        worker.start()

    def on_line_translated(self, cache_key: str, result: str):
        self.line_translation_cache[cache_key] = result
        self.translate_workers.pop(cache_key, None)
        if self.current_item is not None:
            self.refresh_current_subtitle_displays(force=True)

    def on_line_translate_failed(self, cache_key: str, _msg: str):
        self.translate_workers.pop(cache_key, None)

    def update_play_status_label(self, action_mode: str):
        order_txt = "添加顺序" if self.state.order_mode == "add" else "播放列表顺序"
        loop = self.loop_mode_combo.currentText()
        count = self.loop_count_spin.value()
        if action_mode == "slice":
            source = "勾选列表" if self.resolve_checked_playlist_items() else "选中项"
            txt = f"当前策略：{source} + {order_txt} + 循环（每条）{count}次"
        elif action_mode == "video":
            txt = f"当前策略：勾选项从切片位置开始播放 + {order_txt}"
        elif action_mode == "full":
            txt = f"当前策略：全屏观影（忽略勾选，播放选中视频）"
        else:
            txt = f"当前策略：选中播放 {count} 次"
        txt += f" | 循环模式：{loop}"
        self.play_status_label.setText(txt)

    # ---------- download ----------
    def _append_download_task(self, task: dict):
        row = self.download_queue_table.rowCount()
        self.download_queue_table.insertRow(row)
        self.download_queue_table.setItem(row, 0, QTableWidgetItem(task.get("name", "")))
        self.download_queue_table.setItem(row, 1, QTableWidgetItem(task.get("url", "")))
        self.download_queue_table.setItem(row, 2, QTableWidgetItem("待下载"))

    def add_manual_urls_to_download_queue(self):
        lines = [x.strip() for x in self.download_urls_edit.toPlainText().splitlines() if x.strip()]
        for idx, line in enumerate(lines, 1):
            self._append_download_task({"name": f"manual_{idx}", "url": line})
        self.download_urls_edit.clear()

    def clear_download_queue(self):
        self.download_queue_table.setRowCount(0)

    def collect_download_tasks(self) -> List[dict]:
        tasks = []
        for row in range(self.download_queue_table.rowCount()):
            tasks.append({
                "name": self.download_queue_table.item(row, 0).text(),
                "url": self.download_queue_table.item(row, 1).text(),
            })
        return tasks

    def start_batch_download(self):
        tasks = self.collect_download_tasks()
        tasks = [t for t in tasks if t.get("url", "").strip()]
        if not tasks:
            QMessageBox.information(self, "提示", "下载队列为空")
            return
        out_dir = self.download_dir_edit.text().strip() or str(DOWNLOAD_DIR)
        safe_mkdir(Path(out_dir))
        self.download_log.clear()
        self.download_progress.setValue(0)
        self.download_progress_label.setText("进度：准备开始")
        self.download_log.appendPlainText(f"准备下载：{len(tasks)} 项，线程数 {self.download_thread_spin.value()}，目录：{out_dir}")
        for row in range(self.download_queue_table.rowCount()):
            self.download_queue_table.setItem(row, 2, QTableWidgetItem("排队中"))
        self.download_worker = DownloadWorker(tasks, out_dir, self.download_thread_spin.value())
        self.download_worker.log.connect(lambda msg: self.download_log.appendPlainText(msg))
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.done_ok.connect(self.on_download_done)
        self.download_worker.failed.connect(self.on_download_failed)
        self.start_download_btn.setEnabled(False)
        self.stop_download_btn.setEnabled(True)
        self.download_worker.start()

    def stop_batch_download(self):
        if hasattr(self, "download_worker"):
            self.download_worker.stop()

    def on_download_progress(self, done: int, total: int, pct: int, name: str):
        self.download_progress.setValue(pct)
        self.download_progress_label.setText(f"进度：{done}/{total}，{pct}% ，当前文件：{name}")
        for row in range(self.download_queue_table.rowCount()):
            item = self.download_queue_table.item(row, 0)
            if item and item.text() == name:
                self.download_queue_table.setItem(row, 2, QTableWidgetItem("完成"))
                break

    def on_download_done(self, summary: dict):
        self.start_download_btn.setEnabled(True)
        self.stop_download_btn.setEnabled(False)
        state_text = "已停止" if summary.get("stopped") else "完成"
        self.download_progress_label.setText(f"进度：{state_text}，成功 {summary['success']}，失败 {summary['failed']}")
        self.download_log.appendPlainText(json.dumps(summary, ensure_ascii=False, indent=2))
        QMessageBox.information(self, "批量下载", json.dumps(summary, ensure_ascii=False, indent=2))

    def on_download_failed(self, msg: str):
        self.start_download_btn.setEnabled(True)
        self.stop_download_btn.setEnabled(False)
        self.download_log.appendPlainText(msg)
        QMessageBox.critical(self, "批量下载失败", msg)

    # ---------- batch srt ----------
    def start_batch_srt(self):
        folder = Path(self.video_folder_edit.text().strip())
        if not folder.exists():
            QMessageBox.warning(self, "提示", "请选择有效的视频目录")
            return
        overwrite_existing = False
        if not self.skip_existing_cb.isChecked():
            existing = []
            for p in folder.rglob("*"):
                if p.suffix.lower() in VIDEO_EXTS:
                    target_dir = p.parent if self.same_dir_cb.isChecked() else Path(self.out_dir_edit.text().strip() or p.parent)
                    srt = target_dir / f"{p.stem}.srt"
                    if srt.exists():
                        existing.append(str(srt))
            if existing:
                ret = QMessageBox.question(self, "检测到已有字幕", f"检测到 {len(existing)} 个已存在字幕。\n是：跳过\n否：覆盖")
                if ret == QMessageBox.Yes:
                    self.skip_existing_cb.setChecked(True)
                else:
                    overwrite_existing = True
        self.batch_log.clear()
        self.batch_progress.setValue(0)
        self.start_batch_btn.setEnabled(False)
        self.cancel_batch_btn.setEnabled(True)
        self.batch_worker = BatchSrtWorker(
            exe_path=self.exe_edit.text().strip(),
            folder=self.video_folder_edit.text().strip(),
            model=self.model_combo.currentText(),
            model_path=self.model_path_edit.text().strip(),
            language=self.language_combo.currentText(),
            vad=self.vad_cb.isChecked(),
            enhance=self.enhance_cb.isChecked(),
            save_same_dir=self.same_dir_cb.isChecked(),
            out_dir=self.out_dir_edit.text().strip(),
            extra_args=self.extra_args_edit.text().strip(),
            skip_existing=self.skip_existing_cb.isChecked(),
            overwrite_existing=overwrite_existing,
            threads=self.thread_spin.value(),
        )
        self.batch_worker.log.connect(self.batch_log.appendPlainText)
        self.batch_worker.progress.connect(self.on_batch_progress)
        self.batch_worker.done_ok.connect(self.on_batch_done)
        self.batch_worker.failed.connect(self.on_batch_failed)
        self.batch_worker.start()

    def cancel_batch_srt(self):
        if hasattr(self, "batch_worker"):
            self.batch_worker.cancel()
            self.batch_log.appendPlainText("已发送取消请求。")

    def on_batch_progress(self, done: int, total: int, pct: int, name: str):
        self.batch_progress.setValue(pct)
        self.batch_progress_label.setText(f"进度：{done}/{total}，完成 {pct}% ，当前文件：{name}")

    def on_batch_done(self, summary: dict):
        self.start_batch_btn.setEnabled(True)
        self.cancel_batch_btn.setEnabled(False)
        self.batch_progress_label.setText(f"进度：完成，成功 {summary['success']}，跳过 {summary['skipped']}，失败 {summary['failed']}")
        try:
            log_path = BASE_DIR / 'batch_srt_last_log.txt'
            log_path.write_text(self.batch_log.toPlainText(), encoding='utf-8')
        except Exception:
            log_path = None
        msg = json.dumps(summary, ensure_ascii=False, indent=2)
        if summary.get('failed'):
            extra = "\n\n提示：rc=1 多数与模型/显存/路径参数有关，请查看批量日志。"
            if log_path:
                extra += f"\n日志已保存：{log_path}"
            msg += extra
        QMessageBox.information(self, "批量转 SRT", msg)

    def on_batch_failed(self, msg: str):
        self.start_batch_btn.setEnabled(True)
        self.cancel_batch_btn.setEnabled(False)
        QMessageBox.critical(self, "批量转 SRT 失败", msg)

    # ---------- config and persistence ----------
    def collect_settings_snapshot(self) -> dict:
        try:
            self.sync_current_network_profile_detail()
        except Exception:
            pass
        profile = self.get_active_network_profile_dict()
        return {
            "token": profile.get("token", "") if isinstance(profile, dict) else "",
            "cookie": profile.get("cookie", "") if isinstance(profile, dict) else "",
            "csrf": profile.get("csrf", "") if isinstance(profile, dict) else "",
            "user_agent": profile.get("user_agent", "") if isinstance(profile, dict) else "",
            "referer": profile.get("referer", "") if isinstance(profile, dict) else "",
            "proxy": profile.get("proxy", "") if isinstance(profile, dict) else "",
            "online_search_endpoint": profile.get("endpoint", "") if isinstance(profile, dict) else "",
            "online_search_method": profile.get("method", "GET") if isinstance(profile, dict) else "GET",
            "online_search_kind": profile.get("kind", "generic_api") if isinstance(profile, dict) else "generic_api",
            "online_profile_name": profile.get("name", "") if isinstance(profile, dict) else "",
            "online_timeout": self.online_timeout_spin.value() if hasattr(self, "online_timeout_spin") else self.settings.get("online_timeout", 25),
            "ai_timeout": self.settings.get("ai_timeout", 60),
        }

    def get_settings_save_path(self) -> str:
        return str(SETTINGS_PATH)

    def save_all_settings_quiet(self):
        try:
            self.save_all_settings(silent=True)
        except Exception as e:
            self.append_log(f"设置自动保存失败：{e}") if hasattr(self, "append_log") else None

    def schedule_settings_autosave(self, *_args):
        timer = getattr(self, "_settings_autosave_timer", None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self.save_all_settings_quiet)
            self._settings_autosave_timer = timer
        timer.start(300)

    def _load_settings_to_ui(self):
        if hasattr(self, "theme_combo"):
            self.theme_combo.setCurrentText(self.settings.get("theme_name", "曜石金奢"))
        if hasattr(self, "ui_scale_combo"):
            self.ui_scale_combo.setCurrentText(normalize_ui_scale_text(self.settings.get("ui_scale_percent", "100%")))
            self.on_ui_scale_changed(self.ui_scale_combo.currentText())
        if hasattr(self, "palette_combo"):
            self.palette_combo.setCurrentText(self.settings.get("palette_name", self.palette_combo.currentText() if self.palette_combo.count() else ""))
        roots = self.settings.get("local_roots", [])
        if isinstance(roots, list):
            for root in roots:
                self.root_list.addItem(root)
        self.remember_cb.setChecked(bool(self.settings.get("remember", True)))
        self.online_timeout_spin.setValue(int(self.settings.get("online_timeout", 25) or 25))
        if hasattr(self, 'notes_dir_edit'):
            self.notes_dir_edit.setText(self.settings.get('notes_output_dir', str(self._notes_output_dir())))
        if hasattr(self, 'vocab_dir_edit'):
            self.vocab_dir_edit.setText(self.settings.get('vocab_output_dir', str(self._vocab_output_dir())))
        if hasattr(self, 'download_dir_edit'):
            self.download_dir_edit.setText(self.settings.get("download_dir", str(DOWNLOAD_DIR)))
        if hasattr(self, "download_thread_spin"):
            self.download_thread_spin.setValue(int(self.settings.get("download_threads", 3) or 3))
        if hasattr(self, 'online_limit_spin'):
            self.online_limit_spin.setValue(int(self.settings.get('online_default_limit', 20) or 20))
        self.order_mode = self.settings.get("order_mode", "playlist")
        self.state.order_mode = self.order_mode
        if hasattr(self, 'loop_mode_combo'):
            self.loop_mode_combo.setCurrentText(self.settings.get('loop_mode', 'single'))
        if hasattr(self, 'loop_count_spin'):
            self.loop_count_spin.setValue(int(self.settings.get('loop_count', 1) or 1))
        if hasattr(self, 'view_mode_combo'):
            self.view_mode_combo.setCurrentText(self.settings.get('view_mode', self.view_mode_combo.currentText()))
        self.ai_send_limit_spin.setValue(int(self.settings.get("ai_send_limit", 20) or 20))
        self.populate_network_profile_table()
        self.populate_ai_target_table()
        self.populate_link_tree(self.settings.get("link_tags", DEFAULT_LINK_TAGS))
        dict_sources = self.settings.get("dictionary_sources", [
            "https://www.vocabulary.com/dictionary/{query}",
            "https://dictionary.cambridge.org/dictionary/english-chinese-simplified/{query}",
            ""
        ])
        if hasattr(self, "dict_source_edit_1"):
            edits = [self.dict_source_edit_1, self.dict_source_edit_2, self.dict_source_edit_3]
            for i, edit in enumerate(edits):
                edit.setText(dict_sources[i] if i < len(dict_sources) else "")
        elif hasattr(self, "dict_source_table"):
            self.dict_source_table.setRowCount(0)
            for src in dict_sources:
                r = self.dict_source_table.rowCount()
                self.dict_source_table.insertRow(r)
                self.dict_source_table.setItem(r, 0, QTableWidgetItem("单词"))
                self.dict_source_table.setItem(r, 1, QTableWidgetItem(src))
        if hasattr(self, "play_speed_combo"):
            self.play_speed_combo.setCurrentText(self.settings.get("play_speed", "1.0x"))
        self.search_visible_columns = self.settings.get("search_visible_columns", self.search_visible_columns)
        self.refresh_online_profile_combo()
        self.apply_search_column_visibility()
        self.subtitle_display_mode = self.settings.get('subtitle_display_mode', getattr(self, 'subtitle_display_mode', 'dual'))
        self.floating_subtitle_enabled = bool(self.settings.get('floating_subtitle_enabled', getattr(self, 'floating_subtitle_enabled', False)))
        try:
            self.apply_local_font_settings_to_widgets()
        except Exception:
            pass
        try:
            self.apply_subtitle_style_settings()
        except Exception:
            pass
        # 【关键修复】把保存的主题和配色设置到下拉框，并立即应用
        saved_theme = self.settings.get("theme_name", "曜石金奢").strip()
        saved_palette = self.settings.get("palette_name", "").strip()

        if hasattr(self, 'theme_combo') and saved_theme:
            index = self.theme_combo.findText(saved_theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

        if hasattr(self, 'palette_combo') and saved_palette:
            index = self.palette_combo.findText(saved_palette)
            if index >= 0:
                self.palette_combo.setCurrentIndex(index)

        # 立即应用保存的主题和配色
        if saved_theme:
            self.apply_theme(saved_theme, saved_palette if saved_palette else None)

        QTimer.singleShot(0, self.apply_saved_ui_state)

    def save_all_settings(self, silent: bool = False):
        """增强版保存：确保主题、配色、网络配置全部正确保存"""
        try:
            # 先同步当前正在编辑的网络配置
            try:
                self.sync_current_network_profile_detail()
            except Exception:
                pass

            # 创建可安全保存的副本
            data = {}
            for k, v in self.settings.items():
                try:
                    json.dumps({k: v})   # 测试是否可JSON序列化
                    data[k] = v
                except (TypeError, ValueError):
                    data[k] = str(v)     # 无法序列化时转为字符串

            # 调试输出（方便你查看是否真的保存了配色）
            print(f"[SAVE] 正在保存设置 → 主题: {data.get('theme_name')} | 配色: {data.get('palette_name')}")

            if "network_profiles" in data:
                print(f"[SAVE] 网络配置数量: {len(data['network_profiles'])}")

            # 写入文件
            save_settings(data)
            self.settings = data   # 同步回内存

            if not silent:
                QMessageBox.information(self, "保存成功", 
                                      f"配置已保存！\n"
                                      f"主题: {data.get('theme_name', '未设置')}\n"
                                      f"配色: {data.get('palette_name', '未设置')}")
            return True

        except Exception as e:
            print(f"✗ save_all_settings 出错: {e}")
            if not silent:
                QMessageBox.critical(self, "保存失败", f"保存设置失败：{e}")
            return False

    def import_txt_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入 TXT/JSON 配置", "", "Config (*.txt *.json);;All Files (*)")
        if not path:
            return
        raw = Path(path).read_text(encoding="utf-8", errors="ignore")
        pairs = {}
        try:
            if path.lower().endswith('.json'):
                data = json.loads(raw)
            else:
                data = None
        except Exception:
            data = None
        if data is None:
            for line in raw.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                elif ':' in line:
                    k, v = line.split(':', 1)
                else:
                    continue
                pairs[k.strip().lower()] = v.strip()
        current = self.config_tabs.currentIndex() if hasattr(self, 'config_tabs') else 0
        if current == 0:
            if 'remember' in pairs:
                self.remember_cb.setChecked(pairs['remember'] in ('1','true','yes','是'))
            if 'online_timeout' in pairs:
                try: self.online_timeout_spin.setValue(int(pairs['online_timeout']))
                except Exception: pass
            if 'theme_name' in pairs and hasattr(self,'theme_combo'):
                self.theme_combo.setCurrentText(pairs['theme_name'])
            if 'palette_name' in pairs and hasattr(self,'palette_combo'):
                self.palette_combo.setCurrentText(pairs['palette_name'])
            if 'ui_scale_percent' in pairs and hasattr(self,'ui_scale_combo'):
                self.ui_scale_combo.setCurrentText(pairs['ui_scale_percent'])
            self._set_config_status('基础配置已导入')
        elif current == 1:
            rows = self.get_table_selected_rows(self.net_profile_table)
            idx = rows[0] if rows else 0
            if idx >= len(self.network_profiles):
                self.add_network_profile()
                idx = len(self.network_profiles)-1
            prof = self.network_profiles[idx]
            if isinstance(data, dict):
                prof.update(data)
            else:
                mapping = {'name':'name','kind':'kind','enabled':'enabled','default':'is_default','is_default':'is_default','endpoint':'endpoint','method':'method','note':'note','token':'token','cookie':'cookie','csrf':'csrf','user_agent':'user_agent','referer':'referer','proxy':'proxy'}
                for k,v in pairs.items():
                    if k in mapping:
                        prof[mapping[k]] = v
            self.populate_network_profile_table(); self.select_network_profile_row(idx)
            self._set_config_status('联网配置已导入')
        elif current == 2:
            if isinstance(data, list):
                self.ai_targets = [AITarget(**x) for x in data if isinstance(x, dict)]
            else:
                rows = self.get_table_selected_rows(self.ai_target_table)
                idx = rows[0] if rows else 0
                if idx >= len(self.ai_targets):
                    self.ai_targets.append(AITarget(name='新对象'))
                    idx = len(self.ai_targets)-1
                t = self.ai_targets[idx]
                t.name = pairs.get('name', t.name)
                t.kind = pairs.get('kind', t.kind)
                t.endpoint = pairs.get('endpoint', t.endpoint)
                t.method = pairs.get('method', t.method)
                if 'enabled' in pairs:
                    t.enabled = pairs['enabled'] in ('1','true','yes','是')
                headers = {}
                for hk in ['authorization','cookie','content-type','x-api-key','referer','user-agent']:
                    if hk in pairs:
                        headers[hk.title() if hk!='content-type' else 'Content-Type'] = pairs[hk]
                if headers:
                    t.headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            self.populate_ai_target_table(); self.refresh_ai_target_combo(); self._set_config_status('AI对象已导入')
        else:
            if isinstance(data, dict):
                self.populate_link_tree(data)
            else:
                tree = {}
                for line in raw.splitlines():
                    line=line.strip()
                    if not line or line.startswith('#'): continue
                    parts=[x.strip() for x in line.split('|')]
                    if len(parts)>=3:
                        cat,name,url = parts[:3]
                        tree.setdefault(cat,{})[name]=url
                if tree:
                    self.populate_link_tree(tree)
            self._set_config_status('链接标签已导入')

    def _set_config_status(self, text: str):
        if hasattr(self, 'config_status_label'):
            self.config_status_label.setText(text)

    def apply_config_to_runtime(self):
        """配置中心 - 应用到运行中（已优化：自动保存 + 立即生效）"""
        self.sync_current_network_profile_detail()
        self.pull_ai_targets_from_table(silent=True)
        self.refresh_online_profile_combo()
        self.refresh_ai_target_combo()
        
        # ==================== 优化点：自动保存 + 友好提示 ====================
        self.save_all_settings(silent=True)   # 自动保存所有配置
        
        # 刷新网络相关UI
        if hasattr(self, "online_profile_combo"):
            self.online_profile_combo.blockSignals(True)
            self.refresh_online_profile_combo()
            self.online_profile_combo.blockSignals(False)
        
        self._set_config_status('✅ 已成功应用并保存！现在可以去联网模式测试网络配置是否生效。')
        
        # 可选：弹出确认对话框
        if not hasattr(self, '_apply_config_suppress_msg'):
            QMessageBox.information(self, "配置应用成功", 
                                  "联网配置已应用并保存。\n\n"
                                  "你可以立即切换到【联网模式】标签页进行搜索测试。\n"
                                  "如果需要 Token/Cookie 等鉴权，请确保已填写完整。")
            self._apply_config_suppress_msg = True  # 只弹一次

    def export_current_config(self):
        path, _ = QFileDialog.getSaveFileName(self, '导出配置', '', 'JSON (*.json);;Text (*.txt)')
        if not path:
            return
        current = self.config_tabs.currentIndex() if hasattr(self, 'config_tabs') else 0
        data = {}
        if current == 0:
            data = {
                'remember': self.remember_cb.isChecked(),
                'online_timeout': self.online_timeout_spin.value(),
                'theme_name': self.theme_combo.currentText() if hasattr(self,'theme_combo') else '',
                'palette_name': self.palette_combo.currentText() if hasattr(self,'palette_combo') else '',
                'ui_scale_percent': self.ui_scale_combo.currentText() if hasattr(self,'ui_scale_combo') else '100%',
            }
        elif current == 1:
            rows = self.get_table_selected_rows(self.net_profile_table)
            idx = rows[0] if rows else 0
            data = self.network_profiles[idx] if self.network_profiles else {}
        elif current == 2:
            rows = self.get_table_selected_rows(self.ai_target_table)
            idx = rows[0] if rows else 0
            data = asdict(self.ai_targets[idx]) if self.ai_targets and idx < len(self.ai_targets) else {}
        else:
            data = self.export_link_tree()
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        self._set_config_status(f'已导出：{path}')

    def _collect_dictionary_sources(self):
        if hasattr(self, 'dict_source_table'):
            vals = []
            for r in range(self.dict_source_table.rowCount()):
                it = self.dict_source_table.item(r, 1)
                if it and it.text().strip():
                    vals.append(it.text().strip())
            return vals
        vals = []
        for name in ['dict_source_edit_1', 'dict_source_edit_2', 'dict_source_edit_3']:
            w = getattr(self, name, None)
            if w is not None:
                vals.append(w.text().strip())
        return vals

    def _load_network_profiles(self) -> List[dict]:
        data = self.settings.get("network_profiles")
        if isinstance(data, list) and data:
            return data
        legacy = {
            "name": "旧版导入",
            "kind": "generic_api",
            "endpoint": self.settings.get("online_search_endpoint", ""),
            "method": self.settings.get("online_search_method", "GET"),
            "enabled": True,
            "is_default": True,
            "token": self.settings.get("token", ""),
            "cookie": self.settings.get("cookie", ""),
            "csrf": self.settings.get("csrf", ""),
            "user_agent": self.settings.get("user_agent", "Mozilla/5.0"),
            "referer": self.settings.get("referer", ""),
            "proxy": self.settings.get("proxy", ""),
            "note": "从旧版单配置迁移。",
        }
        profiles = default_network_profiles()
        if legacy["endpoint"]:
            profiles.insert(0, legacy)
            for i, p in enumerate(profiles):
                p["is_default"] = (i == 0)
        return profiles

    def refresh_online_profile_combo(self):
        if not hasattr(self, "online_profile_combo"):
            return
        current = str((self.online_profile_combo.currentData() if self.online_profile_combo.count() > 0 else '') or self.settings.get("active_network_profile", "") or '').strip()
        self.online_profile_combo.blockSignals(True)
        self.online_profile_combo.clear()
        for prof in self.network_profiles:
            if prof.get("enabled", True):
                profile_name = str(prof.get("name", "") or "").strip()
                label = f"{profile_name}｜{prof.get('kind','')}"
                self.online_profile_combo.addItem(label, profile_name)
        if self.online_profile_combo.count() > 0:
            idx = 0
            if current:
                for i in range(self.online_profile_combo.count()):
                    if str(self.online_profile_combo.itemData(i) or '').strip() == current:
                        idx = i
                        break
            else:
                for prof in self.network_profiles:
                    if prof.get("enabled", True) and prof.get("is_default", False):
                        target_name = str(prof.get("name", "") or "").strip()
                        for j in range(self.online_profile_combo.count()):
                            if str(self.online_profile_combo.itemData(j) or '').strip() == target_name:
                                idx = j
                                break
                        break
            self.online_profile_combo.setCurrentIndex(idx)
            self.settings["active_network_profile"] = str(self.online_profile_combo.currentData() or '').strip()
        self.online_profile_combo.blockSignals(False)

    def populate_network_profile_table(self):
        if not hasattr(self, "net_profile_table"):
            return
        self.net_profile_table.setRowCount(0)
        for prof in self.network_profiles:
            r = self.net_profile_table.rowCount()
            self.net_profile_table.insertRow(r)
            self.net_profile_table.setItem(r, 0, QTableWidgetItem("是" if prof.get("is_default", False) else "否"))
            self.net_profile_table.setItem(r, 1, QTableWidgetItem(prof.get("name", "")))
            self.net_profile_table.setItem(r, 2, QTableWidgetItem(prof.get("kind", "generic_api")))
            self.net_profile_table.setItem(r, 3, QTableWidgetItem("是" if prof.get("enabled", True) else "否"))
            self.net_profile_table.setItem(r, 4, QTableWidgetItem(prof.get("note", "")))
        if self.net_profile_table.rowCount() > 0 and not self.get_table_selected_rows(self.net_profile_table):
            self.net_profile_table.selectRow(0)
        self.on_network_profile_row_changed()
        self.refresh_online_profile_combo()

    def _current_network_profile_index(self) -> int:
        rows = self.get_table_selected_rows(self.net_profile_table) if hasattr(self, "net_profile_table") else []
        return rows[0] if rows else -1

    def _load_network_profile_detail(self, idx: int):
        if not (0 <= idx < len(self.network_profiles)):
            return
        self._network_profile_sync_guard = True
        prof = self.network_profiles[idx]
        self.net_name_edit.setText(prof.get("name", ""))
        self.net_kind_combo.setCurrentText(prof.get("kind", "generic_api"))
        self.net_enabled_combo.setCurrentText("是" if prof.get("enabled", True) else "否")
        self.net_default_combo.setCurrentText("是" if prof.get("is_default", False) else "否")
        self.net_endpoint_edit.setText(prof.get("endpoint", ""))
        self.net_method_combo.setCurrentText(prof.get("method", "GET"))
        self.net_note_edit.setText(prof.get("note", ""))
        self.token_edit.setPlainText(prof.get("token", ""))
        self.cookie_edit.setPlainText(prof.get("cookie", ""))
        self.csrf_edit.setText(prof.get("csrf", ""))
        self.user_agent_edit.setText(prof.get("user_agent", "Mozilla/5.0"))
        self.referer_edit.setText(prof.get("referer", ""))
        self.proxy_edit.setText(prof.get("proxy", ""))
        self._network_profile_sync_guard = False
        self.update_network_profile_kind_ui()

    def update_network_profile_kind_ui(self):
        kind = self.net_kind_combo.currentText() if hasattr(self, "net_kind_combo") else "generic_api"
        need_auth = kind in {"playphrase_token", "playphrase_auth", "generic_api"}
        if hasattr(self, "net_auth_box"):
            self.net_auth_box.setVisible(need_auth)
        if kind == "playphrase_token":
            if hasattr(self, "net_endpoint_edit") and not self.net_endpoint_edit.text().strip():
                self.net_endpoint_edit.setText("https://www.playphrase.me/api/v1/phrases/search")
            if hasattr(self, "referer_edit") and not self.referer_edit.text().strip():
                self.referer_edit.setText("https://www.playphrase.me/")
            if hasattr(self, "user_agent_edit") and not self.user_agent_edit.text().strip():
                self.user_agent_edit.setText("Mozilla/5.0")
            if hasattr(self, "net_note_edit") and not self.net_note_edit.text().strip():
                self.net_note_edit.setText("Token 直登模式")
            if hasattr(self, "net_auth_box"):
                self.net_auth_box.setTitle("Token 直登（优先填写 Token；Cookie / CSRF 可留空）")
        elif kind == "playphrase_free":
            if hasattr(self, "net_endpoint_edit") and not self.net_endpoint_edit.text().strip():
                self.net_endpoint_edit.setText("https://www.playphrase.me/#/search?q={query}")
            if hasattr(self, "net_auth_box"):
                self.net_auth_box.setTitle("登录 / 鉴权（当前模式通常不需要）")
        elif kind == "direct_web":
            if hasattr(self, "net_auth_box"):
                self.net_auth_box.setTitle("网页直连（通常不需要鉴权）")
        else:
            if hasattr(self, "net_auth_box"):
                self.net_auth_box.setTitle("登录 / 鉴权（按需填写）")

    def apply_token_profile_template(self):
        idx = self._current_network_profile_index()
        if not (0 <= idx < len(self.network_profiles)):
            return
        self.net_kind_combo.setCurrentText("playphrase_token")
        self.net_method_combo.setCurrentText("GET")
        self.net_endpoint_edit.setText("https://www.playphrase.me/api/v1/phrases/search")
        self.referer_edit.setText("https://www.playphrase.me/")
        if not self.user_agent_edit.text().strip():
            self.user_agent_edit.setText("Mozilla/5.0")
        if not self.net_name_edit.text().strip() or self.net_name_edit.text().strip().startswith("新配置"):
            self.net_name_edit.setText("PlayPhrase Token直登")
        self.net_note_edit.setText("Token 直登模式")
        self.net_enabled_combo.setCurrentText("是")
        self.update_network_profile_kind_ui()
        self.sync_current_network_profile_detail()
        self._set_config_status("已切换为 Token 直登模板")

    def clear_network_auth_fields(self):
        self.token_edit.setPlainText("")
        self.cookie_edit.setPlainText("")
        self.csrf_edit.setText("")
        self.sync_current_network_profile_detail()
        self._set_config_status("已清空鉴权字段")

    def on_active_online_profile_changed(self, *_args):
        try:
            self.settings["active_network_profile"] = str(self.online_profile_combo.currentData() or self.online_profile_combo.currentText().split("｜")[0]).strip()
        except Exception:
            self.settings["active_network_profile"] = ""
        self.schedule_settings_autosave()

    def sync_current_network_profile_detail(self):
        """同步当前网络配置表单到 self.settings"""
        try:
            selected = self.net_profile_table.selectedIndexes()
            if not selected:
                return
            
            idx = selected[0].row()
            profiles = self.settings.get("network_profiles", [])
            
            if 0 <= idx < len(profiles):
                profile = profiles[idx]
                
                # 同步所有字段
                profile["name"] = self.net_name_edit.text().strip()
                profile["enabled"] = self.net_enabled_combo.currentText() == "是"
                profile["is_default"] = self.net_default_combo.currentText() == "是"
                profile["kind"] = self.net_kind_combo.currentText()
                profile["endpoint"] = self.net_endpoint_edit.text().strip()
                profile["method"] = self.net_method_combo.currentText()
                profile["note"] = self.net_note_edit.text().strip()
                profile["proxy"] = self.proxy_edit.text().strip()

                # 认证信息
                auth = profile.setdefault("auth", {})
                auth["token"] = self.token_edit.toPlainText().strip()
                auth["cookie"] = self.cookie_edit.toPlainText().strip()
                auth["csrf"] = self.csrf_edit.text().strip()
                auth["user_agent"] = self.user_agent_edit.text().strip()
                auth["referer"] = self.referer_edit.text().strip()

                print(f"✓ 网络配置已同步: {profile.get('name', '未命名')}")
                
        except Exception as e:
            print(f"[ERROR] sync_current_network_profile_detail: {e}")
            traceback.print_exc()
    

    def on_network_profile_row_changed(self):
        idx = self._current_network_profile_index()
        if idx >= 0:
            self._load_network_profile_detail(idx)

    def add_network_profile(self):
        self.sync_current_network_profile_detail()
        self.network_profiles.append({
            "name": f"新配置{len(self.network_profiles)+1}",
            "kind": "playphrase_token",
            "endpoint": "https://www.playphrase.me/api/v1/phrases/search",
            "method": "GET",
            "enabled": True,
            "is_default": False,
            "token": "",
            "cookie": "",
            "csrf": "",
            "user_agent": "Mozilla/5.0",
            "referer": "https://www.playphrase.me/",
            "proxy": "",
            "note": "Token 直登模式",
        })
        self.populate_network_profile_table()
        self.net_profile_table.selectRow(self.net_profile_table.rowCount() - 1)

    def remove_network_profile(self):
        idx = self._current_network_profile_index()
        if not (0 <= idx < len(self.network_profiles)):
            return
        del self.network_profiles[idx]
        if not self.network_profiles:
            self.network_profiles = default_network_profiles()
        if not any(p.get("is_default", False) for p in self.network_profiles):
            self.network_profiles[0]["is_default"] = True
        self.populate_network_profile_table()

    def clone_network_profile(self):
        idx = self._current_network_profile_index()
        if not (0 <= idx < len(self.network_profiles)):
            return
        self.sync_current_network_profile_detail()
        prof = dict(self.network_profiles[idx])
        prof["name"] = prof.get("name", "配置") + " - 副本"
        prof["is_default"] = False
        self.network_profiles.insert(idx + 1, prof)
        self.populate_network_profile_table()
        self.net_profile_table.selectRow(idx + 1)

    def set_selected_network_profile_default(self):
        idx = self._current_network_profile_index()
        if not (0 <= idx < len(self.network_profiles)):
            return
        for i, p in enumerate(self.network_profiles):
            p["is_default"] = (i == idx)
        self.net_default_combo.setCurrentText("是")
        self.populate_network_profile_table()
        self.net_profile_table.selectRow(idx)

    def get_active_network_profile_dict(self) -> dict:
        selected_name = ""
        if hasattr(self, "online_profile_combo") and self.online_profile_combo.count() > 0:
            selected_name = str(self.online_profile_combo.currentData() or self.online_profile_combo.currentText().split("｜")[0]).strip()
        if not selected_name:
            selected_name = str(self.settings.get("active_network_profile", "") or "").strip()
        if selected_name:
            for prof in self.network_profiles:
                if str(prof.get("name", "") or "").strip() == selected_name:
                    return dict(prof)
        idx = self._current_network_profile_index() if hasattr(self, '_current_network_profile_index') else -1
        if 0 <= idx < len(self.network_profiles):
            return dict(self.network_profiles[idx])
        for prof in self.network_profiles:
            if prof.get("enabled", True) and prof.get("is_default", False):
                return dict(prof)
        return dict(self.network_profiles[0]) if self.network_profiles else {}

    def populate_link_tree(self, data: dict):
        self.link_tree.clear()
        for cat, mapping in data.items():
            parent = QTreeWidgetItem([cat, ""])
            self.link_tree.addTopLevelItem(parent)
            if isinstance(mapping, dict):
                for name, url in mapping.items():
                    parent.addChild(QTreeWidgetItem([name, url]))
            parent.setExpanded(True)

    def export_link_tree(self) -> dict:
        out = {}
        for i in range(self.link_tree.topLevelItemCount()):
            top = self.link_tree.topLevelItem(i)
            out[top.text(0)] = {}
            for j in range(top.childCount()):
                child = top.child(j)
                out[top.text(0)][child.text(0)] = child.text(1)
        return out

    def add_link_category(self):
        name, ok = QInputDialog.getText(self, "新增分类", "分类名称：")
        if ok and name.strip():
            self.link_tree.addTopLevelItem(QTreeWidgetItem([name.strip(), ""]))

    def add_link_item(self):
        current = self.link_tree.currentItem()
        parent = current if current and current.parent() is None else (current.parent() if current else None)
        if not parent:
            QMessageBox.information(self, "提示", "请先选中一个分类")
            return
        name, ok = QInputDialog.getText(self, "新增链接", "名称：")
        if not ok or not name.strip():
            return
        url, ok = QInputDialog.getText(self, "新增链接", "URL：")
        if not ok or not url.strip():
            return
        parent.addChild(QTreeWidgetItem([name.strip(), url.strip()]))
        parent.setExpanded(True)

    def remove_link_item(self):
        current = self.link_tree.currentItem()
        if not current:
            return
        parent = current.parent()
        if parent:
            parent.removeChild(current)
        else:
            idx = self.link_tree.indexOfTopLevelItem(current)
            self.link_tree.takeTopLevelItem(idx)

    def open_selected_link(self):
        current = self.link_tree.currentItem()
        if current and current.parent() is not None and current.text(1):
            QDesktopServices.openUrl(QUrl(current.text(1)))

    # ---------- misc ----------
    def pick_dir(self, line_edit: QLineEdit):
        d = QFileDialog.getExistingDirectory(self, "选择目录")
        if d:
            line_edit.setText(d)

    def pick_file(self, line_edit: QLineEdit, title: str, flt: str):
        path, _ = QFileDialog.getOpenFileName(self, title, "", flt)
        if path:
            line_edit.setText(path)

    def _safe_filename(self, text: str) -> str:
        text = re.sub(r"[\\/:*?\"<>|]+", "_", text)
        text = re.sub(r"\s+", "_", text).strip("_")
        return text or "item"


    def _build_ai_tab(self):
        outer = QVBoxLayout(self.ai_tab)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("主题"))
        self.ai_theme_combo = QComboBox()
        self.ai_theme_combo.addItems(list_theme_names())
        self.ai_theme_combo.setCurrentText(self.settings.get("theme_name", "哲风壁纸风格版"))
        toolbar.addWidget(self.ai_theme_combo)
        toolbar.addWidget(QLabel("配色"))
        self.ai_palette_combo = QComboBox()
        self.ai_palette_combo.addItems(list_palette_names())
        self.ai_palette_combo.setCurrentText(self.settings.get("palette_name", self.palette_combo.currentText() if hasattr(self, "palette_combo") else list_palette_names()[0]))
        toolbar.addWidget(self.ai_palette_combo)
        toolbar.addSpacing(12)
        self.ai_analyze_from_current_btn = QPushButton("载入当前内容")
        self.ai_add_note_btn = QPushButton("加入笔记")
        self.ai_add_vocab_btn = QPushButton("加入生词本")
        toolbar.addWidget(self.ai_analyze_from_current_btn)
        toolbar.addWidget(self.ai_add_note_btn)
        toolbar.addWidget(self.ai_add_vocab_btn)
        toolbar.addStretch()
        outer.addLayout(toolbar)

        # 兼容旧主链：保留 AI 接收对象 / 发送预览 / 返回框，避免 _load_settings_to_ui 和 send_preview_to_ai 崩溃
        compat_box = QGroupBox("AI接收与发送（兼容旧链路）")
        compat_layout = QVBoxLayout(compat_box)
        row = QHBoxLayout()
        self.ai_target_combo = QComboBox()
        self.ai_send_limit_spin = QSpinBox()
        self.ai_send_limit_spin.setRange(1, 100)
        self.ai_send_limit_spin.setValue(int(self.settings.get("ai_send_limit", 20) or 20))
        self.ai_send_btn = QPushButton("发送当前选择到 AI")
        row.addWidget(QLabel("接收对象"))
        row.addWidget(self.ai_target_combo)
        row.addWidget(QLabel("默认上限"))
        row.addWidget(self.ai_send_limit_spin)
        row.addWidget(self.ai_send_btn)
        row.addStretch()
        compat_layout.addLayout(row)
        self.ai_input_preview = QPlainTextEdit()
        self.ai_input_preview.setPlaceholderText("这里预览即将发送到 AI 的文本（默认原句全文合并发送）。")
        self.ai_output = QPlainTextEdit()
        self.ai_output.setReadOnly(True)
        compat_split = QSplitter(Qt.Horizontal)
        compat_split.addWidget(self.ai_input_preview)
        compat_split.addWidget(self.ai_output)
        compat_split.setSizes([520, 680])
        compat_layout.addWidget(QLabel("发送预览 / AI返回"))
        compat_layout.addWidget(compat_split)
        outer.addWidget(compat_box, 0)

        self.ai_analysis_panel = AIAnalysisWorkbench()
        outer.addWidget(self.ai_analysis_panel, 1)

        self.refresh_ai_target_combo()
        self.ai_theme_combo.currentTextChanged.connect(lambda *_: self._sync_theme_from_ai())
        self.ai_palette_combo.currentTextChanged.connect(lambda *_: self._sync_theme_from_ai())
        self.ai_analyze_from_current_btn.clicked.connect(self.load_current_text_to_ai_analysis)
        self.ai_add_note_btn.clicked.connect(self.add_ai_analysis_to_notes)
        self.ai_add_vocab_btn.clicked.connect(self.add_ai_analysis_to_vocab)
        self.ai_send_btn.clicked.connect(self.send_preview_to_ai)

    def _sync_theme_from_ai(self):
        if hasattr(self, "theme_combo"):
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentText(self.ai_theme_combo.currentText())
            self.theme_combo.blockSignals(False)
        if hasattr(self, "palette_combo"):
            self.palette_combo.blockSignals(True)
            self.palette_combo.setCurrentText(self.ai_palette_combo.currentText())
            self.palette_combo.blockSignals(False)
        self.apply_selected_theme()

    def apply_selected_theme(self, *_args):
        theme_name = self.theme_combo.currentText() if hasattr(self, "theme_combo") else self.settings.get("theme_name", "曜石金奢")
        palette_name = self.palette_combo.currentText() if hasattr(self, "palette_combo") else self.settings.get("palette_name", "")

        self.apply_theme(theme_name, palette_name)

        # === 关键：强制保存当前主题和配色 ===
        self.settings["theme_name"] = theme_name
        self.settings["palette_name"] = palette_name

        self.schedule_settings_autosave()   # 立即触发保存

    def _build_search_menu(self):
        menu = QMenu(self)
        sort_menu = menu.addMenu("排序方式")
        sort_group = []
        for sort_name in ["文件名", "时间", "匹配度"]:
            act = QAction(sort_name, self)
            act.setCheckable(True)
            act.setChecked(self.local_result_sort_combo.currentText() == sort_name)
            act.triggered.connect(lambda checked=False, name=sort_name: self._set_local_sort(name))
            sort_menu.addAction(act)
            sort_group.append(act)
        field_menu = menu.addMenu("显示字段")
        self._search_field_actions = {}
        for idx, name in enumerate(SEARCH_RESULT_COLUMNS, start=1):
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(bool(self.search_visible_columns.get(name, True)))
            act.triggered.connect(lambda checked, col=idx, n=name: self._toggle_search_column(col, n, checked))
            field_menu.addAction(act)
            self._search_field_actions[name] = act
        menu.addSeparator()
        act_copy = QAction("复制选中项", self)
        act_copy.triggered.connect(lambda: self.copy_items_text(self.resolve_action_items(self.local_results, self.local_result_table)))
        act_note = QAction("加入笔记", self)
        act_note.triggered.connect(lambda: self.add_note_to_items(self.resolve_action_items(self.local_results, self.local_result_table)))
        act_ai = QAction("发送AI", self)
        act_ai.triggered.connect(lambda: self.send_items_to_ai(self.resolve_action_items(self.local_results, self.local_result_table)))
        for a in [act_copy, act_note, act_ai]:
            menu.addAction(a)
        menu.addSeparator()
        act_font = QAction("搜索区字体", self)
        act_font.triggered.connect(lambda: self.open_local_font_settings("search_options"))
        menu.addAction(act_font)
        return menu

    def _build_playlist_menu(self):
        menu = QMenu(self)
        act_slice = QAction("播放切片", self)
        act_slice.triggered.connect(lambda: self.start_playlist_play("slice"))
        act_video = QAction("播放视频", self)
        act_video.triggered.connect(lambda: self.start_playlist_play("video"))
        act_full = QAction("全屏观影", self)
        act_full.triggered.connect(self.start_full_view)
        act_all = QAction("全选", self)
        act_all.triggered.connect(lambda: self.set_checked_for_table(self.playlist_table, self.state.playlist, True))
        act_inv = QAction("反选", self)
        act_inv.triggered.connect(lambda: self.invert_checked_for_table(self.playlist_table, self.state.playlist))
        act_clear = QAction("清空播放列表", self)
        act_clear.triggered.connect(self.clear_playlist)
        for a in [act_slice, act_video, act_full, act_all, act_inv, act_clear]:
            menu.addAction(a)
        menu.addSeparator()
        field_menu = menu.addMenu("字段选项")
        self._playlist_field_actions = {}
        for idx, name in enumerate(SEARCH_RESULT_COLUMNS, start=1):
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(bool(self.search_visible_columns.get(name, True)))
            act.triggered.connect(lambda checked, col=idx, n=name: self._toggle_search_column(col, n, checked))
            field_menu.addAction(act)
            self._playlist_field_actions[name] = act
        menu.addSeparator()
        act_font = QAction("播放列表字体", self)
        act_font.triggered.connect(lambda: self.open_local_font_settings("playlist_options"))
        menu.addAction(act_font)
        return menu

    def _set_local_sort(self, sort_name: str):
        self.local_result_sort_combo.setCurrentText(sort_name)
        if self.local_results:
            self.start_local_search()

    def _toggle_search_column(self, col: int, name: str, checked: bool):
        self.search_visible_columns[name] = bool(checked)
        self.apply_search_column_visibility()
        try:
            self.save_all_settings(silent=True)
        except Exception:
            pass

    def apply_search_column_visibility(self):
        if not hasattr(self, "local_result_table"):
            return
        for idx, name in enumerate(SEARCH_RESULT_COLUMNS, start=1):
            hidden = not bool(self.search_visible_columns.get(name, True))
            if hasattr(self, "local_result_table"):
                self.local_result_table.setColumnHidden(idx, hidden)
            if hasattr(self, "online_result_table"):
                self.online_result_table.setColumnHidden(idx, hidden)
            if hasattr(self, "playlist_table"):
                self.playlist_table.setColumnHidden(idx, hidden)
        if hasattr(self, "_search_field_actions"):
            for name, act in self._search_field_actions.items():
                act.blockSignals(True)
                act.setChecked(bool(self.search_visible_columns.get(name, True)))
                act.blockSignals(False)
        if hasattr(self, "_playlist_field_actions"):
            for name, act in self._playlist_field_actions.items():
                act.blockSignals(True)
                act.setChecked(bool(self.search_visible_columns.get(name, True)))
                act.blockSignals(False)

    def _toggle_group_row(self, layout):
        if layout is None:
            return
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if w:
                w.setVisible(not w.isVisible())

    def _connect_local_signals(self):
        self.add_root_btn.clicked.connect(self.add_root_path)
        self.source_toggle_btn.clicked.connect(self.toggle_local_source_box)
        self.remove_root_btn.clicked.connect(self.remove_selected_root)
        self.clear_root_btn.clicked.connect(self.clear_all_roots)
        self.scan_btn.clicked.connect(self.scan_paths)
        self.local_search_btn.clicked.connect(self.start_local_search)
        self.local_result_select_all_btn.clicked.connect(lambda: self.set_checked_for_table(self.local_result_table, self.local_results, True))
        self.local_result_invert_btn.clicked.connect(lambda: self.invert_checked_for_table(self.local_result_table, self.local_results))
        self.local_result_clear_btn.clicked.connect(self.clear_local_results)
        self.local_add_playlist_btn.clicked.connect(lambda: self.add_items_to_playlist(self.resolve_action_items(self.local_results, self.local_result_table)))
        self.local_copy_btn.clicked.connect(lambda: self.copy_items_text(self.resolve_action_items(self.local_results, self.local_result_table)))
        self.local_note_btn.clicked.connect(lambda: self.add_note_to_items(self.resolve_action_items(self.local_results, self.local_result_table)))
        self.local_ai_btn.clicked.connect(lambda: self.send_items_to_ai(self.resolve_action_items(self.local_results, self.local_result_table)))
        self.local_result_table.cellClicked.connect(lambda r, c: self.on_table_cell_clicked(self.local_result_table, self.local_results, r, c))
        self.local_result_table.itemSelectionChanged.connect(lambda: self.on_table_selection_changed(self.local_result_table, self.local_results, False))
        self.local_result_table.cellDoubleClicked.connect(lambda r, c: self.open_word_action_dialog(self.local_results[r]) if 0 <= r < len(self.local_results) else None)

        self.playlist_select_all_btn.clicked.connect(lambda: self.set_checked_for_table(self.playlist_table, self.state.playlist, True))
        self.playlist_invert_btn.clicked.connect(lambda: self.invert_checked_for_table(self.playlist_table, self.state.playlist))
        self.playlist_clear_btn.clicked.connect(self.clear_playlist)
        self.play_slice_btn.clicked.connect(lambda: self.start_playlist_play("slice"))
        self.play_video_btn.clicked.connect(lambda: self.start_playlist_play("video"))
        self.full_view_btn.clicked.connect(self.start_full_view)
        self.playlist_table.cellClicked.connect(lambda r, c: self.on_table_cell_clicked(self.playlist_table, self.state.playlist, r, c))
        self.playlist_table.itemSelectionChanged.connect(lambda: self.on_table_selection_changed(self.playlist_table, self.state.playlist, True))
        self.playlist_table.cellDoubleClicked.connect(lambda r, c: self.play_single_playlist_item(r))

        self.theme_combo.currentTextChanged.connect(self.apply_selected_theme)
        self.palette_combo.currentTextChanged.connect(self.apply_selected_theme)
        self.play_speed_combo.currentTextChanged.connect(self.change_playback_speed)
        self.left_collapse_btn.clicked.connect(self.toggle_left_workspace)
        self.local_splitter.splitterMoved.connect(self._sync_left_collapse_button)
        self.fullscreen_btn.clicked.connect(self.enter_fullscreen)
        self.restore_layout_btn.clicked.connect(self.restore_layouts)
        if hasattr(self, 'save_settings_btn'):
            self.save_settings_btn.clicked.connect(lambda checked=False: self.save_all_settings(silent=False))
        if hasattr(self, 'ui_scale_combo'):
            self.ui_scale_combo.currentTextChanged.connect(self.on_ui_scale_changed)
            self.ui_scale_combo.currentTextChanged.connect(self.schedule_settings_autosave)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.prev_btn.clicked.connect(lambda: self.navigate_samples(-1))
        self.next_btn.clicked.connect(lambda: self.navigate_samples(1))
        self.player_slider.sliderPressed.connect(self.on_player_slider_pressed)
        self.player_slider.sliderMoved.connect(self.on_player_slider_moved)
        self.player_slider.sliderReleased.connect(self.on_player_slider_released)
        if hasattr(self.player_slider, "jumpTo"):
            self.player_slider.jumpTo.connect(self.on_player_slider_moved)
        if hasattr(self, 'learning_height_slider') and hasattr(self.learning_height_slider, 'valueChanged'):
            self.learning_height_slider.valueChanged.connect(self.on_learning_height_slider_changed)
        if hasattr(self, 'right_splitter'):
            self.right_splitter.splitterMoved.connect(self.sync_learning_height_slider_from_splitter)
        self.copy_line_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.current_item.en if self.current_item else ""))
        self.copy_trans_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.translation_browser.toPlainText()))
        self.lookup_btn.clicked.connect(self.lookup_current_text)
        self.vocab_btn.clicked.connect(self.add_current_to_vocab)
        self.note_btn.clicked.connect(lambda: self.add_note_to_items([self.current_item] if self.current_item else []))
        self.learning_btn.clicked.connect(self.toggle_learning_panel)
        self.clip_btn.clicked.connect(lambda: QMessageBox.information(self, "剪辑工作台", "剪辑工作台已接入口，当前版本提供按钮与后续功能位。"))
        for w in [getattr(self, 'remember_cb', None), getattr(self, 'theme_combo', None), getattr(self, 'palette_combo', None), getattr(self, 'loop_mode_combo', None), getattr(self, 'loop_count_spin', None), getattr(self, 'view_mode_combo', None), getattr(self, 'play_speed_combo', None), getattr(self, 'online_limit_spin', None), getattr(self, 'online_timeout_spin', None)]:
            try:
                if hasattr(w, 'currentTextChanged'):
                    w.currentTextChanged.connect(self.schedule_settings_autosave)
                if hasattr(w, 'valueChanged'):
                    w.valueChanged.connect(self.schedule_settings_autosave)
                if hasattr(w, 'toggled'):
                    w.toggled.connect(self.schedule_settings_autosave)
                if hasattr(w, 'stateChanged'):
                    w.stateChanged.connect(self.schedule_settings_autosave)
            except Exception:
                pass

    # ---------- online tab ----------
    def _build_online_tab(self):
        outer = QVBoxLayout(self.online_tab)
        top = QGroupBox("联网模式")
        top_l = QVBoxLayout(top)
        form = QGridLayout()
        self.online_profile_combo = QComboBox()
        self.online_keyword_edit = QLineEdit(); self.online_keyword_edit.setPlaceholderText("输入关键词 / 句子（联网搜索）"); self.online_keyword_edit.setMinimumWidth(320)
        self.online_limit_spin = QSpinBox(); self.online_limit_spin.setRange(1, 200); self.online_limit_spin.setValue(int(self.settings.get("online_default_limit", 20) or 20))
        self.online_search_btn = QPushButton("联网搜索")
        self.online_result_hint = QLabel("说明：默认显示 20 条；超量使用由用户自己负责。")
        form.addWidget(QLabel("联网配置"), 0, 0); form.addWidget(self.online_profile_combo, 0, 1)
        form.addWidget(QLabel("搜索词"), 0, 2); form.addWidget(self.online_keyword_edit, 0, 3, 1, 3)
        form.addWidget(QLabel("显示条数"), 1, 0); form.addWidget(self.online_limit_spin, 1, 1); form.addWidget(self.online_search_btn, 1, 2); form.addWidget(self.online_result_hint, 1, 3, 1, 3)
        top_l.addLayout(form)
        btns = QHBoxLayout()
        self.online_select_all_btn = QPushButton("全选")
        self.online_invert_btn = QPushButton("反选")
        self.online_clear_btn = QPushButton("清空")
        self.online_add_playlist_btn = QPushButton("加入播放列表")
        self.online_copy_btn = QPushButton("复制选中项")
        self.online_note_btn = QPushButton("加入笔记")
        self.online_ai_btn = QPushButton("发送AI")
        self.online_download_queue_btn = QPushButton("加入下载队列")
        for w in [self.online_select_all_btn, self.online_invert_btn, self.online_clear_btn, self.online_add_playlist_btn, self.online_copy_btn, self.online_note_btn, self.online_ai_btn, self.online_download_queue_btn]:
            btns.addWidget(w)
        btns.addStretch()
        top_l.addLayout(btns)
        self.online_result_table = self._create_item_table(show_show=True)
        top_l.addWidget(self.online_result_table, 1)
        outer.addWidget(top, 1)
        self.online_log = QPlainTextEdit(); self.online_log.setReadOnly(True)
        self.online_log.setMaximumHeight(160)
        outer.addWidget(self.online_log)

        self.online_search_btn.clicked.connect(self.start_online_search)
        self.online_profile_combo.currentIndexChanged.connect(self.on_active_online_profile_changed)
        self.online_select_all_btn.clicked.connect(lambda: self.set_checked_for_table(self.online_result_table, self.online_results, True))
        self.online_invert_btn.clicked.connect(lambda: self.invert_checked_for_table(self.online_result_table, self.online_results))
        self.online_clear_btn.clicked.connect(self.clear_online_results)
        self.online_add_playlist_btn.clicked.connect(lambda: self.add_items_to_playlist(self.resolve_action_items(self.online_results, self.online_result_table)))
        self.online_copy_btn.clicked.connect(lambda: self.copy_items_text(self.resolve_action_items(self.online_results, self.online_result_table)))
        self.online_note_btn.clicked.connect(lambda: self.add_note_to_items(self.resolve_action_items(self.online_results, self.online_result_table)))
        self.online_ai_btn.clicked.connect(lambda: self.send_items_to_ai(self.resolve_action_items(self.online_results, self.online_result_table)))
        self.online_download_queue_btn.clicked.connect(self.add_online_items_to_download_queue)
        self.online_result_table.cellClicked.connect(lambda r, c: self.on_table_cell_clicked(self.online_result_table, self.online_results, r, c))
        self.online_result_table.itemSelectionChanged.connect(lambda: self.on_table_selection_changed(self.online_result_table, self.online_results, False))
        self.online_result_table.cellDoubleClicked.connect(lambda r, c: self.open_word_action_dialog(self.online_results[r]) if 0 <= r < len(self.online_results) else None)
        self.refresh_online_profile_combo()

    # ---------- AI tab ----------
    def _build_ai_tab(self):
        outer = QVBoxLayout(self.ai_tab)
        top = QGroupBox("AI 互动")
        top_l = QVBoxLayout(top)
        row = QHBoxLayout()
        self.ai_target_combo = QComboBox()
        self.refresh_ai_target_combo()
        self.ai_send_limit_spin = QSpinBox(); self.ai_send_limit_spin.setRange(1, 100); self.ai_send_limit_spin.setValue(int(self.settings.get("ai_send_limit", 20) or 20))
        self.ai_send_btn = QPushButton("发送当前选择到 AI")
        row.addWidget(QLabel("接收对象")); row.addWidget(self.ai_target_combo)
        row.addWidget(QLabel("默认上限")); row.addWidget(self.ai_send_limit_spin)
        row.addWidget(self.ai_send_btn)
        self.ai_example_btn = QPushButton('配置案例')
        row.addWidget(self.ai_example_btn)
        row.addStretch()
        top_l.addLayout(row)
        self.ai_input_preview = QPlainTextEdit(); self.ai_input_preview.setPlaceholderText("这里预览即将发送到 AI 的文本（默认原句全文合并发送）。")
        self.ai_output = QPlainTextEdit(); self.ai_output.setReadOnly(True)
        top_l.addWidget(QLabel("发送预览")); top_l.addWidget(self.ai_input_preview, 1)
        top_l.addWidget(QLabel("AI 返回")); top_l.addWidget(self.ai_output, 2)
        outer.addWidget(top, 1)
        self.ai_send_btn.clicked.connect(self.send_preview_to_ai)
        self.ai_example_btn.clicked.connect(self.show_ai_target_examples)

    # ---------- notes tab ----------
    def _build_notes_tab(self):
        outer = QVBoxLayout(self.notes_tab)
        box = QGroupBox("学习笔记")
        lay = QVBoxLayout(box)
        top = QHBoxLayout()
        self.notes_dir_edit = QLineEdit(str(self._notes_output_dir()))
        self.notes_choose_dir_btn = QPushButton("选择输出文件夹")
        self.notes_search_edit = QLineEdit(); self.notes_search_edit.setPlaceholderText("搜索来源/台词/备注")
        self.notes_add_btn = QPushButton("新增/写入")
        self.notes_edit_btn = QPushButton("编辑")
        self.notes_refresh_btn = QPushButton("刷新")
        self.notes_export_btn = QPushButton("导出TXT")
        self.notes_delete_btn = QPushButton("删除选中")
        for w in [QLabel("输出目录"), self.notes_dir_edit, self.notes_choose_dir_btn, self.notes_search_edit, self.notes_add_btn, self.notes_edit_btn, self.notes_refresh_btn, self.notes_export_btn, self.notes_delete_btn]:
            top.addWidget(w)
        lay.addLayout(top)
        self.notes_table = QTableWidget(0, 4)
        self.notes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.notes_table.setHorizontalHeaderLabels(["来源", "时间", "台词", "备注"])
        self.notes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.notes_table)
        outer.addWidget(box, 1)
        self.notes_choose_dir_btn.clicked.connect(self.pick_note_dir)
        self.notes_search_edit.textChanged.connect(self.refresh_notes_table)
        self.notes_add_btn.clicked.connect(self.open_note_editor_from_tab)
        self.notes_edit_btn.clicked.connect(self.edit_selected_note)
        self.notes_refresh_btn.clicked.connect(self.refresh_notes_table)
        self.notes_export_btn.clicked.connect(self.export_notes)
        self.notes_delete_btn.clicked.connect(self.delete_selected_notes)

    def _build_vocab_tab(self):
        outer = QVBoxLayout(self.vocab_tab)
        box = QGroupBox("生词本")
        lay = QVBoxLayout(box)
        top = QHBoxLayout()
        self.vocab_dir_edit = QLineEdit(str(self._vocab_output_dir()))
        self.vocab_choose_dir_btn = QPushButton("选择输出文件夹")
        self.vocab_search_edit = QLineEdit(); self.vocab_search_edit.setPlaceholderText("搜索单词/台词/备注")
        self.vocab_add_btn = QPushButton("新增")
        self.vocab_edit_btn = QPushButton("编辑")
        self.vocab_style_btn = QPushButton("样式面板")
        self.vocab_refresh_btn = QPushButton("刷新")
        self.vocab_export_btn = QPushButton("导出TXT")
        self.vocab_delete_btn = QPushButton("删除选中")
        for w in [QLabel("输出目录"), self.vocab_dir_edit, self.vocab_choose_dir_btn, self.vocab_search_edit, self.vocab_add_btn, self.vocab_edit_btn, self.vocab_style_btn, self.vocab_refresh_btn, self.vocab_export_btn, self.vocab_delete_btn]:
            top.addWidget(w)
        lay.addLayout(top)
        self.vocab_table = QTableWidget(0, 5)
        self.vocab_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vocab_table.setHorizontalHeaderLabels(["单词", "来源台词", "备注", "颜色", "字体"])
        self.vocab_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.vocab_table)
        outer.addWidget(box, 1)
        self.vocab_choose_dir_btn.clicked.connect(self.pick_vocab_dir)
        self.vocab_search_edit.textChanged.connect(self.refresh_vocab_table)
        self.vocab_add_btn.clicked.connect(self.open_vocab_editor)
        self.vocab_edit_btn.clicked.connect(self.edit_selected_vocab)
        self.vocab_style_btn.clicked.connect(self.change_selected_vocab_style)
        self.vocab_refresh_btn.clicked.connect(self.refresh_vocab_table)
        self.vocab_export_btn.clicked.connect(self.export_vocab)
        self.vocab_delete_btn.clicked.connect(self.delete_selected_vocab)

    def _build_download_tab(self):
        outer = QVBoxLayout(self.download_tab)
        box = QGroupBox("批量下载")
        lay = QVBoxLayout(box)
        row = QHBoxLayout()
        self.download_dir_edit = QLineEdit(self.settings.get("download_dir", str(DOWNLOAD_DIR)))
        self.choose_download_dir_btn = QPushButton("选择目录")
        self.download_thread_spin = QSpinBox(); self.download_thread_spin.setRange(1, 10); self.download_thread_spin.setValue(int(self.settings.get("download_threads", 3) or 3))
        self.download_thread_hint = QLabel("下载线程")
        self.start_download_btn = QPushButton("开始下载")
        self.stop_download_btn = QPushButton("停止")
        row.addWidget(QLabel("下载目录")); row.addWidget(self.download_dir_edit, 1); row.addWidget(self.choose_download_dir_btn); row.addWidget(self.download_thread_hint); row.addWidget(self.download_thread_spin); row.addWidget(self.start_download_btn); row.addWidget(self.stop_download_btn)
        lay.addLayout(row)
        self.download_queue_table = QTableWidget(0, 3)
        self.download_queue_table.setHorizontalHeaderLabels(["名称", "URL", "状态"])
        self.download_queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.download_queue_table, 1)
        row2 = QHBoxLayout()
        self.download_urls_edit = QPlainTextEdit(); self.download_urls_edit.setPlaceholderText("可手动粘贴 URL，一行一个。")
        side = QVBoxLayout()
        self.add_urls_btn = QPushButton("从文本加入队列")
        self.clear_download_queue_btn = QPushButton("清空队列")
        self.download_progress_label = QLabel("进度：未开始")
        self.download_progress = QProgressBar(); self.download_progress.setRange(0, 100); self.download_progress.setValue(0)
        for w in [self.add_urls_btn, self.clear_download_queue_btn, self.download_progress_label, self.download_progress]:
            side.addWidget(w)
        side.addStretch()
        row2.addWidget(self.download_urls_edit, 1)
        row2.addLayout(side)
        lay.addLayout(row2)
        self.download_log = QPlainTextEdit(); self.download_log.setReadOnly(True)
        lay.addWidget(self.download_log, 1)
        outer.addWidget(box, 1)

        self.choose_download_dir_btn.clicked.connect(lambda: self.pick_dir(self.download_dir_edit))
        self.add_urls_btn.clicked.connect(self.add_manual_urls_to_download_queue)
        self.clear_download_queue_btn.clicked.connect(self.clear_download_queue)
        self.start_download_btn.clicked.connect(self.start_batch_download)
        self.stop_download_btn.clicked.connect(self.stop_batch_download)

    # ---------- batch srt tab ----------
    def _build_batch_srt_tab(self):
        outer = QVBoxLayout(self.batch_srt_tab)
        box = QGroupBox("SRT批量生成")
        form = QGridLayout(box)
        self.exe_edit = QLineEdit(); self.exe_edit.setMinimumWidth(360)
        exe_btn = QPushButton("选择引擎")
        self.video_folder_edit = QLineEdit(); self.video_folder_edit.setMinimumWidth(360)
        folder_btn = QPushButton("选择视频目录")
        self.model_combo = QComboBox(); self.model_combo.addItems(["large-v3-turbo", "large-v3", "large-v2", "medium", "small"])
        self.model_path_edit = QLineEdit(); self.model_path_edit.setMinimumWidth(360)
        model_btn = QPushButton("选择模型路径")
        self.language_combo = QComboBox(); self.language_combo.addItems(["auto", "en", "zh", "ja", "ko"])
        self.vad_cb = QCheckBox("启用 VAD 过滤器"); self.vad_cb.setChecked(True)
        self.enhance_cb = QCheckBox("语音增强 Demucs")
        self.same_dir_cb = QCheckBox("字幕保存到视频同目录"); self.same_dir_cb.setChecked(True)
        self.skip_existing_cb = QCheckBox("跳过已有字幕"); self.skip_existing_cb.setChecked(True)
        self.out_dir_edit = QLineEdit(); self.out_dir_edit.setMinimumWidth(360)
        out_btn = QPushButton("其他输出目录")
        self.extra_args_edit = QLineEdit(); self.extra_args_edit.setPlaceholderText("额外参数，例如 --device cuda"); self.extra_args_edit.setMinimumWidth(300)
        self.thread_spin = QSpinBox(); self.thread_spin.setRange(1, 10); self.thread_spin.setValue(1)
        self.start_batch_btn = QPushButton("开始批量转换")
        self.cancel_batch_btn = QPushButton("取消转换")
        self.cancel_batch_btn.setEnabled(False)
        self.batch_progress_label = QLabel("进度：未开始")
        self.batch_progress = QProgressBar(); self.batch_progress.setRange(0, 100); self.batch_progress.setValue(0)
        row = 0
        form.addWidget(QLabel("转换引擎"), row, 0); form.addWidget(self.exe_edit, row, 1, 1, 3); form.addWidget(exe_btn, row, 4); row += 1
        form.addWidget(QLabel("视频目录"), row, 0); form.addWidget(self.video_folder_edit, row, 1, 1, 3); form.addWidget(folder_btn, row, 4); row += 1
        form.addWidget(QLabel("模型"), row, 0); form.addWidget(self.model_combo, row, 1); form.addWidget(QLabel("语言"), row, 2); form.addWidget(self.language_combo, row, 3); row += 1
        form.addWidget(QLabel("模型路径"), row, 0); form.addWidget(self.model_path_edit, row, 1, 1, 3); form.addWidget(model_btn, row, 4); row += 1
        form.addWidget(self.vad_cb, row, 0, 1, 2); form.addWidget(self.enhance_cb, row, 2, 1, 2); row += 1
        form.addWidget(self.same_dir_cb, row, 0, 1, 2); form.addWidget(self.skip_existing_cb, row, 2, 1, 2); row += 1
        form.addWidget(QLabel("其他输出目录"), row, 0); form.addWidget(self.out_dir_edit, row, 1, 1, 3); form.addWidget(out_btn, row, 4); row += 1
        form.addWidget(QLabel("线程数"), row, 0); form.addWidget(self.thread_spin, row, 1); form.addWidget(QLabel("额外参数"), row, 2); form.addWidget(self.extra_args_edit, row, 3, 1, 2); row += 1
        form.addWidget(self.batch_progress_label, row, 0, 1, 2); form.addWidget(self.batch_progress, row, 2, 1, 3); row += 1
        form.addWidget(self.start_batch_btn, row, 0, 1, 2); form.addWidget(self.cancel_batch_btn, row, 2, 1, 2)
        outer.addWidget(box)
        self.batch_log = QPlainTextEdit(); self.batch_log.setReadOnly(True)
        outer.addWidget(self.batch_log, 1)
        exe_btn.clicked.connect(lambda: self.pick_file(self.exe_edit, "选择 Faster-Whisper-XXL", "Executable (*.exe);;All Files (*)"))
        folder_btn.clicked.connect(lambda: self.pick_dir(self.video_folder_edit))
        model_btn.clicked.connect(lambda: self.pick_dir(self.model_path_edit))
        out_btn.clicked.connect(lambda: self.pick_dir(self.out_dir_edit))
        self.start_batch_btn.clicked.connect(self.start_batch_srt)
        self.cancel_batch_btn.clicked.connect(self.cancel_batch_srt)

    # ---------- dictionary tab ----------
    def _build_dict_tab(self):
        outer = QVBoxLayout(self.dict_tab)
        top = QGroupBox("查词来源 / 内置标签页")
        top_l = QVBoxLayout(top)
        form = QFormLayout()
        self.dict_source_edit_1 = QLineEdit(); self.dict_source_edit_1.setPlaceholderText("例如 https://www.vocabulary.com/dictionary/{query}")
        self.dict_source_edit_2 = QLineEdit(); self.dict_source_edit_2.setPlaceholderText("例如 https://dictionary.cambridge.org/dictionary/english/{query}")
        self.dict_source_edit_3 = QLineEdit(); self.dict_source_edit_3.setPlaceholderText("例如 https://www.ldoceonline.com/dictionary/{query}")
        form.addRow("查词来源1", self.dict_source_edit_1)
        form.addRow("查词来源2", self.dict_source_edit_2)
        form.addRow("查词来源3", self.dict_source_edit_3)
        top_l.addLayout(form)
        row = QHBoxLayout()
        self.dict_open_manual_btn = QPushButton("打开当前输入")
        self.dict_clear_tabs_btn = QPushButton("清空内部标签页")
        row.addWidget(self.dict_open_manual_btn)
        row.addWidget(self.dict_clear_tabs_btn)
        row.addStretch()
        top_l.addLayout(row)
        self.dict_query_edit = QLineEdit(); self.dict_query_edit.setPlaceholderText("手动输入要查的单词 / 短语")
        top_l.addWidget(self.dict_query_edit)
        outer.addWidget(top)
        self.dict_browser_tabs = QTabWidget()
        outer.addWidget(self.dict_browser_tabs, 1)
        self.dict_open_manual_btn.clicked.connect(lambda: self.open_internal_dictionary_tabs(self.dict_query_edit.text().strip()))
        self.dict_clear_tabs_btn.clicked.connect(self.clear_dictionary_tabs)

    # ---------- config tab ----------
    def _build_config_tab(self):
        outer = QVBoxLayout(self.config_tab)
        self.save_cfg_btn2 = QPushButton("💾 保存全部配置")
        self.save_cfg_btn2.setStyleSheet("font-weight: bold; background: #cfae68; color: black; padding: 6px 12px;")
        self.save_cfg_btn2.clicked.connect(self.save_all_settings)
        cfg_top = QHBoxLayout()
        self.apply_cfg_btn = QPushButton("应用到运行中")
        self.save_cfg_btn2 = QPushButton("保存配置")
        self.import_cfg_btn2 = QPushButton("导入配置")
        self.export_cfg_btn = QPushButton("导出配置")
        self.config_status_label = QLabel("配置中心：未应用")
        for _w in [self.apply_cfg_btn, self.save_cfg_btn2, self.import_cfg_btn2, self.export_cfg_btn]:
            cfg_top.addWidget(_w)
        cfg_top.addStretch()
        cfg_top.addWidget(self.config_status_label)
        outer.addLayout(cfg_top)
        self.config_tabs = QTabWidget()
        outer.addWidget(self.config_tabs)
        basic = QWidget(); networkw = QWidget(); aiw = QWidget(); linksw = QWidget()
        self.config_tabs.addTab(basic, "基础配置")
        self.config_tabs.addTab(networkw, "联网配置")
        self.config_tabs.addTab(aiw, "AI接收对象")
        self.config_tabs.addTab(linksw, "链接标签")

        b_l = QVBoxLayout(basic)
        basic_box = QGroupBox("基础配置")
        basic_form = QFormLayout(basic_box)
        self.remember_cb = QCheckBox("记住配置"); self.remember_cb.setChecked(True)
        self.online_timeout_spin = QSpinBox(); self.online_timeout_spin.setRange(5, 120); self.online_timeout_spin.setValue(25)
        basic_form.addRow(self.remember_cb)
        basic_form.addRow("网络超时(秒)", self.online_timeout_spin)
        self.cfg_theme_info = QLabel()
        self.cfg_palette_info = QLabel()
        self.cfg_scale_info = QLabel()
        self.cfg_theme_info.setText(f"当前主题：{self.settings.get('theme_name', '') or (self.theme_combo.currentText() if hasattr(self, 'theme_combo') else '')}")
        self.cfg_palette_info.setText(f"当前配色：{self.settings.get('palette_name', '') or (self.palette_combo.currentText() if hasattr(self, 'palette_combo') else '')}")
        self.cfg_scale_info.setText(f"当前缩放：{self.settings.get('ui_scale_percent', '') or (self.ui_scale_combo.currentText() if hasattr(self, 'ui_scale_combo') else '100%')}")
        basic_form.addRow("主题状态", self.cfg_theme_info)
        basic_form.addRow("配色状态", self.cfg_palette_info)
        basic_form.addRow("界面缩放", self.cfg_scale_info)
        b_l.addWidget(basic_box)
        basic_hint = QPlainTextEdit()
        basic_hint.setReadOnly(True)
        basic_hint.setMaximumHeight(140)
        basic_hint.setPlainText("说明：\n1. 现在推荐优先使用『PlayPhrase Token直登』。\n2. 你只有 Token 时，直接在联网配置里填 Token 即可，不必再走 Cookie / CSRF 思路。\n3. 免费网页模式仅生成网页入口，不走真实 API 返回解析。\n4. 在线搜索始终优先使用联网模式顶部当前选中的配置。")
        b_l.addWidget(basic_hint)
        btns = QHBoxLayout()
        self.import_cfg_btn = QPushButton("导入TXT配置")
        self.save_cfg_btn = QPushButton("保存全部配置")
        btns.addWidget(self.import_cfg_btn); btns.addWidget(self.save_cfg_btn); btns.addStretch()
        b_l.addLayout(btns)

        nw_l = QVBoxLayout(networkw)
        nw_split = QSplitter(Qt.Horizontal)
        nw_split.setChildrenCollapsible(False)
        nw_split.setHandleWidth(10)
        nw_l.addWidget(nw_split, 1)

        left = QWidget(); left_l = QVBoxLayout(left)
        left_box = QGroupBox("网络配置列表")
        left_box_l = QVBoxLayout(left_box)
        self.net_profile_table = QTableWidget(0, 5)
        self.net_profile_table.setHorizontalHeaderLabels(["默认", "名称", "类型", "启用", "说明"])
        self.net_profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_box_l.addWidget(self.net_profile_table, 1)
        left_btns = QHBoxLayout()
        self.net_add_btn = QPushButton("新增配置")
        self.net_remove_btn = QPushButton("删除配置")
        self.net_clone_btn = QPushButton("复制配置")
        self.net_set_default_btn = QPushButton("设为默认")
        for w in [self.net_add_btn, self.net_remove_btn, self.net_clone_btn, self.net_set_default_btn]:
            left_btns.addWidget(w)
        left_btns.addStretch()
        left_box_l.addLayout(left_btns)
        left_l.addWidget(left_box)
        nw_split.addWidget(left)

        right = QWidget(); right_l = QVBoxLayout(right)
        right_box = QGroupBox("配置详情")
        right_form = QFormLayout(right_box)
        self.net_name_edit = QLineEdit(); self.net_name_edit.setMinimumWidth(220)
        self.net_kind_combo = QComboBox(); self.net_kind_combo.addItems(["playphrase_token", "playphrase_free", "playphrase_auth", "generic_api", "direct_web"])
        self.net_enabled_combo = QComboBox(); self.net_enabled_combo.addItems(["是", "否"])
        self.net_default_combo = QComboBox(); self.net_default_combo.addItems(["否", "是"])
        self.net_endpoint_edit = QLineEdit(); self.net_endpoint_edit.setPlaceholderText("API 地址或网页模板，例如 https://.../search?q={query}"); self.net_endpoint_edit.setMinimumWidth(420)
        self.net_method_combo = QComboBox(); self.net_method_combo.addItems(["GET", "POST"])
        self.net_note_edit = QLineEdit(); self.net_note_edit.setPlaceholderText("备注 / 说明")
        self.token_edit = QPlainTextEdit(); self.token_edit.setMaximumHeight(60)
        self.cookie_edit = QPlainTextEdit(); self.cookie_edit.setMaximumHeight(90)
        self.csrf_edit = QLineEdit(); self.csrf_edit.setMinimumWidth(260)
        self.user_agent_edit = QLineEdit(); self.user_agent_edit.setMinimumWidth(320)
        self.referer_edit = QLineEdit(); self.referer_edit.setMinimumWidth(320)
        self.proxy_edit = QLineEdit(); self.proxy_edit.setMinimumWidth(220)
        right_form.addRow("名称", self.net_name_edit)
        right_form.addRow("类型", self.net_kind_combo)
        right_form.addRow("启用", self.net_enabled_combo)
        right_form.addRow("默认", self.net_default_combo)
        right_form.addRow("端点/模板", self.net_endpoint_edit)
        right_form.addRow("方法", self.net_method_combo)
        right_form.addRow("说明", self.net_note_edit)
        self.net_auth_box = QGroupBox("Token 直登（优先填写 Token；Cookie / CSRF 可留空）")
        auth_form = QFormLayout(self.net_auth_box)
        auth_form.addRow("Token", self.token_edit)
        auth_form.addRow("Cookie", self.cookie_edit)
        auth_form.addRow("CSRF", self.csrf_edit)
        auth_form.addRow("User-Agent", self.user_agent_edit)
        auth_form.addRow("Referer", self.referer_edit)
        auth_form.addRow("代理", self.proxy_edit)
        auth_btn_row = QHBoxLayout()
        self.net_token_template_btn = QPushButton("设为 Token直登模板")
        self.net_clear_auth_btn = QPushButton("清空鉴权")
        auth_btn_row.addWidget(self.net_token_template_btn)
        auth_btn_row.addWidget(self.net_clear_auth_btn)
        auth_btn_row.addStretch()
        auth_btn_wrap = QWidget()
        auth_btn_wrap.setLayout(auth_btn_row)
        auth_form.addRow("快捷操作", auth_btn_wrap)
        right_l.addWidget(right_box)
        right_l.addWidget(self.net_auth_box)
        right_l.addStretch()
        nw_split.addWidget(right)
        left.setMaximumWidth(420)
        self.net_auth_box.setMaximumHeight(280)
        nw_split.setSizes([360, 980])

        ai_l = QVBoxLayout(aiw)
        ai_box = QGroupBox("AI 接收对象")
        ai_box_l = QVBoxLayout(ai_box)
        self.ai_target_table = QTableWidget(0, 5)
        self.ai_target_table.setHorizontalHeaderLabels(["名称", "类型", "端点", "方法", "启用"])
        self.ai_target_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ai_box_l.addWidget(self.ai_target_table)
        row = QHBoxLayout()
        self.ai_target_add_btn = QPushButton("新增对象")
        self.ai_target_remove_btn = QPushButton("删除对象")
        self.ai_target_refresh_btn = QPushButton("刷新到AI标签区")
        for w in [self.ai_target_add_btn, self.ai_target_remove_btn, self.ai_target_refresh_btn]:
            row.addWidget(w)
        row.addStretch()
        ai_box_l.addLayout(row)
        self.ai_headers_edit = QPlainTextEdit(); self.ai_headers_edit.setPlaceholderText("选中 AI 对象的请求头 JSON（例如 Authorization / Cookie）")
        ai_box_l.addWidget(self.ai_headers_edit)
        ai_l.addWidget(ai_box, 1)

        links_l = QVBoxLayout(linksw)
        links_box = QGroupBox("配置链接标签")
        links_box_l = QVBoxLayout(links_box)
        self.link_tree = QTreeWidget(); self.link_tree.setHeaderLabels(["分类 / 名称", "链接"])
        links_box_l.addWidget(self.link_tree)
        row2 = QHBoxLayout()
        self.link_add_cat_btn = QPushButton("新增分类")
        self.link_add_item_btn = QPushButton("新增链接")
        self.link_remove_btn = QPushButton("删除选中")
        self.link_open_btn = QPushButton("打开选中链接")
        for w in [self.link_add_cat_btn, self.link_add_item_btn, self.link_remove_btn, self.link_open_btn]:
            row2.addWidget(w)
        row2.addStretch()
        links_box_l.addLayout(row2)
        links_l.addWidget(links_box, 1)

        self.import_cfg_btn.clicked.connect(self.import_txt_config)
        self.save_cfg_btn.clicked.connect(self.save_all_settings)
        self.net_add_btn.clicked.connect(self.add_network_profile)
        self.net_remove_btn.clicked.connect(self.remove_network_profile)
        self.net_clone_btn.clicked.connect(self.clone_network_profile)
        self.net_set_default_btn.clicked.connect(self.set_selected_network_profile_default)
        self.net_profile_table.itemSelectionChanged.connect(self.on_network_profile_row_changed)
        self.net_kind_combo.currentTextChanged.connect(self.update_network_profile_kind_ui)
        for w in [self.net_name_edit, self.net_endpoint_edit, self.net_note_edit, self.csrf_edit, self.user_agent_edit, self.referer_edit, self.proxy_edit]:
            if hasattr(w, 'editingFinished'):
                w.editingFinished.connect(self.sync_current_network_profile_detail)
        self.net_method_combo.currentTextChanged.connect(self.sync_current_network_profile_detail)
        self.net_enabled_combo.currentTextChanged.connect(self.sync_current_network_profile_detail)
        self.net_default_combo.currentTextChanged.connect(self.sync_current_network_profile_detail)
        self.token_edit.textChanged.connect(self.sync_current_network_profile_detail)
        self.cookie_edit.textChanged.connect(self.sync_current_network_profile_detail)
        self.net_token_template_btn.clicked.connect(self.apply_token_profile_template)
        self.net_clear_auth_btn.clicked.connect(self.clear_network_auth_fields)

        self.ai_target_add_btn.clicked.connect(self.add_ai_target_row)
        self.ai_target_remove_btn.clicked.connect(self.remove_ai_target_row)
        self.ai_target_refresh_btn.clicked.connect(self.pull_ai_targets_from_table)
        self.ai_target_table.itemSelectionChanged.connect(self.on_ai_target_row_changed)
        self.ai_headers_edit.textChanged.connect(lambda: self.pull_ai_targets_from_table(silent=True))
        self.link_add_cat_btn.clicked.connect(self.add_link_category)
        self.link_add_item_btn.clicked.connect(self.add_link_item)
        self.link_remove_btn.clicked.connect(self.remove_link_item)
        self.link_open_btn.clicked.connect(self.open_selected_link)
        self.apply_cfg_btn.clicked.connect(self.apply_config_to_runtime)
        self.save_cfg_btn2.clicked.connect(self.save_all_settings)
        self.import_cfg_btn2.clicked.connect(self.import_txt_config)
        self.export_cfg_btn.clicked.connect(self.export_current_config)


    def _save_notes_records(self):
        self._save_notes_store()

    def update_status_banner(self):
        try:
            total = len(self.state.playlist) if hasattr(self, 'state') and getattr(self.state, 'playlist', None) is not None else 0
            current = self.current_item.show_name if getattr(self, 'current_item', None) else '未选择'
            text = f"播放列表：{total} 条｜当前：{current}"
            if hasattr(self, 'play_status_label') and self.play_status_label is not None:
                self.play_status_label.setText(text)
            if hasattr(self, 'config_status_label') and self.config_status_label is not None:
                self.config_status_label.setText(text)
        except Exception:
            pass

    def select_network_profile_row(self, idx: int):
        try:
            if hasattr(self, 'net_profile_table') and self.net_profile_table is not None and 0 <= int(idx) < self.net_profile_table.rowCount():
                self.net_profile_table.blockSignals(True)
                self.net_profile_table.clearSelection()
                self.net_profile_table.selectRow(int(idx))
                self.net_profile_table.blockSignals(False)
                try:
                    self.on_network_profile_row_changed()
                except Exception:
                    pass
        except Exception:
            pass


    def apply_theme(self, theme_name: str, palette_name: str = None):
        """应用主题和配色"""
        if not theme_name:
            theme_name = "曜石金奢"

        ai_pack_apply_theme(self, theme_name, palette_name or self.settings.get("palette_name", ""))

        self.settings["theme_name"] = theme_name
        if palette_name and palette_name.strip():
            self.settings["palette_name"] = palette_name.strip()

        try:
            scale_text = normalize_ui_scale_text(self.settings.get("ui_scale_percent", "100%"))
            m = re.match(r"^(\d{1,3})%$", scale_text)
            self._apply_ui_scale_stylesheet(int(m.group(1)) if m else 100)
        except Exception:
            pass

        try:
            self.apply_local_font_settings_to_widgets()
        except Exception:
            pass

        print(f"✓ 主题已应用 → {theme_name} | 配色: {palette_name or '默认'}")

        # 保存（静默保存，避免弹窗干扰）
        try:
            self.save_all_settings(silent=True)
        except Exception as e:
            print(f"保存主题时出错: {e}")

    def force_reload_theme_and_palette(self):
        """启动后强制重新加载并应用保存的主题和配色"""
        try:
            saved_theme = self.settings.get("theme_name", "曜石金奢").strip()
            saved_palette = self.settings.get("palette_name", "").strip()

            print(f"[FORCE-RELOAD] 从配置文件读取 → 主题: {saved_theme} | 配色: {saved_palette}")

            if hasattr(self, 'theme_combo') and saved_theme:
                idx = self.theme_combo.findText(saved_theme)
                if idx >= 0:
                    self.theme_combo.setCurrentIndex(idx)

            if hasattr(self, 'palette_combo') and saved_palette:
                idx = self.palette_combo.findText(saved_palette)
                if idx >= 0:
                    self.palette_combo.setCurrentIndex(idx)

            self.apply_theme(saved_theme, saved_palette if saved_palette else None)

            print(f"[FORCE-RELOAD] 成功应用保存的主题和配色")
        except Exception as e:
            print(f"[FORCE-RELOAD] 执行失败: {e}")

    def load_current_text_to_ai_analysis(self):
        text = ""
        if self.current_item is not None:
            text = (self.current_item.en or self.current_item.subtitle_text or self.current_item.zh or "").strip()
        elif self.state.playlist:
            for it in self.state.playlist:
                if it.selected:
                    text = (it.en or it.subtitle_text or it.zh or "").strip()
                    break
        if not text:
            rows = self.get_table_selected_rows(self.local_result_table) if hasattr(self, "local_result_table") else []
            if rows and 0 <= rows[0] < len(self.local_results):
                it = self.local_results[rows[0]]
                text = (it.en or it.subtitle_text or it.zh or "").strip()
        if not text:
            text = (self.subtitle_browser.toPlainText() if hasattr(self, "subtitle_browser") else "").strip()
        if hasattr(self, "ai_analysis_panel") and text:
            try:
                self.ai_analysis_panel.input_box.setPlainText(text)
            except Exception:
                pass

    def add_ai_analysis_to_notes(self):
        text = ""
        try:
            text = self.ai_analysis_panel.input_box.toPlainText().strip()
        except Exception:
            return
        if not text:
            QMessageBox.information(self, "提示", "AI分析区暂无内容")
            return
        uid = self.current_item.uid if self.current_item else make_uid("ai_note", text, time.time())
        self.notes_records[uid] = {"uid": uid, "source": "AI分析", "time": time.strftime("%Y-%m-%d %H:%M:%S"), "text": text, "note": "来自AI分析"}
        self._save_notes_records()
        self.refresh_notes_table()
        QMessageBox.information(self, "完成", "已加入学习笔记")

    def add_ai_analysis_to_vocab(self):
        text = ""
        try:
            text = self.ai_analysis_panel.input_box.toPlainText().strip()
        except Exception:
            return
        if not text:
            QMessageBox.information(self, "提示", "AI分析区暂无内容")
            return
        first = text.split()[0][:80]
        self.vocab_store.append(VocabularyEntry(word=first, source_uid=self.current_item.uid if self.current_item else "", source_text=text))
        self._save_vocab_store()
        self.refresh_vocab_table()
        QMessageBox.information(self, "完成", "已加入生词本")

    def closeEvent(self, event):
        """关闭窗口前强制保存所有设置"""
        try:
            self.sync_current_network_profile_detail()
            self.save_all_settings(silent=True)
        except Exception as e:
            print(f"关闭时保存设置失败: {e}")

        # 原有清理逻辑
        tmp = [p for p in self.pending_download_cleanup if p.exists()]
        if tmp:
            ret = QMessageBox.question(self, "退出提醒", "存在未加入学习列表的缓存/下载文件。是否清空这些临时文件？")
            if ret == QMessageBox.Yes:
                for p in tmp:
                    try:
                        if p.is_file():
                            p.unlink()
                    except Exception:
                        pass
        super().closeEvent(event)


def main():
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
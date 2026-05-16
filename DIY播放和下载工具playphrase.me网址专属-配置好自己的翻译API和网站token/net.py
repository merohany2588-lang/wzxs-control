import os
import re
import sys
import html
import json
import time
import hashlib
import random
import threading
import subprocess
import urllib3
import requests
import html
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QSize, QTimer
from PySide6.QtGui import QAction, QDesktopServices, QFont, QTextDocument, QGuiApplication, QColor, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QLineEdit,
    QSpinBox, QCheckBox, QTabWidget, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QGroupBox, QFormLayout, QSlider, QComboBox,
    QAbstractItemView, QFrame, QProgressBar, QPlainTextEdit,
    QDialog, QDialogButtonBox, QSizePolicy, QStackedLayout, QMenu, QTextBrowser, QColorDialog, QKeySequenceEdit
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtPrintSupport import QPrinter

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_OK = True
except Exception:
    WEB_OK = False
    QWebEngineView = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
baidu_lock = threading.Lock()
==================在这里配置好自己的翻译API和网站token即可以使用===================
TENCENT_ID = ""
TENCENT_KEY = ""
BAIDU_ID = ""
BAIDU_KEY = ""
PROXIES = {""}
MY_AUTH = ""
MY_CSRF = ""
MY_COOKIE = ""
DEFAULT_OUTPUT_DIR = os.path.abspath(os.path.join(os.getcwd(), "渲染结果"))
APP_TITLE = "VIP 原片商业工作台 V3"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}

ASPECT_PRESETS = {
    "9:16 竖版": (1080, 1920),
    "16:9 横版": (1920, 1080),
    "1:1 方形": (1080, 1080),
    "4:5 海报": (1080, 1350),
}

AI_URLS = {
    "豆包 AI": "https://www.doubao.com/",
    "Google AI": "https://aistudio.google.com/",
    "Gemini": "https://gemini.google.com/",
}

RESOURCES = {
    "AI 搜索": {
        "豆包 AI": "https://www.doubao.com/",
        "Google AI": "https://aistudio.google.com/",
        "Gemini": "https://gemini.google.com/",
        "ChatGPT": "https://chatgpt.com/",
        "Claude": "https://claude.ai/",
        "Grok": "https://grok.com/",
        "通义千问": "https://qianwen.aliyun.com/",
        "元宝": "https://yuanbao.tencent.com/",
    },
    "词典": {
        "Bing词典": "https://cn.bing.com/dict/",
        "Ozdic": "https://ozdic.com/",
        "Ludwig": "https://ludwig.guru/",
        "Collins": "https://www.collinsdictionary.com/zh/",
        "Longman": "https://www.ldoceonline.com/",
        "Vocabulary": "https://www.vocabulary.com/",
        "Cambridge": "https://dictionary.cambridge.org/",
        "Oxford": "https://www.oxfordlearnersdictionaries.com/",
        "Reverso": "https://context.reverso.net/",
        "Thesaurus": "https://www.thesaurus.com/",
        "Power Thesaurus": "https://www.powerthesaurus.org/",
        "MW Thesaurus": "https://www.merriam-webster.com/thesaurus",
    },
    "台词视频": {
        "PlayPhrase": "https://playphrase.me",
        "YouGlish": "https://youglish.com/",
        "Yarn": "https://yarn.co/",
        "GetYarn": "https://getyarn.io/",
        "Comb.io": "https://comb.io/",
    },
    "学习工具": {
        "BBC English": "https://www.bbc.co.uk/learningenglish/",
        "British Council": "https://learnenglish.britishcouncil.org/free-resources",
        "Coursera": "https://www.coursera.org/",
        "WolframAlpha": "https://www.wolframalpha.com/",
    }
}




FONT_STYLE_PRESETS = [
    "Microsoft YaHei", "Microsoft YaHei UI", "SimHei", "SimSun", "KaiTi",
    "NSimSun", "Arial", "Calibri", "Tahoma", "Verdana",
    "Trebuchet MS", "Georgia", "Times New Roman", "Segoe UI", "Consolas",
    "Courier New", "Candara", "Century Gothic", "Comic Sans MS", "Impact"
]

EXTRA_PLAYER_THEMES = {
    "梦幻星空": {"window_bg":"#11162a","window_fg":"#e9f0ff","header1":"#1c2340","header2":"#232b52","header3":"#2e3767","border":"#6677d6","group_bg1":"#161d37","group_bg2":"#141b33","group_title":"#c3ccff","input_bg":"#0f1530","input_fg":"#eff3ff","select_bg":"#293462","button1":"#7a89ff","button2":"#5d6ee4","button_hover":"#93a0ff","button_press":"#4d5fd2","tab_bg":"#171f3a","tab_sel":"#2f3b6b","tab_text":"#dbe2ff","chunk":"#90a0ff","handle":"#91a1ff","video_card":"#0e1328","video_stage1":"#151c35","video_stage2":"#0f1530","transport_bg":"rgba(19,25,48,0.96)","player_badge_bg":"#6e7dff","player_badge_fg":"#ffffff","player_title":"#eff3ff","player_hint":"#c9d2ff","time_pill_bg":"#1b2343","time_pill_fg":"#ffffff","accent":"#7487ff","accent2":"#9ab0ff","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(17,23,44,0.96)","subtitle_en":"#ffffff","subtitle_zh":"#f4c8ff","side_bg":"rgba(18,24,46,0.97)","side_title":"#d5ddff","translation_bg":"rgba(31,39,71,0.88)","translation_border":"#7181e0","word_bg":"#131936","word_border":"#6577d6","word_fg":"#eef2ff"},
    "儿童乐园": {"window_bg":"#fffaf3","window_fg":"#564b35","header1":"#fff2cf","header2":"#ffe7a8","header3":"#ffd86c","border":"#f2c65d","group_bg1":"#fff8e9","group_bg2":"#fff4dc","group_title":"#c58c25","input_bg":"#ffffff","input_fg":"#564b35","select_bg":"#ffe9b7","button1":"#ffb74d","button2":"#ff9800","button_hover":"#ffc86e","button_press":"#f08e00","tab_bg":"#fff0c8","tab_sel":"#ffe2a0","tab_text":"#956615","chunk":"#ffcf67","handle":"#ffd56f","video_card":"#fffdf5","video_stage1":"#fff7df","video_stage2":"#fff0ce","transport_bg":"rgba(255,247,226,0.96)","player_badge_bg":"#ffe082","player_badge_fg":"#7a5600","player_title":"#70542f","player_hint":"#b18643","time_pill_bg":"#fffdf5","time_pill_fg":"#8d6a28","accent":"#f7a832","accent2":"#ffd166","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(255,251,240,0.96)","subtitle_en":"#5a4b31","subtitle_zh":"#d67e00","side_bg":"rgba(255,248,232,0.97)","side_title":"#c48a25","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#f4d18d","word_bg":"#fffef8","word_border":"#f4d18d","word_fg":"#564b35"},
    "动物世界": {"window_bg":"#f7f4ea","window_fg":"#4c493f","header1":"#edf0e3","header2":"#dfe7cf","header3":"#c8d6b2","border":"#a9b98a","group_bg1":"#f5f7ef","group_bg2":"#edf2e2","group_title":"#76885b","input_bg":"#ffffff","input_fg":"#4c493f","select_bg":"#dce5cb","button1":"#a8bf73","button2":"#8faa54","button_hover":"#b7cc83","button_press":"#7d9749","tab_bg":"#eef3e4","tab_sel":"#dce7ca","tab_text":"#667b48","chunk":"#a2bf6d","handle":"#bdd19b","video_card":"#fcfcf8","video_stage1":"#edf1e5","video_stage2":"#e6ecdc","transport_bg":"rgba(241,244,232,0.96)","player_badge_bg":"#c8d6b2","player_badge_fg":"#50613a","player_title":"#576649","player_hint":"#7f8f70","time_pill_bg":"#fcfdf9","time_pill_fg":"#6b7b59","accent":"#8fa55c","accent2":"#b7cc83","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(251,252,246,0.96)","subtitle_en":"#4e5548","subtitle_zh":"#7f935f","side_bg":"rgba(243,246,235,0.97)","side_title":"#708154","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#c9d7b4","word_bg":"#fcfdf9","word_border":"#cfdbc0","word_fg":"#4c493f"},
    "海底世界": {"window_bg":"#eefaff","window_fg":"#355463","header1":"#ddf7ff","header2":"#c7f0ff","header3":"#99def6","border":"#7cc7df","group_bg1":"#f3fdff","group_bg2":"#eaf9fd","group_title":"#3e8ea7","input_bg":"#ffffff","input_fg":"#355463","select_bg":"#d0f1fb","button1":"#67c5e6","button2":"#39a8ce","button_hover":"#83d4ee","button_press":"#3199bb","tab_bg":"#e4f8ff","tab_sel":"#c9efff","tab_text":"#4c90a8","chunk":"#6ac7e7","handle":"#9adcf2","video_card":"#f8feff","video_stage1":"#ddf6fc","video_stage2":"#d3effa","transport_bg":"rgba(239,251,255,0.97)","player_badge_bg":"#a4e6ff","player_badge_fg":"#236680","player_title":"#3b6777","player_hint":"#6697a8","time_pill_bg":"#ffffff","time_pill_fg":"#4b8192","accent":"#4eb7da","accent2":"#8ad9ef","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(248,254,255,0.96)","subtitle_en":"#345866","subtitle_zh":"#1194be","side_bg":"rgba(237,251,255,0.97)","side_title":"#3a8ba4","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#bce8f5","word_bg":"#ffffff","word_border":"#c8edf8","word_fg":"#355463"},
    "恐龙侏罗纪": {"window_bg":"#f6f5ef","window_fg":"#4a4a3d","header1":"#eef0e5","header2":"#e0e6d0","header3":"#b9c59c","border":"#97a86c","group_bg1":"#f7f8f1","group_bg2":"#edf0e3","group_title":"#697a43","input_bg":"#ffffff","input_fg":"#4a4a3d","select_bg":"#dbe4c1","button1":"#92a85d","button2":"#728641","button_hover":"#9db46a","button_press":"#65783a","tab_bg":"#eef1e5","tab_sel":"#dce6c5","tab_text":"#5f7240","chunk":"#9ab463","handle":"#bccb95","video_card":"#fbfbf7","video_stage1":"#eef0e5","video_stage2":"#e2e6d7","transport_bg":"rgba(245,246,238,0.96)","player_badge_bg":"#cad6a8","player_badge_fg":"#58693a","player_title":"#566045","player_hint":"#7c8666","time_pill_bg":"#ffffff","time_pill_fg":"#68754e","accent":"#809754","accent2":"#adbf79","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(252,252,248,0.96)","subtitle_en":"#4c4d40","subtitle_zh":"#7a8f4a","side_bg":"rgba(242,245,234,0.97)","side_title":"#697a43","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#d4dcc0","word_bg":"#ffffff","word_border":"#dde4cc","word_fg":"#4a4a3d"},
    "精灵天使": {"window_bg":"#fffaff","window_fg":"#5b5360","header1":"#f8efff","header2":"#efe2ff","header3":"#d9c1ff","border":"#c7abea","group_bg1":"#fcf7ff","group_bg2":"#f7f0ff","group_title":"#9a79c3","input_bg":"#ffffff","input_fg":"#5b5360","select_bg":"#eadcff","button1":"#d3b5ff","button2":"#b98de8","button_hover":"#e1c9ff","button_press":"#aa79dd","tab_bg":"#f7efff","tab_sel":"#eadcff","tab_text":"#8b6ab2","chunk":"#d1b0ff","handle":"#e0cbff","video_card":"#fffafe","video_stage1":"#f8f1ff","video_stage2":"#f3e8ff","transport_bg":"rgba(253,249,255,0.96)","player_badge_bg":"#efdcff","player_badge_fg":"#815da8","player_title":"#695e78","player_hint":"#9b8aad","time_pill_bg":"#ffffff","time_pill_fg":"#836ba3","accent":"#b98de8","accent2":"#e2c8ff","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(255,251,255,0.96)","subtitle_en":"#5e5467","subtitle_zh":"#a36cd9","side_bg":"rgba(251,246,255,0.97)","side_title":"#916dc0","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#e0cff5","word_bg":"#ffffff","word_border":"#eadcf9","word_fg":"#5b5360"},
    "暧昧空间": {"window_bg":"#fff5f7","window_fg":"#604851","header1":"#ffe7ec","header2":"#ffd7e0","header3":"#f3afc1","border":"#e09bb0","group_bg1":"#fff8fa","group_bg2":"#fff0f4","group_title":"#bc7289","input_bg":"#ffffff","input_fg":"#604851","select_bg":"#ffdbe5","button1":"#ee9cb4","button2":"#da7896","button_hover":"#f3aec2","button_press":"#cd6a87","tab_bg":"#ffeef3","tab_sel":"#ffdbe5","tab_text":"#a56277","chunk":"#f0a0b7","handle":"#f5bfd0","video_card":"#fffafd","video_stage1":"#fff2f6","video_stage2":"#ffe9f0","transport_bg":"rgba(255,246,249,0.96)","player_badge_bg":"#ffd8e3","player_badge_fg":"#90566b","player_title":"#7a5764","player_hint":"#b08191","time_pill_bg":"#ffffff","time_pill_fg":"#906171","accent":"#db7a98","accent2":"#f0a6bc","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(255,250,252,0.96)","subtitle_en":"#6a515a","subtitle_zh":"#d46d92","side_bg":"rgba(255,244,248,0.97)","side_title":"#ba6f86","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#f1c3d1","word_bg":"#ffffff","word_border":"#f3d0da","word_fg":"#604851"},
    "极简风格": {"window_bg":"#fafafa","window_fg":"#444444","header1":"#f3f3f3","header2":"#ececec","header3":"#dfdfdf","border":"#d0d0d0","group_bg1":"#ffffff","group_bg2":"#f9f9f9","group_title":"#6a6a6a","input_bg":"#ffffff","input_fg":"#444444","select_bg":"#efefef","button1":"#d6d6d6","button2":"#bebebe","button_hover":"#e2e2e2","button_press":"#b0b0b0","tab_bg":"#f5f5f5","tab_sel":"#ebebeb","tab_text":"#666666","chunk":"#cfcfcf","handle":"#dcdcdc","video_card":"#ffffff","video_stage1":"#fbfbfb","video_stage2":"#f3f3f3","transport_bg":"rgba(255,255,255,0.96)","player_badge_bg":"#ededed","player_badge_fg":"#666666","player_title":"#4a4a4a","player_hint":"#888888","time_pill_bg":"#ffffff","time_pill_fg":"#666666","accent":"#bdbdbd","accent2":"#dfdfdf","accent_fg":"#333333","subtitle_panel_bg":"rgba(255,255,255,0.96)","subtitle_en":"#444444","subtitle_zh":"#777777","side_bg":"rgba(255,255,255,0.97)","side_title":"#666666","translation_bg":"rgba(255,255,255,0.94)","translation_border":"#e6e6e6","word_bg":"#ffffff","word_border":"#ececec","word_fg":"#444444"},
    "护眼模式": {"window_bg":"#f4f7ee","window_fg":"#4c5747","header1":"#edf3e4","header2":"#dfe9d2","header3":"#cad8b5","border":"#a8b891","group_bg1":"#f8fbf3","group_bg2":"#eef4e6","group_title":"#6b7e58","input_bg":"#ffffff","input_fg":"#4c5747","select_bg":"#dfe9d2","button1":"#a8bc8a","button2":"#8fa470","button_hover":"#b4c69b","button_press":"#829565","tab_bg":"#edf4e4","tab_sel":"#dce8cc","tab_text":"#647653","chunk":"#abc190","handle":"#c7d6b3","video_card":"#fbfcf8","video_stage1":"#eff4e8","video_stage2":"#e8f0df","transport_bg":"rgba(245,249,239,0.96)","player_badge_bg":"#d7e4c3","player_badge_fg":"#59694b","player_title":"#56634b","player_hint":"#7c8a6f","time_pill_bg":"#ffffff","time_pill_fg":"#6f7d62","accent":"#92a874","accent2":"#bfd1a6","accent_fg":"#ffffff","subtitle_panel_bg":"rgba(252,253,249,0.96)","subtitle_en":"#4c5747","subtitle_zh":"#72885c","side_bg":"rgba(245,249,239,0.97)","side_title":"#677956","translation_bg":"rgba(255,255,255,0.92)","translation_border":"#d4dec5","word_bg":"#ffffff","word_border":"#dde6d0","word_fg":"#4c5747"}
}

def safe_mkdir(path: str):
    os.makedirs(path, exist_ok=True)


def normalize_auth(token: str) -> str:
    token = (token or "").strip()
    if token.startswith("Token "):
        return token
    if token.startswith("Token"):
        return "Token " + token[5:]
    return token


def ffmpeg_exists() -> bool:
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return r.returncode == 0
    except Exception:
        return False


def extract_year(text: str) -> int:
    years = re.findall(r"(19\d{2}|20\d{2})", text or "")
    return int(years[-1]) if years else 0


def make_session():
    s = requests.Session()
    s.proxies = PROXIES
    s.headers.update({
        "authorization": normalize_auth(MY_AUTH),
        "x-csrf-token": MY_CSRF,
        "cookie": MY_COOKIE,
    })
    return s


def get_translation(text):
    try:
        from tencentcloud.common import credential
        from tencentcloud.tmt.v20180321 import tmt_client, models
        cred = credential.Credential(TENCENT_ID, TENCENT_KEY)
        client = tmt_client.TmtClient(cred, "ap-guangzhou")
        req = models.TextTranslateRequest()
        req.SourceText, req.Source, req.Target, req.ProjectId = text, "en", "zh", 0
        return client.TextTranslate(req).TargetText
    except Exception:
        with baidu_lock:
            try:
                salt = str(random.randint(32768, 65536))
                sign = hashlib.md5((BAIDU_ID + text + salt + BAIDU_KEY).encode("utf-8")).hexdigest()
                r = requests.get(
                    "https://fanyi-api.baidu.com/api/trans/vip/translate",
                    params={"q": text, "from": "en", "to": "zh", "appid": BAIDU_ID, "salt": salt, "sign": sign},
                    timeout=5,
                    proxies={"http": None, "https": None},
                    verify=False,
                )
                res = r.json()
                if "trans_result" in res:
                    return res["trans_result"][0]["dst"]
            except Exception:
                pass
    return text


def translate_text(text: str, engine: str = "内置翻译") -> str:
    text = (text or "").strip()
    if not text:
        return text
    if engine in ("内置翻译", ""):
        return get_translation(text)
    if engine == "MyMemory 免费":
        try:
            r = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": "en|zh-CN"},
                timeout=15,
                proxies={"http": None, "https": None},
                verify=False,
            )
            data = r.json()
            return data.get("responseData", {}).get("translatedText", "").strip() or text
        except Exception:
            return text
    if engine == "LibreTranslate 免费":
        for ep in ("https://translate.argosopentech.com/translate", "https://libretranslate.de/translate"):
            try:
                r = requests.post(
                    ep,
                    data={"q": text, "source": "en", "target": "zh", "format": "text"},
                    timeout=20,
                    proxies={"http": None, "https": None},
                    verify=False,
                )
                data = r.json()
                if data.get("translatedText"):
                    return data["translatedText"].strip()
            except Exception:
                continue
    return text


def subtitle_filter_arg(path: str) -> str:
    norm = os.path.abspath(path).replace("\\", "/")
    norm = norm.replace(":", "\\:")
    norm = norm.replace("'", "\\'")
    return f"subtitles={norm}"


def build_scale_pad_filter(aspect_name: str) -> str:
    width, height = ASPECT_PRESETS.get(aspect_name, ASPECT_PRESETS["9:16 竖版"])
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
    )


def find_potplayer() -> str:
    candidates = [
        r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
        r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini.exe",
        r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return ""


def download_file(session: requests.Session, url: str, out_path: str):
    with session.get(url, stream=True, verify=False, timeout=90) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)


def open_with_potplayer(potplayer_path: str, media_path: str, subtitle_path: str = "", start_ms: int = 0):
    potplayer_path = (potplayer_path or "").strip()
    if not potplayer_path or not os.path.exists(potplayer_path):
        raise RuntimeError("PotPlayer 路径无效，请先选择 PotPlayer 主程序")
    args = [potplayer_path]
    if subtitle_path and os.path.exists(subtitle_path):
        args.append(f"/sub={subtitle_path}")
    if start_ms > 0:
        sec = int(start_ms // 1000)
        hh = sec // 3600
        mm = (sec % 3600) // 60
        ss = sec % 60
        args.append(f"/seek={hh:02d}:{mm:02d}:{ss:02d}")
    args.append(media_path)
    subprocess.Popen(args)


@dataclass
class PhraseItem:
    rank: int
    sentence: str
    video_url: str
    words: list = field(default_factory=list)
    movie: str = ""
    subtitle_override: str = ""
    zh_override: str = ""
    trim_start: float = 0.0
    trim_end: float = 0.0
    duration_hint: float = 0.0
    selected: bool = False
    source_id: str = ""
    year: int = 0
    zh_auto: str = ""

    def display_title(self) -> str:
        text = re.sub(r"\s+", " ", (self.subtitle_override or self.sentence or "").strip())
        return f"#{self.rank} [{self.year or '-'}] {text[:92]}" + ("..." if len(text) > 92 else "")


def extract_transcribed_text(item) -> str:
    words = getattr(item, "words", None) or []
    if words:
        parts = []
        for w in words:
            if isinstance(w, dict):
                t = str(w.get("text", "")).strip()
            else:
                t = str(getattr(w, "text", "")).strip()
            if t:
                parts.append(t)
        txt = re.sub(r"\s+", " ", " ".join(parts)).strip()
        if txt:
            return txt
    return re.sub(r"\s+", " ", str(getattr(item, "sentence", "")).strip())


def fetch_search_results(keyword: str, limit: int = 100, skip: int = 0) -> List[PhraseItem]:
    session = make_session()
    resp = session.get(
        "https://www.playphrase.me/api/v1/phrases/search",
        params={"q": keyword, "limit": limit, "skip": skip},
        verify=False,
        timeout=40,
    )
    resp.raise_for_status()
    data = resp.json().get("phrases", [])
    results = []
    for idx, item in enumerate(data, start=skip + 1):
        words = item.get("words", []) or []
        sentence = " ".join([w.get("text", "") for w in words]).strip() or item.get("text", "")
        movie = item.get("movie") or item.get("film") or item.get("source") or ""
        source_id = str(item.get("id") or item.get("uuid") or "")
        duration_hint = 0.0
        if words:
            duration_hint = max(0.0, (words[-1].get("end", 0) - words[0].get("start", 0)) / 1000)
        results.append(PhraseItem(
            rank=idx,
            sentence=sentence,
            video_url=item.get("video-url", ""),
            words=words,
            movie=movie,
            duration_hint=duration_hint,
            source_id=source_id,
            year=extract_year(movie),
        ))
    return results


def build_export_rows(items: List[PhraseItem], field_keys: List[str], do_translate: bool = False, translate_engine: str = "内置翻译"):
    headers_map = {
        "rank": "序号",
        "sentence": "台词",
        "translation": "翻译",
        "year": "年份",
        "movie": "影片",
        "video_url": "视频链接",
    }
    headers = [headers_map[k] for k in field_keys]
    rows = []
    for it in items:
        trans_cache = None
        row = []
        for key in field_keys:
            if key == "rank":
                row.append(it.rank)
            elif key == "sentence":
                row.append(extract_transcribed_text(it))
            elif key == "translation":
                if trans_cache is None:
                    trans_cache = it.zh_override or it.zh_auto or translate_text(extract_transcribed_text(it), translate_engine if do_translate else "内置翻译")
                row.append(trans_cache)
            elif key == "year":
                row.append(it.year or "")
            elif key == "movie":
                row.append(it.movie)
            elif key == "video_url":
                row.append(it.video_url)
        rows.append(row)
    return headers, rows


def export_search_results(items: List[PhraseItem], out_dir: str, base_name: str, export_formats: List[str], field_keys: List[str], do_translate: bool = False, translate_engine: str = "内置翻译"):
    safe_mkdir(out_dir)
    base = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", base_name).strip("_") or "搜索结果"
    headers, rows = build_export_rows(items, field_keys, do_translate, translate_engine)
    outputs = []

    if "txt" in export_formats:
        txt_path = os.path.join(out_dir, f"{base}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\t".join(headers) + "\n")
            for row in rows:
                f.write("\t".join([str(x) for x in row]) + "\n")
        outputs.append(txt_path)

    html = ["<html><head><meta charset='utf-8'><style>body{font-family:Microsoft YaHei,Arial;} table{border-collapse:collapse;width:100%;} td,th{border:1px solid #888;padding:6px;vertical-align:top;} th{background:#ddd;}</style></head><body>"]
    html.append(f"<h2>{base}</h2><table><tr>")
    for h in headers:
        html.append(f"<th>{h}</th>")
    html.append("</tr>")
    for row in rows:
        html.append("<tr>" + "".join([f"<td>{str(v)}</td>" for v in row]) + "</tr>")
    html.append("</table></body></html>")
    html_text = "".join(html)

    if "doc" in export_formats:
        doc_path = os.path.join(out_dir, f"{base}.doc")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        outputs.append(doc_path)

    if "pdf" in export_formats:
        pdf_path = os.path.join(out_dir, f"{base}.pdf")
        doc = QTextDocument()
        doc.setHtml(html_text)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(pdf_path)
        doc.print_(printer)
        outputs.append(pdf_path)

    if "xlsx" in export_formats:
        from openpyxl import Workbook
        xlsx_path = os.path.join(out_dir, f"{base}.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "SearchResults"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        wb.save(xlsx_path)
        outputs.append(xlsx_path)

    return tuple(outputs)


def generate_ass_from_text_mode(en_text: str, zh_text: str, out_path: str, font_size: int = 56, subtitle_mode: str = "双语"):
    en_text = re.sub(r"\s+", " ", (en_text or "").strip())
    zh_text = re.sub(r"\s+", " ", (zh_text or "").strip())
    total_ms = 3500
    en_chunks = en_text.split() or [en_text]
    kf = max(10, total_ms // max(1, len(en_chunks)) // 10)
    en_body = "".join(f"{{\\kf{kf}}}{w} " for w in en_chunks)
    zh_body = ""
    if zh_text:
        zh_kf = max(6, total_ms // max(1, len(zh_text)) // 10)
        zh_body = "".join(f"{{\\kf{zh_kf}}}{c}" for c in zh_text)

    en_size = font_size
    zh_size = max(24, int(font_size * 0.72))
    header = (
        "[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: English,Microsoft YaHei,{en_size},&H00FFFFFF&,&H00FFFFFF&,&H00101010&,&H00000000&,1,1,3,1,2,30,30,120,1\n"
        f"Style: Chinese,Microsoft YaHei,{zh_size},&H0000FFFF&,&H0000FFFF&,&H00101010&,&H00000000&,1,1,3,1,2,30,30,56,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    with open(out_path, "w", encoding="utf-8-sig") as f:
        f.write(header)
        if subtitle_mode in ("英文", "双语"):
            f.write(f"Dialogue: 0,0:00:00.00,0:00:03.50,English,,0,0,0,,{en_body}\n")
        if subtitle_mode in ("中文", "双语"):
            f.write(f"Dialogue: 0,0:00:00.00,0:00:03.50,Chinese,,0,0,0,,{zh_body}\n")


def render_selected_items(items: List[PhraseItem], output_dir: str, project_name: str, subtitle_font_size: int, subtitle_mode: str, aspect_ratio: str, translate_engine: str, logger):
    if not ffmpeg_exists():
        raise RuntimeError("未检测到 ffmpeg")
    if not items:
        raise RuntimeError("没有可导出的片段")
    project_safe = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", project_name).strip("_") or "项目"
    project_dir = os.path.join(output_dir, f"{project_safe}_{int(time.time())}")
    safe_mkdir(project_dir)
    session = make_session()
    clip_paths = []
    for idx, item in enumerate(items, start=1):
        logger(f"[{idx}/{len(items)}] 下载并渲染：{item.display_title()}")
        raw_path = os.path.join(project_dir, f"raw_{idx:03d}.mp4")
        clip_path = os.path.join(project_dir, f"clip_{idx:03d}.mp4")
        ass_path = os.path.join(project_dir, f"clip_{idx:03d}.ass")
        download_file(session, item.video_url, raw_path)
        en_text = item.subtitle_override or extract_transcribed_text(item)
        zh_text = item.zh_override or item.zh_auto or translate_text(en_text, translate_engine)
        generate_ass_from_text_mode(en_text, zh_text, ass_path, subtitle_font_size, subtitle_mode)

        cmd = ["ffmpeg", "-y"]
        if item.trim_start > 0:
            cmd += ["-ss", str(item.trim_start)]
        cmd += ["-i", raw_path]
        if item.trim_end > 0 and item.trim_end > item.trim_start:
            duration = item.trim_end - item.trim_start if item.trim_start > 0 else item.trim_end
            cmd += ["-to", str(duration)]
        vf = [build_scale_pad_filter(aspect_ratio)]
        if subtitle_mode != "无字幕":
            vf.append(subtitle_filter_arg(ass_path))
        cmd += [
            "-vf", ",".join(vf),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            clip_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "FFmpeg 渲染失败")[-1800:])
        clip_paths.append(clip_path)
        for p in [raw_path, ass_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    concat_txt = os.path.join(project_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8-sig") as f:
        for path in clip_paths:
            safe = path.replace("\\", "/").replace("'", r"'\''")
            f.write(f"file '{safe}'\n")

    final_path = os.path.join(project_dir, "合成结果.mp4")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", final_path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        logger("直接拼接失败，切换重编码合成...")
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
               "-c:v", "libx264", "-preset", "medium", "-crf", "22",
               "-c:a", "aac", "-b:a", "192k", final_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "合成失败")[-1800:])

    with open(os.path.join(project_dir, "project.json"), "w", encoding="utf-8") as f:
        json.dump([asdict(it) for it in items], f, ensure_ascii=False, indent=2)
    return project_dir, final_path


def batch_download_raw(items: List[PhraseItem], out_dir: str, logger):
    session = make_session()
    folder = os.path.join(out_dir, f"批量下载_{int(time.time())}")
    safe_mkdir(folder)
    for idx, item in enumerate(items, start=1):
        ext = Path(QUrl(item.video_url).path()).suffix or ".mp4"
        name = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", extract_transcribed_text(item)[:60]).strip("_") or f"clip_{idx:03d}"
        out = os.path.join(folder, f"{idx:03d}_{name}{ext}")
        logger(f"[{idx}/{len(items)}] 下载：{item.display_title()}")
        download_file(session, item.video_url, out)
    return folder


class SearchWorker(QThread):
    finished_ok = Signal(list)
    failed = Signal(str)

    def __init__(self, keyword: str, limit: int, skip: int):
        super().__init__()
        self.keyword, self.limit, self.skip = keyword, limit, skip

    def run(self):
        try:
            self.finished_ok.emit(fetch_search_results(self.keyword, self.limit, self.skip))
        except Exception as e:
            self.failed.emit(str(e))


class ExportWorker(QThread):
    log_msg = Signal(str)
    done_ok = Signal(str, str)
    failed = Signal(str)

    def __init__(self, items, output_dir, project_name, subtitle_font_size, subtitle_mode, aspect_ratio, translate_engine):
        super().__init__()
        self.items = items
        self.output_dir = output_dir
        self.project_name = project_name
        self.subtitle_font_size = subtitle_font_size
        self.subtitle_mode = subtitle_mode
        self.aspect_ratio = aspect_ratio
        self.translate_engine = translate_engine

    def run(self):
        try:
            project_dir, final_path = render_selected_items(
                self.items, self.output_dir, self.project_name, self.subtitle_font_size,
                self.subtitle_mode, self.aspect_ratio, self.translate_engine, self.log_msg.emit
            )
            self.done_ok.emit(project_dir, final_path)
        except Exception as e:
            self.failed.emit(str(e))


class DownloadWorker(QThread):
    log_msg = Signal(str)
    done_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, items, out_dir):
        super().__init__()
        self.items = items
        self.out_dir = out_dir

    def run(self):
        try:
            folder = batch_download_raw(self.items, self.out_dir, self.log_msg.emit)
            self.done_ok.emit(folder)
        except Exception as e:
            self.failed.emit(str(e))


class DocExportWorker(QThread):
    done_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, items, out_dir, base_name, export_formats, field_keys, do_translate, translate_engine):
        super().__init__()
        self.items = items
        self.out_dir = out_dir
        self.base_name = base_name
        self.export_formats = export_formats
        self.field_keys = field_keys
        self.do_translate = do_translate
        self.translate_engine = translate_engine

    def run(self):
        try:
            paths = export_search_results(self.items, self.out_dir, self.base_name, self.export_formats, self.field_keys, self.do_translate, self.translate_engine)
            self.done_ok.emit("\n".join([p for p in paths if p]))
        except Exception as e:
            self.failed.emit(str(e))


class TranslateWorker(QThread):
    translated = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, cache_key: str, text: str, engine: str):
        super().__init__()
        self.cache_key = cache_key
        self.text = text
        self.engine = engine

    def run(self):
        try:
            result = translate_text(self.text, self.engine)
            self.translated.emit(self.cache_key, result)
        except Exception as e:
            self.failed.emit(self.cache_key, str(e))



class ResultRowWidget(QWidget):
    rowClicked = Signal()
    rowDoubleClicked = Signal()

    def __init__(self, title_html: str, checked: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        self.label = QLabel(title_html)
        self.label.setTextFormat(Qt.RichText)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.NoTextInteraction)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.checkbox, 0)
        layout.addWidget(self.label, 1)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.rowClicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.rowDoubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class PreviewCacheWorker(QThread):
    done_ok = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, cache_key: str, url: str, out_path: str):
        super().__init__()
        self.cache_key = cache_key
        self.url = url
        self.out_path = out_path

    def run(self):
        try:
            safe_mkdir(os.path.dirname(self.out_path))
            tmp_path = self.out_path + '.part'
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            download_file(make_session(), self.url, tmp_path)
            if os.path.exists(self.out_path):
                try:
                    os.remove(self.out_path)
                except Exception:
                    pass
            os.replace(tmp_path, self.out_path)
            self.done_ok.emit(self.cache_key, self.out_path)
        except Exception as e:
            self.failed.emit(self.cache_key, str(e))


class DictionaryLookupWorker(QThread):
    finished_ok = Signal(str, dict)
    failed = Signal(str, str)

    def __init__(self, word: str):
        super().__init__()
        self.word = (word or '').strip().lower()

    def run(self):
        try:
            if not self.word:
                raise RuntimeError('空单词')
            r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{self.word}", timeout=15, proxies={"http": None, "https": None}, verify=False)
            r.raise_for_status()
            data = r.json()
            entry = data[0] if isinstance(data, list) and data else {}
            phonetics = entry.get('phonetics', []) or []
            meanings = entry.get('meanings', []) or []
            ipa = ''
            audio = ''
            for ph in phonetics:
                ipa = ipa or str(ph.get('text') or '').strip()
                audio = audio or str(ph.get('audio') or '').strip()
            defs = []
            for m in meanings[:4]:
                part = str(m.get('partOfSpeech') or '').strip()
                for d in (m.get('definitions') or [])[:2]:
                    defi = str(d.get('definition') or '').strip()
                    ex = str(d.get('example') or '').strip()
                    if defi:
                        defs.append({'part': part, 'definition': defi, 'example': ex})
            self.finished_ok.emit(self.word, {'ipa': ipa, 'audio': audio, 'definitions': defs})
        except Exception as e:
            self.failed.emit(self.word, str(e))


class SubtitleOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent;")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 40)
        root.addStretch()
        self.en = QLabel("")
        self.zh = QLabel("")
        for lab, color, size in ((self.en, "#ffffff", 28), (self.zh, "#8cf2ff", 22)):
            lab.setWordWrap(True)
            lab.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            lab.setStyleSheet(f"""
                color: {color};
                font-weight: 700;
                font-size: {size}px;
                background-color: rgba(0, 0, 0, 120);
                border-radius: 10px;
                padding: 8px 12px;
            """)
            root.addWidget(lab)
        self.hide()

    def set_mode_and_text(self, mode: str, en_text: str, zh_text: str):
        self.en.setVisible(mode in ("英文", "双语"))
        self.zh.setVisible(mode in ("中文", "双语"))
        self.en.setText(en_text or "")
        self.zh.setText(zh_text or "")
        self.setVisible(mode != "无字幕" and bool(en_text or zh_text))

    def clear_text(self):
        self.en.clear()
        self.zh.clear()
        self.hide()



class VideoFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("videoCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.video = QVideoWidget()
        self.video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.video)
        self.overlay = SubtitleOverlay(self.video)
        self.overlay.raise_()
        self.center_tip = QLabel("未加载预览视频")
        self.center_tip.setParent(self.video)
        self.center_tip.setAlignment(Qt.AlignCenter)
        self.center_tip.setWordWrap(True)
        self.center_tip.setStyleSheet("""
            color: #dff7ff;
            font-size: 22px;
            font-weight: 800;
            background-color: rgba(0, 0, 0, 120);
            border: 1px solid rgba(14, 205, 230, 0.9);
            border-radius: 16px;
            padding: 14px 22px;
        """)
        self.center_tip.raise_()

    def show_message(self, text: str):
        self.center_tip.setText(text or "")
        self.center_tip.show()
        self.center_tip.raise_()

    def hide_message(self):
        self.center_tip.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay") and hasattr(self, "video"):
            self.overlay.setGeometry(self.video.rect())
        if hasattr(self, "center_tip") and hasattr(self, "video"):
            w = max(320, int(self.video.width() * 0.48))
            h = 92
            x = max(20, (self.video.width() - w) // 2)
            y = max(20, (self.video.height() - h) // 2)
            self.center_tip.setGeometry(x, y, w, h)

class FloatingEditorDialog(QDialog):
    applied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("剪辑操作台")
        self.resize(520, 720)
        self.setMinimumSize(440, 560)
        self.setWindowFlag(Qt.Window, True)

        main = QVBoxLayout(self)
        head = QHBoxLayout()
        self.topmost_cb = QCheckBox("置顶")
        self.topmost_cb.toggled.connect(self.toggle_topmost)
        self.hide_after_apply_cb = QCheckBox("应用后自动收起")
        head.addWidget(self.topmost_cb)
        head.addWidget(self.hide_after_apply_cb)
        head.addStretch()
        main.addLayout(head)

        self.form_box = QGroupBox("剪辑 / 字幕 / 导出设置")
        self.form_layout = QVBoxLayout(self.form_box)
        main.addWidget(self.form_box, 1)

        self.buttons = QDialogButtonBox()
        self.apply_btn = self.buttons.addButton("应用到当前选中项", QDialogButtonBox.AcceptRole)
        self.close_btn = self.buttons.addButton("关闭", QDialogButtonBox.RejectRole)
        self.close_btn.clicked.connect(self.close)
        self.apply_btn.clicked.connect(self.applied.emit)
        main.addWidget(self.buttons)

    def set_form_widget(self, widget):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        self.form_layout.addWidget(widget)

    def toggle_topmost(self, checked: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()


class WebLoginTab(QWidget):
    def __init__(self, title: str, url: str):
        super().__init__()
        self.url = url
        layout = QVBoxLayout(self)
        tools = QHBoxLayout()
        self.open_btn = QPushButton(f"打开 {title}")
        self.open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url)))
        self.login_btn = QPushButton("登录 / 跳转到本站")
        self.login_btn.clicked.connect(self.open_here)
        self.reload_btn = QPushButton("刷新")
        tools.addWidget(self.open_btn)
        tools.addWidget(self.login_btn)
        tools.addWidget(self.reload_btn)
        tools.addStretch()
        layout.addLayout(tools)
        if WEB_OK:
            self.view = QWebEngineView()
            self.view.setUrl(QUrl(self.url))
            self.reload_btn.clicked.connect(self.view.reload)
            layout.addWidget(self.view, 1)
        else:
            tip = QLabel("当前环境未安装 Qt WebEngine，标签内浏览不可用。点击上方按钮可外部打开。")
            tip.setWordWrap(True)
            tip.setStyleSheet("padding:16px;")
            layout.addWidget(tip)
            self.view = None
            self.reload_btn.setEnabled(False)

    def open_here(self):
        if self.view:
            self.view.setUrl(QUrl(self.url))
        else:
            QDesktopServices.openUrl(QUrl(self.url))


class ProWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1720, 1040)
        self.setMinimumSize(1320, 820)

        self.results: List[PhraseItem] = []
        self.queue_items: List[PhraseItem] = []
        self.search_worker = None
        self.export_worker = None
        self.download_worker = None
        self.doc_worker = None

        self.root_output_dir = DEFAULT_OUTPUT_DIR
        safe_mkdir(self.root_output_dir)

        self.current_preview_from_queue = False
        self.last_exported_video = ""
        self.current_temp_subtitle = ""
        self.player_mode = "embedded"
        self.current_theme_name = "奶油樱花房"
        self.font_area_settings = {
            "search": {"family": "Microsoft YaHei UI", "size": 12, "color": "#5b4b57"},
            "results": {"family": "Georgia", "size": 12, "color": "#5b4b57"},
            "queue": {"family": "Segoe UI", "size": 12, "color": "#5b4b57"},
            "subtitle_en": {"family": "Trebuchet MS", "size": 20, "color": "#6d5263"},
            "subtitle_zh": {"family": "Microsoft YaHei UI", "size": 18, "color": "#c0789b"},
            "title": {"family": "Microsoft YaHei UI", "size": 16, "color": "#7b5870"},
        }
        self.shortcuts_map = {"播放/暂停":"Space","停止":"Ctrl+S","沉浸式学习":"Ctrl+I","显示/隐藏上栏":"Ctrl+1","显示/隐藏下栏":"Ctrl+2","切换循环模式":"Ctrl+L","循环次数+1":"Ctrl+Up","循环次数-1":"Ctrl+Down","复制英文字幕":"Ctrl+Shift+C","复制中文字幕":"Ctrl+Alt+C"}
        self.current_theme_cfg = None
        self.current_item: Optional[PhraseItem] = None
        self.resource_views = {}
        self.base_font_px = 14
        self.translate_workers = {}
        self.translation_cache = {}
        self.bing_lookup_timer = QTimer(self)
        self.bing_lookup_timer.setSingleShot(True)
        self.bing_lookup_timer.timeout.connect(self._flush_pending_bing_lookup)
        self.pending_bing_word = ""
        self.preview_cache_dir = os.path.join(self.root_output_dir, "preview_cache")
        safe_mkdir(self.preview_cache_dir)
        self.preview_cache_workers = {}
        self.preview_cache_index = {}
        self.pending_preview_autoplay_key = ""
        self.immersive_mode = False
        self.top_controls_visible = True
        self.bottom_controls_visible = True
        self.dictionary_worker = None

        self.audio = QAudioOutput()
        self.audio.setVolume(0.8)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.pron_audio = QAudioOutput()
        self.pron_audio.setVolume(1.0)
        self.pron_player = QMediaPlayer()
        self.pron_player.setAudioOutput(self.pron_audio)
        self.video_frame = VideoFrame()
        self.player.setVideoOutput(self.video_frame.video)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)
        self.player.playbackStateChanged.connect(self.on_player_state_changed)
        self.player.errorOccurred.connect(self.on_player_error)

        self._setup_ui()
        self.apply_font_scale(2)
        if hasattr(self, "video_frame"):
            self.video_frame.show_message("双击搜索结果或点击“加入预览”开始播放")

    def _setup_ui(self):
        self.setStyleSheet(self._build_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        title_box = QVBoxLayout()
        hero = QLabel(APP_TITLE)
        hero.setObjectName("heroTitle")
        sub = QLabel("搜索 / 双语内嵌字幕预览 / 批量下载 / 文档导出 / PotPlayer 联动 / AI 内嵌搜索")
        sub.setObjectName("heroSub")
        title_box.addWidget(hero)
        title_box.addWidget(sub)
        hl.addLayout(title_box)
        hl.addStretch()

        output_box = QHBoxLayout()
        output_box.addWidget(QLabel("输出目录"))
        self.output_edit = QLineEdit(self.root_output_dir)
        choose_btn = QPushButton("选择输出目录")
        choose_btn.clicked.connect(self.choose_output_dir)
        open_btn = QPushButton("打开输出目录")
        open_btn.clicked.connect(self.open_output_dir)
        output_box.addWidget(self.output_edit, 1)
        output_box.addWidget(choose_btn)
        output_box.addWidget(open_btn)
        hl.addLayout(output_box, 1)
        root.addWidget(header)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.workspace_tab = QWidget()
        self.batch_tab = QWidget()
        self.docs_tab = QWidget()
        self.ai_tab = QWidget()
        self.log_tab = QWidget()
        self.tabs.addTab(self.workspace_tab, "智能工作台")
        self.tabs.addTab(self.batch_tab, "批量下载")
        self.tabs.addTab(self.docs_tab, "文档导出")
        self.tabs.addTab(self.ai_tab, "AI 搜索")
        self.tabs.addTab(self.log_tab, "运行日志")

        self._build_workspace_tab()
        self._build_batch_tab()
        self._build_docs_tab()
        self._build_ai_tab()
        self._build_log_tab()

        toolbar = self.addToolBar("主工具")
        toolbar.setMovable(False)
        act_small = QAction("字体-", self)
        act_small.triggered.connect(lambda: self.font_slider.setValue(max(0, self.font_slider.value() - 1)))
        act_big = QAction("字体+", self)
        act_big.triggered.connect(lambda: self.font_slider.setValue(min(7, self.font_slider.value() + 1)))
        toolbar.addAction(act_small)
        toolbar.addAction(act_big)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

    def _build_workspace_tab(self):
        layout = QVBoxLayout(self.workspace_tab)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(True)
        self.main_splitter.setHandleWidth(10)
        layout.addWidget(self.main_splitter)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setSpacing(10)
        self.main_splitter.addWidget(left)

        search_group = QGroupBox("搜索与筛选")
        sg = QGridLayout(search_group)
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("输入关键词，例如 join / brilliant / what's on your mind")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(20, 3000)
        self.limit_spin.setValue(200)
        self.skip_spin = QSpinBox()
        self.skip_spin.setRange(0, 999999)
        self.skip_spin.setValue(0)
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(0, 7)
        self.font_slider.setValue(2)
        self.font_slider.valueChanged.connect(self.apply_font_scale)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["默认排序", "句子长度短→长", "句子长度长→短", "影片年代旧→新", "影片年代新→旧"])
        self.sort_combo.currentIndexChanged.connect(self.sort_results)
        self.select_all_by_default_cb = QCheckBox("搜索结果默认全选")
        self.search_btn = QPushButton("开始搜索")
        self.search_btn.clicked.connect(self.start_search)
        self.load_more_btn = QPushButton("继续加载下一批")
        self.load_more_btn.clicked.connect(self.load_more_results)
        sg.addWidget(QLabel("关键词"), 0, 0)
        sg.addWidget(self.keyword_edit, 0, 1, 1, 5)
        sg.addWidget(QLabel("返回数量"), 1, 0)
        sg.addWidget(self.limit_spin, 1, 1)
        sg.addWidget(QLabel("跳过条数"), 1, 2)
        sg.addWidget(self.skip_spin, 1, 3)
        sg.addWidget(QLabel("界面字号"), 1, 4)
        sg.addWidget(self.font_slider, 1, 5)
        sg.addWidget(QLabel("结果排序"), 2, 0)
        sg.addWidget(self.sort_combo, 2, 1, 1, 2)
        sg.addWidget(self.select_all_by_default_cb, 2, 3, 1, 2)
        sg.addWidget(self.search_btn, 2, 5)
        sg.addWidget(self.load_more_btn, 3, 5)

        self.search_font_combo = QComboBox(); self.search_font_combo.addItems(FONT_STYLE_PRESETS); self.search_font_combo.setCurrentText(self.font_area_settings["search"]["family"])
        self.results_font_combo = QComboBox(); self.results_font_combo.addItems(FONT_STYLE_PRESETS); self.results_font_combo.setCurrentText(self.font_area_settings["results"]["family"])
        self.queue_font_combo = QComboBox(); self.queue_font_combo.addItems(FONT_STYLE_PRESETS); self.queue_font_combo.setCurrentText(self.font_area_settings["queue"]["family"])
        self.search_font_size_spin = QSpinBox(); self.search_font_size_spin.setRange(8, 48); self.search_font_size_spin.setValue(self.font_area_settings["search"]["size"])
        self.results_font_size_spin = QSpinBox(); self.results_font_size_spin.setRange(8, 48); self.results_font_size_spin.setValue(self.font_area_settings["results"]["size"])
        self.queue_font_size_spin = QSpinBox(); self.queue_font_size_spin.setRange(8, 48); self.queue_font_size_spin.setValue(self.font_area_settings["queue"]["size"])
        self.search_font_color_btn = QPushButton("颜色")
        self.results_font_color_btn = QPushButton("颜色")
        self.queue_font_color_btn = QPushButton("颜色")
        self.search_font_combo.currentTextChanged.connect(lambda v: self.update_font_area("search", family=v))
        self.results_font_combo.currentTextChanged.connect(lambda v: self.update_font_area("results", family=v))
        self.queue_font_combo.currentTextChanged.connect(lambda v: self.update_font_area("queue", family=v))
        self.search_font_size_spin.valueChanged.connect(lambda v: self.update_font_area("search", size=v))
        self.results_font_size_spin.valueChanged.connect(lambda v: self.update_font_area("results", size=v))
        self.queue_font_size_spin.valueChanged.connect(lambda v: self.update_font_area("queue", size=v))
        self.search_font_color_btn.clicked.connect(lambda: self.choose_font_color("search"))
        self.results_font_color_btn.clicked.connect(lambda: self.choose_font_color("results"))
        self.queue_font_color_btn.clicked.connect(lambda: self.choose_font_color("queue"))
        sg.addWidget(QLabel("搜索框字体"), 4, 0)
        sg.addWidget(self.search_font_combo, 4, 1)
        sg.addWidget(self.search_font_size_spin, 4, 2)
        sg.addWidget(self.search_font_color_btn, 4, 3)
        sg.addWidget(QLabel("结果框字体"), 5, 0)
        sg.addWidget(self.results_font_combo, 5, 1)
        sg.addWidget(self.results_font_size_spin, 5, 2)
        sg.addWidget(self.results_font_color_btn, 5, 3)
        sg.addWidget(QLabel("预览框字体"), 6, 0)
        sg.addWidget(self.queue_font_combo, 6, 1)
        sg.addWidget(self.queue_font_size_spin, 6, 2)
        sg.addWidget(self.queue_font_color_btn, 6, 3)

        result_group = QGroupBox("搜索结果 / 预览列表")
        rg = QVBoxLayout(result_group)

        top_toggle = QHBoxLayout()
        self.toggle_result_tools_btn = QPushButton("隐藏结果工具")
        self.toggle_result_tools_btn.clicked.connect(self.toggle_result_tools)
        self.minimize_left_btn = QPushButton("左侧最小化")
        self.minimize_left_btn.clicked.connect(self.minimize_left_panel)
        self.restore_layout_btn = QPushButton("恢复布局")
        self.restore_layout_btn.clicked.connect(self.restore_default_layout)
        top_toggle.addWidget(self.toggle_result_tools_btn)
        top_toggle.addWidget(self.minimize_left_btn)
        top_toggle.addWidget(self.restore_layout_btn)
        top_toggle.addStretch()
        rg.addLayout(top_toggle)

        self.result_tools_wrap = QWidget()
        rt = QHBoxLayout(self.result_tools_wrap)
        rt.setContentsMargins(0, 0, 0, 0)
        self.add_selected_btn = QPushButton("加入预览")
        self.add_selected_btn.clicked.connect(self.add_selected_results)
        self.preview_btn = QPushButton("播放当前")
        self.preview_btn.clicked.connect(self.preview_current_result)
        self.browser_btn = QPushButton("浏览器打开")
        self.browser_btn.clicked.connect(self.open_current_in_browser)
        self.export_search_btn = QPushButton("导出搜索结果文档")
        self.export_search_btn.clicked.connect(lambda: self.tabs.setCurrentWidget(self.docs_tab))
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_results)
        self.invert_btn = QPushButton("反选")
        self.invert_btn.clicked.connect(self.invert_all_results)
        self.clear_btn = QPushButton("清空勾选")
        self.clear_btn.clicked.connect(self.unselect_all_results)
        for w in [self.add_selected_btn, self.preview_btn, self.browser_btn, self.export_search_btn, self.select_all_btn, self.invert_btn, self.clear_btn]:
            rt.addWidget(w)
        rt.addStretch()
        rg.addWidget(self.result_tools_wrap)

        self.result_list = QListWidget()
        self.result_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_list.itemSelectionChanged.connect(self.on_result_selection_changed)
        self.result_list.itemDoubleClicked.connect(self.handle_result_double_click)
        rg.addWidget(self.result_list, 1)

        preview_queue_box = QGroupBox("预览列表")
        ql = QVBoxLayout(preview_queue_box)
        queue_tools = QHBoxLayout()
        self.preview_queue_play_btn = QPushButton("播放选中预览")
        self.preview_queue_play_btn.clicked.connect(self.preview_current_queue_item)
        self.remove_btn = QPushButton("移除")
        self.remove_btn.clicked.connect(self.remove_queue_item)
        self.clear_queue_btn = QPushButton("清空预览列表")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_tools.addWidget(self.preview_queue_play_btn)
        queue_tools.addWidget(self.remove_btn)
        queue_tools.addWidget(self.clear_queue_btn)
        queue_tools.addStretch()
        ql.addLayout(queue_tools)
        self.queue_list = QListWidget()
        self.queue_list.itemSelectionChanged.connect(self.on_queue_selection_changed)
        self.queue_list.itemDoubleClicked.connect(lambda _=None: self.preview_current_queue_item())
        ql.addWidget(self.queue_list)

        self.left_vertical_splitter = QSplitter(Qt.Vertical)
        self.left_vertical_splitter.setChildrenCollapsible(True)
        self.left_vertical_splitter.setHandleWidth(8)
        self.left_vertical_splitter.addWidget(search_group)
        self.left_vertical_splitter.addWidget(result_group)
        self.left_vertical_splitter.addWidget(preview_queue_box)
        self.left_vertical_splitter.setSizes([280, 360, 320])
        left_l.addWidget(self.left_vertical_splitter, 1)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setSpacing(10)
        self.main_splitter.addWidget(right)

        preview_group = QGroupBox("专业播放器 / 实时预览")
        pg = QVBoxLayout(preview_group)
        pg.setSpacing(10)

        preview_head = QHBoxLayout()
        self.player_mode_combo = QComboBox()
        self.player_mode_combo.addItems(["内嵌播放器", "PotPlayer"])
        self.player_mode_combo.currentTextChanged.connect(self.on_player_mode_changed)
        self.preview_ratio_combo = QComboBox()
        self.preview_ratio_combo.addItems(list(ASPECT_PRESETS.keys()))
        self.preview_ratio_combo.setCurrentText("16:9 横版")
        self.preview_ratio_combo.currentTextChanged.connect(self.apply_preview_aspect)
        self.player_theme_combo = QComboBox()
        self.player_theme_combo.addItems(["奶油樱花房", "薰衣草卧室", "原木奶白房", "夜灯粉紫房", "草莓奶昔房", "晨雾玫瑰房", "薄荷手账房", "月光银杏房", "梦幻星空", "儿童乐园", "动物世界", "海底世界", "恐龙侏罗纪", "精灵天使", "暧昧空间", "极简风格", "护眼模式"])
        self.player_theme_combo.currentTextChanged.connect(self.apply_player_theme)
        self.playback_options_btn = QPushButton("播放选项 ▾")
        self.open_editor_popup_btn = QPushButton("剪辑工作台")
        self.open_editor_popup_btn.clicked.connect(self.show_editor_dialog)
        self.max_preview_btn = QPushButton("预览最大化")
        self.max_preview_btn.clicked.connect(self.maximize_preview_area)
        self.fullscreen_btn = QPushButton("全屏观影")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen_playback)
        preview_head.addWidget(QLabel("播放模式"))
        preview_head.addWidget(self.player_mode_combo)
        preview_head.addWidget(QLabel("预览画幅"))
        preview_head.addWidget(self.preview_ratio_combo)
        preview_head.addWidget(self.playback_options_btn)
        preview_head.addWidget(self.open_editor_popup_btn)
        preview_head.addWidget(self.max_preview_btn)
        preview_head.addWidget(self.fullscreen_btn)
        preview_head.addStretch()
        pg.addLayout(preview_head)

        self.video_stage = QFrame()
        self.video_stage.setObjectName("videoStage")
        stage_l = QVBoxLayout(self.video_stage)
        stage_l.setContentsMargins(12, 12, 12, 12)
        stage_l.setSpacing(8)

        self.player_title_row = QHBoxLayout()
        self.player_badge = QPushButton("沉浸式学习")
        self.player_badge.setObjectName("playerBadge")
        self.player_badge.setCheckable(True)
        self.player_badge.clicked.connect(self.toggle_immersive_mode)
        self.player_title = QLabel("未选择预览项")
        self.player_title.setObjectName("playerTitle")
        self.player_hint = QLabel("双击搜索结果可自动加入预览并播放；暂停时可点单词查释义")
        self.player_hint.setObjectName("playerHint")
        self.player_title_row.addWidget(self.player_badge, 0)
        self.player_title_row.addWidget(self.player_title, 1)
        self.player_title_row.addWidget(self.player_hint, 0)
        stage_l.addLayout(self.player_title_row)

        self.video_splitter = QSplitter(Qt.Horizontal)
        self.video_splitter.setChildrenCollapsible(False)
        self.video_splitter.setHandleWidth(6)

        self.video_learning_pane = QWidget()
        vll = QVBoxLayout(self.video_learning_pane)
        vll.setContentsMargins(0, 0, 0, 0)
        vll.setSpacing(10)
        vll.addWidget(self.video_frame, 1)

        self.subtitle_panel = QFrame()
        self.subtitle_panel.setObjectName('subtitlePanel')
        spl = QVBoxLayout(self.subtitle_panel)
        spl.setContentsMargins(18, 12, 18, 12)
        spl.setSpacing(8)
        self.subtitle_en_label = QLabel('')
        self.subtitle_en_label.setObjectName('subtitleEn')
        self.subtitle_en_label.setWordWrap(True)
        self.subtitle_en_label.setAlignment(Qt.AlignCenter)
        self.subtitle_zh_label = QLabel('')
        self.subtitle_zh_label.setObjectName('subtitleZh')
        self.subtitle_zh_label.setWordWrap(True)
        self.subtitle_zh_label.setAlignment(Qt.AlignCenter)
        self.clickable_subtitle_browser = QTextBrowser()
        self.clickable_subtitle_browser.setObjectName('clickableSubtitle')
        self.clickable_subtitle_browser.setOpenLinks(False)
        self.clickable_subtitle_browser.setMaximumHeight(84)
        self.clickable_subtitle_browser.anchorClicked.connect(self.on_subtitle_word_clicked)
        self.clickable_subtitle_browser.hide()
        sub_copy_row = QHBoxLayout()
        self.copy_en_btn = QPushButton("复制英文")
        self.copy_en_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.subtitle_en_label.text().strip()))
        self.copy_zh_btn = QPushButton("复制中文")
        self.copy_zh_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.subtitle_zh_label.text().strip()))
        sub_copy_row.addWidget(self.copy_en_btn)
        sub_copy_row.addWidget(self.copy_zh_btn)
        sub_copy_row.addStretch()
        spl.addLayout(sub_copy_row)
        spl.addWidget(self.subtitle_en_label)
        spl.addWidget(self.subtitle_zh_label)
        spl.addWidget(self.clickable_subtitle_browser)
        vll.addWidget(self.subtitle_panel, 0)

        self.immersive_side_panel = QFrame()
        self.immersive_side_panel.setObjectName('immersiveSidePanel')
        isp = QVBoxLayout(self.immersive_side_panel)
        isp.setContentsMargins(10, 10, 10, 10)
        isp.setSpacing(8)
        self.immersive_side_title = QLabel('沉浸式学习 / 预览列表')
        self.immersive_side_title.setObjectName('immersiveSideTitle')
        isp.addWidget(self.immersive_side_title)
        top_immersive_bar = QHBoxLayout()
        self.immersive_exit_btn = QPushButton("退出沉浸式学习")
        self.immersive_exit_btn.clicked.connect(lambda: self.set_immersive_mode(False))
        self.immersive_copy_en_btn = QPushButton("复制英文")
        self.immersive_copy_en_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.subtitle_en_label.text().strip()))
        self.immersive_copy_zh_btn = QPushButton("复制中文")
        self.immersive_copy_zh_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.subtitle_zh_label.text().strip()))
        top_immersive_bar.addWidget(self.immersive_exit_btn)
        top_immersive_bar.addWidget(self.immersive_copy_en_btn)
        top_immersive_bar.addWidget(self.immersive_copy_zh_btn)
        top_immersive_bar.addStretch()
        isp.addLayout(top_immersive_bar)
        self.immersive_queue_list = QListWidget()
        self.immersive_queue_list.itemSelectionChanged.connect(self.sync_immersive_queue_selection)
        self.immersive_queue_list.itemDoubleClicked.connect(lambda _=None: self.preview_current_queue_item())
        isp.addWidget(self.immersive_queue_list, 2)
        self.current_translation_label = QLabel('当前双语对照会显示在这里')
        self.current_translation_label.setObjectName('translationCard')
        self.current_translation_label.setWordWrap(True)
        isp.addWidget(self.current_translation_label, 0)
        self.word_info_browser = QTextBrowser()
        self.word_info_browser.setObjectName('wordInfoBrowser')
        self.word_info_browser.setOpenLinks(False)
        isp.addWidget(self.word_info_browser, 1)
        word_btn_row = QHBoxLayout()
        self.pronounce_btn = QPushButton('🔊 发音')
        self.pronounce_btn.clicked.connect(self.play_current_word_audio)
        self.pronounce_btn.setEnabled(False)
        word_btn_row.addWidget(self.pronounce_btn)
        word_btn_row.addStretch()
        isp.addLayout(word_btn_row)
        self.immersive_side_panel.hide()

        self.video_splitter.addWidget(self.video_learning_pane)
        self.video_splitter.addWidget(self.immersive_side_panel)
        self.video_splitter.setSizes([1200, 420])
        stage_l.addWidget(self.video_splitter, 1)

        progress_row = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setObjectName("timePill")
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setObjectName("seekSlider")
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self.on_seek_slider_moved)
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setObjectName("timePill")
        progress_row.addWidget(self.current_time_label)
        progress_row.addWidget(self.seek_slider, 1)
        progress_row.addWidget(self.total_time_label)
        stage_l.addLayout(progress_row)

        controls_bar = QFrame()
        controls_bar.setObjectName("transportBar")
        cb = QHBoxLayout(controls_bar)
        cb.setContentsMargins(12, 8, 12, 8)
        cb.setSpacing(10)
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn = QPushButton("■ 停止")
        self.stop_btn.clicked.connect(self.stop_playback)
        self.loop_mode_btn = QComboBox()
        self.loop_mode_btn.addItems(["单个循环", "列表循环"])
        self.loop_mode_btn.currentIndexChanged.connect(self.on_loop_mode_changed)
        self.repeat_count_spin = QSpinBox()
        self.repeat_count_spin.setRange(1, 999)
        self.repeat_count_spin.setValue(1)
        self.repeat_count_spin.setToolTip("自定义循环次数，支持 1-999")
        self.repeat_count_spin.valueChanged.connect(self.on_repeat_count_spin_changed)
        self.repeat_forever_cb = QCheckBox("无限")
        self.repeat_forever_cb.toggled.connect(self.on_repeat_forever_toggled)
        self.preview_btn_2 = QPushButton("▶ 播放预览列表")
        self.preview_btn_2.clicked.connect(self.preview_current_queue_item)
        self.playback_options_btn_2 = QPushButton("播放选项 ▾")
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setCheckable(True)
        self.mute_btn.toggled.connect(self.toggle_mute)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        self.preview_label = QLabel("未选择预览项")
        self.preview_label.setObjectName("transportTitle")
        for w in [self.play_btn, self.stop_btn, self.preview_btn_2]:
            cb.addWidget(w)
        cb.addWidget(QLabel("循环模式"))
        cb.addWidget(self.loop_mode_btn)
        cb.addWidget(QLabel("循环次数"))
        cb.addWidget(self.repeat_count_spin)
        cb.addWidget(self.repeat_forever_cb)
        cb.addWidget(self.preview_label, 1)
        cb.addWidget(self.playback_options_btn_2)
        cb.addWidget(self.mute_btn)
        cb.addWidget(self.volume_slider)
        stage_l.addWidget(controls_bar)

        self.player_footer = QLabel("就绪 · 双击搜索结果可直接加入预览")
        self.player_footer.setObjectName("playerFooter")
        stage_l.addWidget(self.player_footer)

        pg.addWidget(self.video_stage, 1)
        right_l.addWidget(preview_group, 1)

        # 主界面不显示剪辑设置，只保留弹出式剪辑工作台
        self.project_name_edit = QLineEdit("商业成片")
        self.subtitle_edit = QTextEdit()
        self.subtitle_edit.setFixedHeight(88)
        self.zh_subtitle_edit = QTextEdit()
        self.zh_subtitle_edit.setFixedHeight(72)
        self.trim_start_spin = QSpinBox()
        self.trim_start_spin.setRange(0, 3600)
        self.trim_end_spin = QSpinBox()
        self.trim_end_spin.setRange(0, 3600)
        self.subtitle_font_spin = QSpinBox()
        self.subtitle_font_spin.setRange(28, 100)
        self.subtitle_font_spin.setValue(56)
        self.export_subtitle_mode = QComboBox()
        self.export_subtitle_mode.addItems(["无字幕", "英文", "中文", "双语"])
        self.export_subtitle_mode.setCurrentText("双语")
        self.aspect_ratio_combo = QComboBox()
        self.aspect_ratio_combo.addItems(list(ASPECT_PRESETS.keys()))
        self.aspect_ratio_combo.setCurrentText("9:16 竖版")
        self.preview_subtitle_mode = QComboBox()
        self.preview_subtitle_mode.addItems(["无字幕", "英文", "中文", "双语"])
        self.preview_subtitle_mode.setCurrentText("双语")
        self.preview_subtitle_mode.currentTextChanged.connect(self.refresh_preview_subtitle_overlay)
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self.apply_playback_speed)
        self.loop_scope_combo = QComboBox()
        self.loop_scope_combo.addItems(["选中循环", "全部循环"])
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 999)
        self.repeat_spin.setValue(1)
        self.repeat_spin.valueChanged.connect(lambda v: self.repeat_count_spin.setValue(v) if hasattr(self, 'repeat_count_spin') and self.repeat_count_spin.value() != v else None)
        self.auto_next_cb = QCheckBox("播完次数后自动下一个")
        self.auto_next_cb.setChecked(True)
        self.subtitle_translate_engine = QComboBox()
        self.subtitle_translate_engine.addItems(["内置翻译", "MyMemory 免费", "LibreTranslate 免费"])
        self.potplayer_edit = QLineEdit(find_potplayer())
        self.potplayer_edit.setPlaceholderText("选择 PotPlayer 主程序")
        self.choose_pot_btn = QPushButton("选择 PotPlayer")
        self.choose_pot_btn.clicked.connect(self.choose_potplayer)
        self.current_pot_btn = QPushButton("PotPlayer 打开当前")
        self.current_pot_btn.clicked.connect(self.open_current_in_potplayer)
        self.last_export_pot_btn = QPushButton("PotPlayer 打开成片")
        self.last_export_pot_btn.clicked.connect(self.open_last_export_in_potplayer)
        self.export_btn = QPushButton("导出并合成 MP4")
        self.export_btn.clicked.connect(self.start_export)
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0, 0)
        self.export_progress.hide()
        self.editor_panel = QWidget()
        self.toggle_editor_panel_btn = QPushButton("隐藏剪辑区")
        self.editor_hint_label = QLabel("主界面不显示剪辑设置，请使用剪辑工作台。")

        self.build_playback_menu()
        self.playback_options_btn.setMenu(self.playback_menu)
        self.playback_options_btn_2.setMenu(self.playback_menu)
        self.main_splitter.setSizes([760, 960])
        self.apply_preview_aspect()
        self.apply_player_theme("奶油樱花房")
        self.apply_font_area_styles()
        self.install_custom_shortcuts()

    
    def apply_player_theme(self, theme_name: str):
        theme_name = (theme_name or "奶油樱花房").strip()
        themes = {
            "奶油樱花房": {
                "window_bg": "#fff8fb", "window_fg": "#5b4b57", "header1": "#ffe8f0", "header2": "#f8dce8",
                "header3": "#f6cddc", "border": "#e8bfd1", "group_bg1": "#fff4f8", "group_bg2": "#fdeef4",
                "group_title": "#b96f95", "input_bg": "#fffdfd", "input_fg": "#5b4b57", "select_bg": "#f6cade",
                "button1": "#efb6cf", "button2": "#d990b1", "button_hover": "#f3c1d7", "button_press": "#cf7fa6",
                "tab_bg": "#fdf0f5", "tab_sel": "#f7d6e4", "tab_text": "#8c5d78", "chunk": "#f2a9c4",
                "handle": "#f1c6d9", "video_card": "#fff8fb", "video_stage1": "#fff4f8", "video_stage2": "#f8e9f0",
                "transport_bg": "rgba(255,245,249,0.96)", "player_badge_bg": "#ffd9e8", "player_badge_fg": "#874e68",
                "player_title": "#7b5870", "player_hint": "#b17e98", "time_pill_bg": "#fff6f9", "time_pill_fg": "#8d5b76",
                "accent": "#d987ac", "accent2": "#efb6cf", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(255,248,251,0.95)",
                "subtitle_en": "#6d5263", "subtitle_zh": "#c0789b", "side_bg": "rgba(255,243,248,0.97)", "side_title": "#b4688f",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#ecc7d7", "word_bg": "#fffdfd",
                "word_border": "#ecd5df", "word_fg": "#5b4b57"
            },
            "薰衣草卧室": {
                "window_bg": "#faf7ff", "window_fg": "#544d65", "header1": "#f1ebff", "header2": "#e8dcff",
                "header3": "#dccaf9", "border": "#d3c2ec", "group_bg1": "#f8f4ff", "group_bg2": "#f2ecff",
                "group_title": "#8c73c2", "input_bg": "#ffffff", "input_fg": "#544d65", "select_bg": "#e5d9ff",
                "button1": "#c6b0f4", "button2": "#ac92df", "button_hover": "#d2bef7", "button_press": "#9f85d8",
                "tab_bg": "#f3edff", "tab_sel": "#e5d8ff", "tab_text": "#7963a8", "chunk": "#bea7ee",
                "handle": "#d5c8f0", "video_card": "#faf7ff", "video_stage1": "#f3eeff", "video_stage2": "#ece3ff",
                "transport_bg": "rgba(247,243,255,0.96)", "player_badge_bg": "#e6dbff", "player_badge_fg": "#6f5a9e",
                "player_title": "#64597e", "player_hint": "#8f81aa", "time_pill_bg": "#faf7ff", "time_pill_fg": "#75689a",
                "accent": "#a78cde", "accent2": "#c6b0f4", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(248,244,255,0.95)",
                "subtitle_en": "#5a4f74", "subtitle_zh": "#8f79c8", "side_bg": "rgba(245,240,255,0.97)", "side_title": "#8570bd",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#d8c8f1", "word_bg": "#ffffff",
                "word_border": "#e2d8f1", "word_fg": "#544d65"
            },
            "原木奶白房": {
                "window_bg": "#fcfaf7", "window_fg": "#5a4d44", "header1": "#f7f1ea", "header2": "#efe4d8",
                "header3": "#e7d5c2", "border": "#d9c6b1", "group_bg1": "#fbf6f0", "group_bg2": "#f4ece3",
                "group_title": "#a47c5f", "input_bg": "#fffefe", "input_fg": "#5a4d44", "select_bg": "#efe1d2",
                "button1": "#d7b79c", "button2": "#be9876", "button_hover": "#e0c4ae", "button_press": "#b18966",
                "tab_bg": "#f7f1ea", "tab_sel": "#eadbcb", "tab_text": "#8d6d54", "chunk": "#d0b296",
                "handle": "#e1cfbf", "video_card": "#fffdfa", "video_stage1": "#f8f3ed", "video_stage2": "#efe6dc",
                "transport_bg": "rgba(250,246,241,0.96)", "player_badge_bg": "#efe0d1", "player_badge_fg": "#855f43",
                "player_title": "#6a574a", "player_hint": "#9b836f", "time_pill_bg": "#fffaf6", "time_pill_fg": "#8a705c",
                "accent": "#c79d7a", "accent2": "#d7b79c", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(252,249,245,0.96)",
                "subtitle_en": "#5f4f44", "subtitle_zh": "#b38867", "side_bg": "rgba(249,243,235,0.97)", "side_title": "#a17b60",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#e4d4c6", "word_bg": "#fffdfb",
                "word_border": "#e6d7ca", "word_fg": "#5a4d44"
            },
            "夜灯粉紫房": {
                "window_bg": "#fff7fe", "window_fg": "#5a4b63", "header1": "#ffeaf7", "header2": "#f0defc",
                "header3": "#e4caf5", "border": "#d8b7e8", "group_bg1": "#fff4fb", "group_bg2": "#f8eefb",
                "group_title": "#a26cba", "input_bg": "#fffefe", "input_fg": "#5a4b63", "select_bg": "#efd8fb",
                "button1": "#d7a8ea", "button2": "#c487df", "button_hover": "#e1bcf0", "button_press": "#ba78d6",
                "tab_bg": "#fbf0fd", "tab_sel": "#efdaf8", "tab_text": "#905fa8", "chunk": "#d09ae6",
                "handle": "#ebc8f7", "video_card": "#fff8ff", "video_stage1": "#fff1fb", "video_stage2": "#f8e9fb",
                "transport_bg": "rgba(255,246,252,0.96)", "player_badge_bg": "#f7ddff", "player_badge_fg": "#8a54a4",
                "player_title": "#6f577c", "player_hint": "#a17cb5", "time_pill_bg": "#fff7fd", "time_pill_fg": "#8f67a5",
                "accent": "#c38bdf", "accent2": "#d7a8ea", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(255,248,252,0.96)",
                "subtitle_en": "#654f72", "subtitle_zh": "#b77fd1", "side_bg": "rgba(253,244,252,0.97)", "side_title": "#9d69b9",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#e8d0f2", "word_bg": "#fffefe",
                "word_border": "#ecdaf3", "word_fg": "#5a4b63"
            },
            "草莓奶昔房": {
                "window_bg": "#fff7f7", "window_fg": "#654b50", "header1": "#ffe7ea", "header2": "#ffd8df",
                "header3": "#f8c0cc", "border": "#ebb5c0", "group_bg1": "#fff2f4", "group_bg2": "#ffecef",
                "group_title": "#c56f84", "input_bg": "#fffefe", "input_fg": "#654b50", "select_bg": "#ffd5de",
                "button1": "#f0a9bb", "button2": "#de839b", "button_hover": "#f5b8c7", "button_press": "#d5728c",
                "tab_bg": "#fff0f2", "tab_sel": "#ffd9e0", "tab_text": "#a16072", "chunk": "#ec9eb0",
                "handle": "#f2c4cf", "video_card": "#fffafa", "video_stage1": "#fff2f4", "video_stage2": "#ffe6eb",
                "transport_bg": "rgba(255,245,246,0.96)", "player_badge_bg": "#ffd9df", "player_badge_fg": "#97576b",
                "player_title": "#7c5961", "player_hint": "#ba7d8f", "time_pill_bg": "#fff8f9", "time_pill_fg": "#9a6274",
                "accent": "#dd7e97", "accent2": "#f0a9bb", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(255,248,248,0.96)",
                "subtitle_en": "#6c5157", "subtitle_zh": "#d07289", "side_bg": "rgba(255,242,244,0.97)", "side_title": "#c86e84",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#efc8d0", "word_bg": "#fffefe",
                "word_border": "#efd8dd", "word_fg": "#654b50"
            },
            "晨雾玫瑰房": {
                "window_bg": "#fdf8f8", "window_fg": "#5d4f54", "header1": "#f9eeee", "header2": "#f5e3e5",
                "header3": "#eed0d6", "border": "#ddc1c8", "group_bg1": "#fcf5f6", "group_bg2": "#f8eef0",
                "group_title": "#ae7988", "input_bg": "#fffefe", "input_fg": "#5d4f54", "select_bg": "#f3dbe0",
                "button1": "#d9a4b5", "button2": "#bc8697", "button_hover": "#e1b7c4", "button_press": "#ae7487",
                "tab_bg": "#faf1f2", "tab_sel": "#eedadf", "tab_text": "#8f6874", "chunk": "#d596aa",
                "handle": "#e8c7cf", "video_card": "#fffdfd", "video_stage1": "#faf2f3", "video_stage2": "#f6e7ea",
                "transport_bg": "rgba(250,244,245,0.96)", "player_badge_bg": "#f1dde2", "player_badge_fg": "#825d68",
                "player_title": "#6d5860", "player_hint": "#a6818c", "time_pill_bg": "#fffafa", "time_pill_fg": "#8a6771",
                "accent": "#bc8697", "accent2": "#d9a4b5", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(253,248,248,0.96)",
                "subtitle_en": "#65545a", "subtitle_zh": "#b07b8b", "side_bg": "rgba(250,243,244,0.97)", "side_title": "#a97686",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#e7d2d7", "word_bg": "#fffefe",
                "word_border": "#ead9dd", "word_fg": "#5d4f54"
            },
            "薄荷手账房": {
                "window_bg": "#f7fffb", "window_fg": "#4f5f58", "header1": "#e9fbf2", "header2": "#d9f5e8",
                "header3": "#c1ead8", "border": "#b8dbc9", "group_bg1": "#f3fcf7", "group_bg2": "#ebf8f1",
                "group_title": "#69a186", "input_bg": "#ffffff", "input_fg": "#4f5f58", "select_bg": "#d4f0e2",
                "button1": "#9fd8bf", "button2": "#7fbe9e", "button_hover": "#b2e0cc", "button_press": "#72b18f",
                "tab_bg": "#effbf5", "tab_sel": "#dff3e8", "tab_text": "#5f8f77", "chunk": "#92cfb4",
                "handle": "#c8ebda", "video_card": "#fcfffd", "video_stage1": "#eefbf5", "video_stage2": "#e2f4eb",
                "transport_bg": "rgba(245,254,248,0.96)", "player_badge_bg": "#d7f1e4", "player_badge_fg": "#4f8f72",
                "player_title": "#56685f", "player_hint": "#799a8d", "time_pill_bg": "#fafffc", "time_pill_fg": "#5f8f77",
                "accent": "#7fbe9e", "accent2": "#9fd8bf", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(248,255,251,0.96)",
                "subtitle_en": "#51625b", "subtitle_zh": "#6fa78b", "side_bg": "rgba(243,252,247,0.97)", "side_title": "#679d84",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#d2e8dc", "word_bg": "#ffffff",
                "word_border": "#dcebdf", "word_fg": "#4f5f58"
            },
            "月光银杏房": {
                "window_bg": "#fffdf7", "window_fg": "#5d584a", "header1": "#fff8e9", "header2": "#f9efd1",
                "header3": "#f0e0ac", "border": "#e0d0a2", "group_bg1": "#fffaf0", "group_bg2": "#faf4e1",
                "group_title": "#a7914f", "input_bg": "#fffefc", "input_fg": "#5d584a", "select_bg": "#f7edc7",
                "button1": "#e3cf8d", "button2": "#cdb86b", "button_hover": "#eadaa6", "button_press": "#c1a959",
                "tab_bg": "#fff8e8", "tab_sel": "#f5eac2", "tab_text": "#8f7b3c", "chunk": "#dac56f",
                "handle": "#efe2ad", "video_card": "#fffef9", "video_stage1": "#fff9ea", "video_stage2": "#f8efd3",
                "transport_bg": "rgba(255,251,239,0.96)", "player_badge_bg": "#f8ecc2", "player_badge_fg": "#88753a",
                "player_title": "#736a4d", "player_hint": "#a69869", "time_pill_bg": "#fffdf7", "time_pill_fg": "#8f7d45",
                "accent": "#c8ad59", "accent2": "#e3cf8d", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(255,253,245,0.96)",
                "subtitle_en": "#686049", "subtitle_zh": "#b69b41", "side_bg": "rgba(255,250,239,0.97)", "side_title": "#a28d49",
                "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#eadfb9", "word_bg": "#fffefb",
                "word_border": "#ece4cb", "word_fg": "#5d584a"
            }
        }
        themes.update(EXTRA_PLAYER_THEMES)
        cfg = themes.get(theme_name, themes["奶油樱花房"])
        self.current_theme_name = theme_name
        self.current_theme_cfg = cfg
        self.font_area_settings["subtitle_en"]["color"] = cfg.get("subtitle_en", self.font_area_settings["subtitle_en"]["color"])
        self.font_area_settings["subtitle_zh"]["color"] = cfg.get("subtitle_zh", self.font_area_settings["subtitle_zh"]["color"])
        self.font_area_settings["title"]["color"] = cfg.get("player_title", self.font_area_settings["title"]["color"])
        self.setStyleSheet(self._build_stylesheet())
        frame_css = (
            f"QFrame#videoCard{{background:{cfg['video_card']};border:2px solid {cfg['border']};border-radius:18px;}}"
            f"QFrame#subtitlePanel{{background:{cfg['subtitle_panel_bg']};border:1px solid {cfg['border']};border-radius:16px;}}"
            f"QLabel#previewBanner{{background:{cfg['transport_bg']};color:{cfg['player_title']};border:1px solid {cfg['border']};border-radius:10px;padding:8px 12px;font-weight:800;}}"
            f"QPushButton#playAccentButton{{background:{cfg['accent']};border:1px solid {cfg['border']};border-radius:12px;padding:8px 14px;color:{cfg['accent_fg']};font-weight:800;}}"
        )
        for widget_name in ['video_frame', 'subtitle_panel']:
            w = getattr(self, widget_name, None)
            if w is not None:
                w.setStyleSheet(frame_css)
        for btn_name in ['play_btn', 'stop_btn', 'add_preview_btn', 'show_queue_btn', 'playback_options_btn', 'playback_options_btn_2']:
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setObjectName('playAccentButton')
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        self.update()

    def build_playback_menu(self):
        menu = QMenu(self)
        self.playback_menu = menu
        theme_menu = menu.addMenu("播放器主题")
        for theme in ["奶油樱花房", "薰衣草卧室", "原木奶白房", "夜灯粉紫房", "草莓奶昔房", "晨雾玫瑰房", "薄荷手账房", "月光银杏房", "梦幻星空", "儿童乐园", "动物世界", "海底世界", "恐龙侏罗纪", "精灵天使", "暧昧空间", "极简风格", "护眼模式"]:
            act = theme_menu.addAction(theme)
            act.triggered.connect(lambda checked=False, t=theme: self.player_theme_combo.setCurrentText(t))

        subtitle_menu = menu.addMenu("预览字幕")
        for mode in ["无字幕", "英文", "中文", "双语"]:
            act = subtitle_menu.addAction(mode)
            act.triggered.connect(lambda checked=False, m=mode: self.preview_subtitle_mode.setCurrentText(m))

        speed_menu = menu.addMenu("播放速度")
        for speed in ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"]:
            act = speed_menu.addAction(speed)
            act.triggered.connect(lambda checked=False, s=speed: self.speed_combo.setCurrentText(s))

        loop_menu = menu.addMenu("循环模式")
        act_single = loop_menu.addAction("单个循环")
        act_single.triggered.connect(lambda checked=False: self.loop_scope_combo.setCurrentIndex(0))
        act_list = loop_menu.addAction("列表循环")
        act_list.triggered.connect(lambda checked=False: self.loop_scope_combo.setCurrentIndex(1))

        repeat_menu = menu.addMenu("重复次数")
        for n in [1, 2, 3, 5, 10, 20, 50, 100]:
            act = repeat_menu.addAction(str(n))
            act.triggered.connect(lambda checked=False, v=n: (self.repeat_count_spin.setValue(v), self.repeat_spin.setValue(v)))
        repeat_menu.addSeparator()
        repeat_menu.addAction("切换无限循环", lambda: self.repeat_forever_cb.toggle())

        menu.addSeparator()
        view_menu = menu.addMenu("控制条显示")
        view_menu.addAction("隐藏上方功能按钮", lambda: self.set_top_controls_visible(False))
        view_menu.addAction("隐藏下方功能按钮", lambda: self.set_bottom_controls_visible(False))
        view_menu.addAction("全部隐藏", lambda: self.set_control_bars_visible(False, False))
        view_menu.addAction("全部显示", lambda: self.set_control_bars_visible(True, True))

        font_menu = menu.addMenu("字体样式（20种）")
        for area_label, area_key in [("搜索框字体","search"),("搜索结果字体","results"),("预览列表字体","queue"),("英文字幕字体","subtitle_en"),("中文字幕字体","subtitle_zh")]:
            subm = font_menu.addMenu(area_label)
            for fam in FONT_STYLE_PRESETS:
                subm.addAction(fam, lambda checked=False, a=area_key, f=fam: self.update_font_area(a, family=f))
            subm.addSeparator()
            subm.addAction("字体颜色...", lambda checked=False, a=area_key: self.choose_font_color(a))

        menu.addAction("自定义快捷键面板", self.build_shortcuts_dialog)
        menu.addSeparator()
        act_preview = menu.addAction("播放当前结果")
        act_preview.triggered.connect(self.preview_current_result)
        act_queue = menu.addAction("播放预览列表选中项")
        act_queue.triggered.connect(self.preview_current_queue_item)
        act_add = menu.addAction("把当前结果加入预览列表")
        act_add.triggered.connect(self.add_current_to_preview)
        act_immersive = menu.addAction("切换沉浸式学习")
        act_immersive.triggered.connect(lambda: self.set_immersive_mode(not self.immersive_mode))
        act_immersive.triggered.connect(self.toggle_immersive_mode)
        menu.addSeparator()
        act_open_current = menu.addAction("PotPlayer 打开当前")
        act_open_current.triggered.connect(self.open_current_in_potplayer)
        act_choose_pot = menu.addAction("选择 PotPlayer")
        act_choose_pot.triggered.connect(self.choose_potplayer)
        self.playback_options_btn.setMenu(menu)
        self.playback_options_btn_2.setMenu(menu)

    def handle_result_double_click(self, item_widget):
        item = self.current_result_item()
        if not item and item_widget is not None:
            self.result_list.setCurrentItem(item_widget)
            item = self.current_result_item()
        if not item:
            self.append_log("双击失败：当前结果为空")
            return
        self.add_current_to_preview(preview_now=True)

    def add_current_to_preview(self, preview_now: bool = False):
        item = self.current_result_item()
        if not item:
            self.append_log("加入预览失败：当前没有选中搜索结果")
            return
        item_key = item.source_id or item.video_url or extract_transcribed_text(item)
        existing = {q.source_id or q.video_url or extract_transcribed_text(q) for q in self.queue_items}
        if item_key not in existing:
            clone = PhraseItem(**asdict(item))
            clone.selected = True
            self.queue_items.append(clone)
            self.refresh_queue_list()
            self.queue_list.setCurrentRow(len(self.queue_items) - 1)
            self.append_log(f"已加入预览列表：{clone.display_title()}")
        else:
            for idx, q in enumerate(self.queue_items):
                key = q.source_id or q.video_url or extract_transcribed_text(q)
                if key == item_key:
                    self.queue_list.setCurrentRow(idx)
                    break
            self.append_log("该条目已在预览列表中，已自动定位")
        if preview_now or len(self.queue_items) == 1:
            self.preview_current_queue_item()

    def _build_batch_tab(self):
        layout = QVBoxLayout(self.batch_tab)
        top = QGroupBox("批量下载原片")
        form = QGridLayout(top)
        self.batch_info = QLabel("从当前搜索结果中勾选后，在这里下载原始片段，不做字幕和合成。")
        self.batch_select_all_btn = QPushButton("当前搜索结果全选")
        self.batch_select_all_btn.clicked.connect(self.select_all_results)
        self.batch_clear_all_btn = QPushButton("当前搜索结果全不选")
        self.batch_clear_all_btn.clicked.connect(self.unselect_all_results)
        self.batch_download_btn = QPushButton("下载勾选结果")
        self.batch_download_btn.clicked.connect(self.start_batch_download)
        self.batch_progress = QProgressBar()
        self.batch_progress.setRange(0, 0)
        self.batch_progress.hide()
        form.addWidget(self.batch_info, 0, 0, 1, 3)
        form.addWidget(self.batch_select_all_btn, 1, 0)
        form.addWidget(self.batch_clear_all_btn, 1, 1)
        form.addWidget(self.batch_download_btn, 1, 2)
        form.addWidget(self.batch_progress, 2, 0, 1, 3)
        layout.addWidget(top)
        self.batch_preview = QPlainTextEdit()
        self.batch_preview.setReadOnly(True)
        self.batch_preview.setPlainText("这里会显示即将批量下载的条目列表。")
        layout.addWidget(self.batch_preview, 1)

    def _build_docs_tab(self):
        layout = QVBoxLayout(self.docs_tab)
        box = QGroupBox("导出搜索结果文档")
        form = QFormLayout(box)
        self.doc_name_edit = QLineEdit("搜索结果导出")

        fmt_row = QWidget()
        fmt_l = QHBoxLayout(fmt_row)
        fmt_l.setContentsMargins(0, 0, 0, 0)
        self.fmt_txt_cb = QCheckBox("TXT")
        self.fmt_txt_cb.setChecked(True)
        self.fmt_doc_cb = QCheckBox("DOC")
        self.fmt_pdf_cb = QCheckBox("PDF")
        self.fmt_xlsx_cb = QCheckBox("EXCEL")
        for w in [self.fmt_txt_cb, self.fmt_doc_cb, self.fmt_pdf_cb, self.fmt_xlsx_cb]:
            fmt_l.addWidget(w)
        fmt_l.addStretch()

        field_row = QWidget()
        field_l = QHBoxLayout(field_row)
        field_l.setContentsMargins(0, 0, 0, 0)
        self.field_sentence_cb = QCheckBox("只导出台词")
        self.field_sentence_cb.setChecked(True)
        self.field_rank_cb = QCheckBox("序号")
        self.field_year_cb = QCheckBox("年份")
        self.field_movie_cb = QCheckBox("影片")
        self.field_url_cb = QCheckBox("视频链接")
        self.field_translation_cb = QCheckBox("翻译")
        for w in [self.field_sentence_cb, self.field_rank_cb, self.field_year_cb, self.field_movie_cb, self.field_url_cb, self.field_translation_cb]:
            field_l.addWidget(w)
        field_l.addStretch()

        trans_row = QWidget()
        trans_l = QHBoxLayout(trans_row)
        trans_l.setContentsMargins(0, 0, 0, 0)
        self.doc_translate_cb = QCheckBox("下载时翻译")
        self.doc_translate_engine = QComboBox()
        self.doc_translate_engine.addItems(["内置翻译", "MyMemory 免费", "LibreTranslate 免费"])
        trans_l.addWidget(self.doc_translate_cb)
        trans_l.addWidget(QLabel("翻译引擎"))
        trans_l.addWidget(self.doc_translate_engine)
        trans_l.addStretch()

        self.doc_export_btn = QPushButton("按所选格式导出")
        self.doc_export_btn.clicked.connect(self.export_current_search_docs)
        self.doc_hint = QLabel("支持只导出台词，或勾选附加字段；也可勾选翻译。")

        form.addRow("文档基础名", self.doc_name_edit)
        form.addRow("导出格式", fmt_row)
        form.addRow("导出字段", field_row)
        form.addRow("翻译选项", trans_row)
        form.addRow("", self.doc_export_btn)
        form.addRow("", self.doc_hint)
        layout.addWidget(box)

        self.doc_preview = QPlainTextEdit()
        self.doc_preview.setReadOnly(True)
        self.doc_preview.setPlainText("导出预览：默认只导出台词。")
        layout.addWidget(self.doc_preview, 1)

    def _build_ai_tab(self):
        layout = QVBoxLayout(self.ai_tab)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)
        self.resource_views = {}
        for category, sites in RESOURCES.items():
            cat_tabs = QTabWidget()
            for title, url in sites.items():
                page = WebLoginTab(title, url)
                if WEB_OK and getattr(page, "view", None):
                    self.resource_views[title] = page.view
                cat_tabs.addTab(page, title)
            tabs.addTab(cat_tabs, category)

    def _build_log_tab(self):
        layout = QVBoxLayout(self.log_tab)
        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        layout.addWidget(self.log_edit)

    
    def _build_stylesheet(self):
        base = getattr(self, "base_font_px", 14)
        hero = base + 18
        sub = max(12, base - 1)
        cfg = getattr(self, "current_theme_cfg", None) or {
            "window_bg": "#fff8fb", "window_fg": "#5b4b57", "header1": "#ffe8f0", "header2": "#f8dce8",
            "header3": "#f6cddc", "border": "#e8bfd1", "group_bg1": "#fff4f8", "group_bg2": "#fdeef4",
            "group_title": "#b96f95", "input_bg": "#fffdfd", "input_fg": "#5b4b57", "select_bg": "#f6cade",
            "button1": "#efb6cf", "button2": "#d990b1", "button_hover": "#f3c1d7", "button_press": "#cf7fa6",
            "tab_bg": "#fdf0f5", "tab_sel": "#f7d6e4", "tab_text": "#8c5d78", "chunk": "#f2a9c4",
            "handle": "#f1c6d9", "video_card": "#fff8fb", "video_stage1": "#fff4f8", "video_stage2": "#f8e9f0",
            "transport_bg": "rgba(255,245,249,0.96)", "player_badge_bg": "#ffd9e8", "player_badge_fg": "#874e68",
            "player_title": "#7b5870", "player_hint": "#b17e98", "time_pill_bg": "#fff6f9", "time_pill_fg": "#8d5b76",
            "accent": "#d987ac", "accent2": "#efb6cf", "accent_fg": "#ffffff", "subtitle_panel_bg": "rgba(255,248,251,0.95)",
            "subtitle_en": "#6d5263", "subtitle_zh": "#c0789b", "side_bg": "rgba(255,243,248,0.97)", "side_title": "#b4688f",
            "translation_bg": "rgba(255,255,255,0.82)", "translation_border": "#ecc7d7", "word_bg": "#fffdfd",
            "word_border": "#ecd5df", "word_fg": "#5b4b57"
        }
        return f"""
        QMainWindow, QWidget {{ background: {cfg['window_bg']}; color: {cfg['window_fg']}; font-size: {base}px; }}
        #header {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {cfg['header1']}, stop:0.55 {cfg['header2']}, stop:1 {cfg['header3']});
            border: 1px solid {cfg['border']}; border-radius: 24px; padding: 12px;
        }}
        QLabel#heroTitle {{ font-size: {hero}px; font-weight: 900; color: {cfg['player_title']}; }}
        QLabel#heroSub {{ font-size: {sub}px; color: {cfg['player_hint']}; }}
        QGroupBox {{
            border: 1px solid {cfg['border']}; border-radius: 20px; margin-top: 14px; font-weight: 800;
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {cfg['group_bg1']}, stop:1 {cfg['group_bg2']});
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 16px; padding: 0 8px; color: {cfg['group_title']}; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QListWidget, QTextBrowser {{
            background: {cfg['input_bg']}; border: 1px solid {cfg['border']}; border-radius: 14px; padding: 8px; color: {cfg['input_fg']};
            selection-background-color: {cfg['select_bg']};
        }}
        QListWidget::item {{ padding: 8px; border-bottom: 1px solid {cfg['border']}; }}
        QListWidget::item:selected {{ background: {cfg['select_bg']}; border-radius: 10px; color: {cfg['window_fg']}; }}
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {cfg['button1']}, stop:1 {cfg['button2']});
            border: 1px solid {cfg['border']}; border-radius: 14px; padding: 10px 14px; color: {cfg['accent_fg']}; font-weight: 800;
        }}
        QPushButton:hover {{ background: {cfg['button_hover']}; }}
        QPushButton:pressed {{ background: {cfg['button_press']}; }}
        QTabWidget::pane {{ border: 1px solid {cfg['border']}; border-radius: 18px; background: {cfg['tab_bg']}; }}
        QTabBar::tab {{ background: {cfg['tab_bg']}; color: {cfg['tab_text']}; padding: 11px 20px; border-top-left-radius: 12px; border-top-right-radius: 12px; margin-right: 4px; }}
        QTabBar::tab:selected {{ background: {cfg['tab_sel']}; color: {cfg['player_title']}; }}
        QProgressBar {{ border: 1px solid {cfg['border']}; border-radius: 10px; text-align: center; background: {cfg['group_bg1']}; color: {cfg['window_fg']}; }}
        QProgressBar::chunk {{ background: {cfg['chunk']}; border-radius: 8px; }}
        QSplitter::handle {{ background: {cfg['border']}; border-radius: 4px; }}
        QFrame#videoCard {{
            background: {cfg['video_card']}; border: 1px solid {cfg['border']}; border-radius: 20px;
        }}
        QFrame#videoStage {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {cfg['video_stage1']}, stop:1 {cfg['video_stage2']});
            border: 1px solid {cfg['border']}; border-radius: 26px;
        }}
        QFrame#transportBar {{
            background: {cfg['transport_bg']};
            border: 1px solid {cfg['border']}; border-radius: 20px;
        }}
        QLabel#playerBadge {{
            background: {cfg['player_badge_bg']}; color: {cfg['player_badge_fg']}; padding: 6px 12px; border-radius: 13px; font-weight: 900;
        }}
        QLabel#playerTitle {{ color: {cfg['player_title']}; font-size: 18px; font-weight: 800; }}
        QLabel#playerHint {{ color: {cfg['player_hint']}; font-size: 12px; }}
        QLabel#timePill {{
            background: {cfg['time_pill_bg']}; border: 1px solid {cfg['border']}; border-radius: 10px; padding: 4px 10px; color: {cfg['time_pill_fg']}; font-weight: 700;
        }}
        QLabel#transportTitle {{ color: {cfg['player_title']}; font-weight: 700; }}
        QLabel#playerFooter {{ color: {cfg['group_title']}; font-weight: 700; padding-top: 4px; }}
        QSlider#seekSlider::groove:horizontal {{
            height: 8px; border-radius: 4px; background: {cfg['group_bg2']};
        }}
        QSlider#seekSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {cfg['accent2']}, stop:1 {cfg['accent']});
            border-radius: 4px;
        }}
        QSlider#seekSlider::handle:horizontal {{
            width: 16px; margin: -5px 0; border-radius: 8px; background: #ffffff; border: 1px solid {cfg['accent']};
        }}
        QSlider#volumeSlider::groove:horizontal {{
            height: 6px; border-radius: 3px; background: {cfg['group_bg2']}; min-width: 120px;
        }}
        QSlider#volumeSlider::sub-page:horizontal {{
            background: {cfg['accent']}; border-radius: 3px;
        }}
        QSlider#volumeSlider::handle:horizontal {{
            width: 14px; margin: -4px 0; border-radius: 7px; background: white; border: 1px solid {cfg['accent']};
        }}
        QFrame#subtitlePanel {{ background: {cfg['subtitle_panel_bg']}; border:1px solid {cfg['border']}; border-radius:16px; }}
        QLabel#subtitleEn {{ color:{cfg['subtitle_en']}; font-size:20px; font-weight:800; }}
        QLabel#subtitleZh {{ color:{cfg['subtitle_zh']}; font-size:18px; }}
        QTextBrowser#clickableSubtitle {{ background: transparent; border: none; color:{cfg['subtitle_zh']}; }}
        QFrame#immersiveSidePanel {{ background: {cfg['side_bg']}; border:1px solid {cfg['border']}; border-radius:18px; }}
        QLabel#immersiveSideTitle {{ color:{cfg['side_title']}; font-size:18px; font-weight:900; }}
        QLabel#translationCard {{ background: {cfg['translation_bg']}; border:1px solid {cfg['translation_border']}; border-radius:12px; padding:12px; color:{cfg['window_fg']}; }}
        QTextBrowser#wordInfoBrowser {{ background:{cfg['word_bg']}; border:1px solid {cfg['word_border']}; border-radius:12px; color:{cfg['word_fg']}; }}
        """

    def append_log(self, text: str):
        now = time.strftime("%H:%M:%S")
        self.log_edit.appendPlainText(f"[{now}] {text}")
        self.status_bar.showMessage(text, 8000)

    def choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR)
        if path:
            self.output_edit.setText(path)
            self.root_output_dir = path

    def restore_default_layout(self):
        self.result_tools_wrap.setVisible(True)
        self.toggle_result_tools_btn.setText("隐藏结果工具")
        self.editor_panel.setVisible(False)
        self.toggle_editor_panel_btn.setText("显示剪辑区")
        self.main_splitter.setSizes([740, 980])

    def minimize_left_panel(self):
        self.main_splitter.setSizes([80, 1700])

    def maximize_preview_area(self):
        self.result_tools_wrap.setVisible(False)
        self.toggle_result_tools_btn.setText("展开结果工具")
        self.editor_panel.setVisible(False)
        self.toggle_editor_panel_btn.setText("显示剪辑区")
        self.main_splitter.setSizes([80, 1700])

    def toggle_fullscreen_playback(self):
        if self.isFullScreen():
            self.showNormal()
            self.restore_default_layout()
            self.fullscreen_btn.setText("全屏观影")
        else:
            self.maximize_preview_area()
            self.showFullScreen()
            self.fullscreen_btn.setText("退出全屏")

    def open_output_dir(self):
        path = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def apply_font_scale(self, value: int):
        base = 10 + value * 2
        self.base_font_px = base
        app = QApplication.instance()
        if app:
            app.setFont(QFont("Microsoft YaHei UI", base))
        self.setStyleSheet(self._build_stylesheet())
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(f"界面字号 {base}px", 2000)

    def start_search(self):
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
        self.results = []
        self.result_list.clear()
        self.search_btn.setEnabled(False)
        self.append_log(f"开始搜索：{keyword}；limit={self.limit_spin.value()} skip={self.skip_spin.value()}")
        self.search_worker = SearchWorker(keyword, self.limit_spin.value(), self.skip_spin.value())
        self.search_worker.finished_ok.connect(self.on_search_done_replace)
        self.search_worker.failed.connect(self.on_search_failed)
        self.search_worker.start()

    def load_more_results(self):
        keyword = self.keyword_edit.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
        self.search_btn.setEnabled(False)
        next_skip = self.skip_spin.value() + len(self.results)
        self.append_log(f"继续加载：{keyword}；limit={self.limit_spin.value()} skip={next_skip}")
        self.search_worker = SearchWorker(keyword, self.limit_spin.value(), next_skip)
        self.search_worker.finished_ok.connect(self.on_search_done_append)
        self.search_worker.failed.connect(self.on_search_failed)
        self.search_worker.start()

    def _fill_result_list(self):
        self.result_list.setUpdatesEnabled(False)
        self.result_list.blockSignals(True)
        self.result_list.clear()
        keyword = (self.keyword_edit.text().strip() or "")
        keyword_lower = keyword.lower()
        for item in self.results:
            line = extract_transcribed_text(item)
            display_line = line
            if keyword and keyword_lower in line.lower():
                display_line = re.sub(re.escape(keyword), lambda m: f"【{m.group(0)}】", line, flags=re.IGNORECASE)
            text_line = f"#{item.rank} [{item.year or '-'}] {display_line}"
            if item.movie:
                text_line += f"\n{item.movie}"
            lw = QListWidgetItem(text_line)
            lw.setData(Qt.UserRole, item)
            lw.setToolTip(
                f"影片: {item.movie}\n年份: {item.year or '-'}\n时长: {item.duration_hint:.2f}s\n链接: {item.video_url}"
            )
            lw.setFlags(lw.flags() | Qt.ItemIsUserCheckable)
            lw.setCheckState(Qt.Checked if self.select_all_by_default_cb.isChecked() else Qt.Unchecked)
            self.result_list.addItem(lw)
        self.result_list.blockSignals(False)
        self.result_list.setUpdatesEnabled(True)
        if self.results:
            self.result_list.setCurrentRow(0)
        self.refresh_batch_preview()

    def on_search_done_replace(self, results: list):
        self.search_btn.setEnabled(True)
        self.results = results
        self.sort_results(silent=True)
        self.append_log(f"搜索完成，载入 {len(results)} 条结果")

    def on_search_done_append(self, results: list):
        self.search_btn.setEnabled(True)
        existing = {f"{it.rank}|{it.source_id}|{it.sentence}" for it in self.results}
        for it in results:
            key = f"{it.rank}|{it.source_id}|{it.sentence}"
            if key not in existing:
                self.results.append(it)
        self.sort_results(silent=True)
        self.append_log(f"追加完成，当前共 {len(self.results)} 条结果")

    def on_search_failed(self, msg: str):
        self.search_btn.setEnabled(True)
        self.append_log(f"搜索失败：{msg}")
        QMessageBox.critical(self, "搜索失败", msg)

    def sort_results(self, silent=False):
        mode = self.sort_combo.currentText() if hasattr(self, "sort_combo") else "默认排序"
        if mode == "句子长度短→长":
            self.results.sort(key=lambda x: (len(extract_transcribed_text(x)), x.rank))
        elif mode == "句子长度长→短":
            self.results.sort(key=lambda x: (-len(extract_transcribed_text(x)), x.rank))
        elif mode == "影片年代旧→新":
            self.results.sort(key=lambda x: (x.year or 999999, x.rank))
        elif mode == "影片年代新→旧":
            self.results.sort(key=lambda x: (-(x.year or 0), x.rank))
        else:
            self.results.sort(key=lambda x: x.rank)
        self._fill_result_list()
        if not silent:
            self.append_log(f"已按“{mode}”排序")

    def current_result_item(self) -> Optional[PhraseItem]:
        item = self.result_list.currentItem()
        if item is not None:
            data = item.data(Qt.UserRole)
            if isinstance(data, PhraseItem):
                return data
        row = self.result_list.currentRow()
        return self.results[row] if 0 <= row < len(self.results) else None

    def current_queue_item(self) -> Optional[PhraseItem]:
        row = self.queue_list.currentRow()
        return self.queue_items[row] if 0 <= row < len(self.queue_items) else None

    def get_current_preview_item(self) -> Optional[PhraseItem]:
        return self.current_queue_item() if self.current_preview_from_queue else self.current_result_item()

    def ensure_zh_text(self, item: PhraseItem) -> str:
        if item.zh_override:
            return item.zh_override
        if item.zh_auto:
            return item.zh_auto
        cache_key = item.source_id or item.video_url or str(id(item))
        if cache_key in self.translation_cache:
            item.zh_auto = self.translation_cache[cache_key]
            return item.zh_auto
        self.request_translation_for_item(item)
        return "翻译中..."

    def request_translation_for_item(self, item: Optional[PhraseItem]):
        if not item:
            return
        if item.zh_override or item.zh_auto:
            return
        cache_key = item.source_id or item.video_url or str(id(item))
        if cache_key in self.translation_cache:
            item.zh_auto = self.translation_cache[cache_key]
            return
        if cache_key in self.translate_workers:
            return
        text = item.subtitle_override or extract_transcribed_text(item)
        worker = TranslateWorker(cache_key, text, self.subtitle_translate_engine.currentText().strip())
        self.translate_workers[cache_key] = worker
        worker.translated.connect(self.on_item_translated)
        worker.failed.connect(self.on_item_translate_failed)
        worker.finished.connect(lambda key=cache_key: self.translate_workers.pop(key, None))
        worker.start()

    def on_item_translated(self, cache_key: str, translated_text: str):
        self.translation_cache[cache_key] = translated_text
        for seq in (self.results, self.queue_items):
            for item in seq:
                key = item.source_id or item.video_url or str(id(item))
                if key == cache_key:
                    item.zh_auto = translated_text
        current = self.get_current_preview_item()
        if current:
            current_key = current.source_id or current.video_url or str(id(current))
            if current_key == cache_key:
                if self.current_preview_from_queue and hasattr(self, 'zh_subtitle_edit'):
                    self.zh_subtitle_edit.setPlainText(current.zh_override or translated_text)
                self.refresh_preview_subtitle_overlay()

    def on_item_translate_failed(self, cache_key: str, err: str):
        self.append_log(f"翻译失败: {err}")

    def refresh_preview_subtitle_overlay(self):
        item = self.get_current_preview_item() or self.current_item
        if not item:
            self.video_frame.overlay.clear_text()
            if hasattr(self, 'subtitle_en_label'):
                self.subtitle_en_label.clear()
                self.subtitle_zh_label.clear()
                self.clickable_subtitle_browser.clear()
                self.current_translation_label.setText('当前双语对照会显示在这里')
            return
        en = item.subtitle_override or extract_transcribed_text(item)
        zh = item.zh_override or self.ensure_zh_text(item)
        mode = self.preview_subtitle_mode.currentText()
        self.video_frame.overlay.set_mode_and_text(mode, en, zh)
        if hasattr(self, 'subtitle_en_label'):
            self.subtitle_en_label.setVisible(mode in ('英文', '双语'))
            self.subtitle_zh_label.setVisible(mode in ('中文', '双语'))
            self.subtitle_en_label.setText(en if mode in ('英文', '双语') else '')
            self.subtitle_zh_label.setText(zh if mode in ('中文', '双语') else '')
            clickable_html = ' '.join([f'<a href="{w.lower()}">{html.escape(w)}</a>' for w in re.findall(r"[A-Za-z']+|[^A-Za-z'\s]+", en)])
            self.clickable_subtitle_browser.setHtml(f'<div style="font-size:18px; text-align:center;">{clickable_html}</div>')
            self.clickable_subtitle_browser.setVisible(self.player.playbackState() != QMediaPlayer.PlayingState and bool(en))
            self.current_translation_label.setText(f"<b>当前句子</b><br>{html.escape(en)}<br><br><b>翻译</b><br>{html.escape(zh)}")
            if hasattr(self, "player_footer"):
                self.player_footer.setText("字幕显示在视频下方；点击复制按钮可快速查询")

    def preview_cache_key(self, item: PhraseItem) -> str:
        base = item.source_id or item.video_url or extract_transcribed_text(item)
        return hashlib.md5(base.encode("utf-8", errors="ignore")).hexdigest()

    def preview_cache_path(self, item: PhraseItem) -> str:
        ext = Path(QUrl(item.video_url).path()).suffix or ".mp4"
        return os.path.join(self.preview_cache_dir, f"{self.preview_cache_key(item)}{ext}")


    def request_preview_cache(self, item: Optional[PhraseItem], autoplay: bool = False, force_restart: bool = False):
        if not item or not item.video_url.startswith("http"):
            return ""
        cache_key = self.preview_cache_key(item)
        out_path = self.preview_cache_path(item)
        self.preview_cache_index[cache_key] = out_path
        if autoplay:
            self.pending_preview_autoplay_key = cache_key
        if os.path.exists(out_path) and not force_restart:
            return out_path
        if cache_key in self.preview_cache_workers and not force_restart:
            return out_path
        worker = PreviewCacheWorker(cache_key, item.video_url, out_path)
        self.preview_cache_workers[cache_key] = worker
        worker.done_ok.connect(self.on_preview_cached)
        worker.failed.connect(self.on_preview_cache_failed)
        worker.finished.connect(lambda key=cache_key: self.preview_cache_workers.pop(key, None))
        worker.start()
        return out_path

    def on_preview_cached(self, cache_key: str, local_path: str):
        self.append_log(f"预览缓存完成：{os.path.basename(local_path)}")
        current = self.get_current_preview_item() or self.current_item
        if not current:
            return
        if self.preview_cache_key(current) != cache_key:
            return
        if hasattr(self, "video_frame"):
            self.video_frame.hide_message()
        if self.pending_preview_autoplay_key == cache_key:
            self.pending_preview_autoplay_key = ""
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(local_path))
            self.player.play()
            self.play_btn.setText("⏸ 暂停")
            self.refresh_preview_subtitle_overlay()
            self.append_log("已切换本地缓存继续播放")

    def on_preview_cache_failed(self, cache_key: str, err: str):
        self.append_log(f"预览缓存失败：{err}")
        if getattr(self, 'pending_preview_autoplay_key', '') == cache_key:
            self.pending_preview_autoplay_key = ''

    def preview_item(self, item: Optional[PhraseItem], from_queue=False):
        if not item or not item.video_url:
            self.append_log("预览失败：当前条目没有可播放视频链接")
            if hasattr(self, "video_frame"):
                self.video_frame.show_message("当前条目没有可播放视频链接")
            return
        self.current_item = item
        self.current_preview_from_queue = from_queue
        self.preview_label.setText(item.display_title())
        if hasattr(self, "player_title"):
            self.player_title.setText(item.display_title())
        self.request_translation_for_item(item)
        self.refresh_preview_subtitle_overlay()

        if self.player_mode == "potplayer":
            if hasattr(self, "video_frame"):
                self.video_frame.show_message("已切换到 PotPlayer 外部播放")
            self.open_current_in_potplayer()
            return

        source_url = (item.video_url or "").strip()
        if source_url.startswith("http"):
            cached = self.preview_cache_path(item)
            if os.path.exists(cached):
                self.player.stop()
                self.player.setSource(QUrl.fromLocalFile(cached))
                if hasattr(self, "video_frame"):
                    self.video_frame.hide_message()
                self.player.play()
                self.play_btn.setText("⏸ 暂停")
                self.append_log(f"使用本地缓存预览：{item.display_title()}")
                return
            if hasattr(self, "video_frame"):
                self.video_frame.show_message("正在缓存预览视频…")
            self.append_log(f"开始缓存预览视频：{item.display_title()}")
            self.request_preview_cache(item, autoplay=True, force_restart=False)
            return

        if source_url.startswith("file://"):
            local_url = QUrl(source_url)
        else:
            local_url = QUrl.fromLocalFile(source_url)
        self.player.stop()
        self.player.setSource(local_url)
        if hasattr(self, "video_frame"):
            self.video_frame.hide_message()
        self.player.play()
        self.play_btn.setText("⏸ 暂停")
        self.append_log(f"开始预览：{item.display_title()}")

    def preview_current_result(self):
        item = self.current_result_item()
        if not item:
            self.append_log("预览失败：当前没有选中任何搜索结果")
            return
        self.preview_item(item, from_queue=False)

    def preview_current_queue_item(self):
        self.preview_item(self.current_queue_item(), from_queue=True)

    def apply_playback_speed(self, text: str):
        try:
            rate = float(str(text).lower().replace("x", "").strip())
        except Exception:
            rate = 1.0
        self.player.setPlaybackRate(rate)
        if hasattr(self, "player_footer"):
            self.player_footer.setText(f"播放速度 {rate:g}x · 双击搜索结果可直接加入预览")


    def on_loop_mode_changed(self, idx: int):
        if hasattr(self, 'loop_scope_combo'):
            self.loop_scope_combo.setCurrentIndex(max(0, min(idx, self.loop_scope_combo.count()-1)))
        if hasattr(self, 'player_footer'):
            self.player_footer.setText(f"循环模式：{self.loop_mode_btn.currentText()} · 可在播放选项中设置快捷键")

    def on_repeat_combo_changed(self, text: str):
        text = (text or '').replace('次','').strip()
        val = -1 if text == '无限' else int(text or '1')
        if hasattr(self, 'repeat_spin'):
            self.repeat_spin.setValue(10 if val == -1 else val)
        if hasattr(self, 'repeat_count_spin') and val != -1:
            self.repeat_count_spin.setValue(val)
        self.repeat_forever = (val == -1)
        if hasattr(self, 'repeat_forever_cb'):
            self.repeat_forever_cb.blockSignals(True)
            self.repeat_forever_cb.setChecked(val == -1)
            self.repeat_forever_cb.blockSignals(False)

    def on_repeat_count_spin_changed(self, value: int):
        if hasattr(self, 'repeat_spin') and self.repeat_spin.value() != value:
            self.repeat_spin.setValue(value)
        self.repeat_forever = False
        if hasattr(self, 'repeat_forever_cb') and self.repeat_forever_cb.isChecked():
            self.repeat_forever_cb.blockSignals(True)
            self.repeat_forever_cb.setChecked(False)
            self.repeat_forever_cb.blockSignals(False)

    def on_repeat_forever_toggled(self, checked: bool):
        self.repeat_forever = checked
        if hasattr(self, 'repeat_count_spin'):
            self.repeat_count_spin.setEnabled(not checked)
        if hasattr(self, 'player_footer'):
            self.player_footer.setText(f"循环模式：{self.loop_mode_btn.currentText()} · 循环次数：{'无限' if checked else self.repeat_count_spin.value()}")

    def update_font_area(self, area: str, family=None, size=None, color=None):
        cfg = self.font_area_settings.get(area, {}).copy()
        if family is not None: cfg['family'] = family
        if size is not None: cfg['size'] = size
        if color is not None: cfg['color'] = color
        self.font_area_settings[area] = cfg
        self.apply_font_area_styles()

    def apply_font_area_styles(self):
        search = self.font_area_settings['search']
        results = self.font_area_settings['results']
        queue = self.font_area_settings['queue']
        sub_en = self.font_area_settings['subtitle_en']
        sub_zh = self.font_area_settings['subtitle_zh']
        title = self.font_area_settings['title']
        self.keyword_edit.setFont(QFont(search['family'], search['size']))
        self.keyword_edit.setStyleSheet(f"color:{search['color']};")
        self.result_list.setFont(QFont(results['family'], results['size']))
        self.result_list.setStyleSheet(self.result_list.styleSheet() + f"QListWidget{{color:{results['color']};}}")
        self.queue_list.setFont(QFont(queue['family'], queue['size']))
        self.queue_list.setStyleSheet(self.queue_list.styleSheet() + f"QListWidget{{color:{queue['color']};}}")
        if hasattr(self, 'search_font_color_btn'):
            self.search_font_color_btn.setStyleSheet(f"background:{search['color']}; color:#ffffff;")
        if hasattr(self, 'results_font_color_btn'):
            self.results_font_color_btn.setStyleSheet(f"background:{results['color']}; color:#ffffff;")
        if hasattr(self, 'queue_font_color_btn'):
            self.queue_font_color_btn.setStyleSheet(f"background:{queue['color']}; color:#ffffff;")
        self.subtitle_en_label.setFont(QFont(sub_en['family'], sub_en['size']))
        self.subtitle_en_label.setStyleSheet(f"color:{sub_en['color']};")
        self.subtitle_zh_label.setFont(QFont(sub_zh['family'], sub_zh['size']))
        self.subtitle_zh_label.setStyleSheet(f"color:{sub_zh['color']};")
        self.player_title.setFont(QFont(title['family'], title['size'], QFont.Bold))
        self.player_title.setStyleSheet(f"color:{title['color']};")

    def choose_font_color(self, area: str):
        c = QColorDialog.getColor(QColor(self.font_area_settings.get(area,{}).get('color','#333333')), self, '选择字体颜色')
        if c.isValid():
            self.update_font_area(area, color=c.name())

    def build_shortcuts_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('自定义快捷键面板')
        lay = QVBoxLayout(dlg)
        edits = {}
        for action, seq in self.shortcuts_map.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(action))
            edit = QKeySequenceEdit(QKeySequence(seq))
            edits[action] = edit
            row.addWidget(edit, 1)
            lay.addLayout(row)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(btns)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        if dlg.exec():
            self.shortcuts_map = {k: v.keySequence().toString() or self.shortcuts_map[k] for k,v in edits.items()}
            self.install_custom_shortcuts()

    def install_custom_shortcuts(self):
        from PySide6.QtGui import QShortcut
        if hasattr(self, '_custom_shortcuts'):
            for s in self._custom_shortcuts:
                s.setParent(None)
        self._custom_shortcuts = []
        mapping = {
            '播放/暂停': self.toggle_playback,
            '停止': self.stop_playback,
            '沉浸式学习': lambda: self.set_immersive_mode(not self.immersive_mode),
            '显示/隐藏上栏': lambda: self.set_top_controls_visible(not self.top_controls_visible),
            '显示/隐藏下栏': lambda: self.set_bottom_controls_visible(not self.bottom_controls_visible),
            '切换循环模式': lambda: self.loop_mode_btn.setCurrentIndex(1 - self.loop_mode_btn.currentIndex()),
            '循环次数+1': lambda: self.repeat_count_spin.setValue(min(self.repeat_count_spin.maximum(), self.repeat_count_spin.value()+1)),
            '循环次数-1': lambda: self.repeat_count_spin.setValue(max(self.repeat_count_spin.minimum(), self.repeat_count_spin.value()-1)),
            '复制英文字幕': lambda: QGuiApplication.clipboard().setText(self.subtitle_en_label.text().strip()),
            '复制中文字幕': lambda: QGuiApplication.clipboard().setText(self.subtitle_zh_label.text().strip()),
        }
        for name, func in mapping.items():
            seq = self.shortcuts_map.get(name, '')
            if not seq:
                continue
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(func)
            self._custom_shortcuts.append(sc)

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶ 播放")
            if hasattr(self, "player_footer"):
                self.player_footer.setText("已暂停 · 双击搜索结果可直接加入预览")
            return
        current = self.get_current_preview_item() or self.current_item
        if current and self.player.source().isEmpty():
            self.preview_item(current, from_queue=self.current_preview_from_queue)
            return
        self.player.play()
        self.play_btn.setText("⏸ 暂停")
        if hasattr(self, "player_footer"):
            self.player_footer.setText("正在播放 · 双击搜索结果可直接加入预览")

    def stop_playback(self):
        self.pending_preview_autoplay_key = ""
        self.player.stop()
        self.video_frame.overlay.clear_text()
        self.video_frame.show_message("已停止\n双击搜索结果或点击“加入预览”开始播放")
        self.play_btn.setText("▶ 播放")
        if hasattr(self, "player_footer"):
            self.player_footer.setText("已停止 · 点击字幕单词可直接搜索")

    def on_volume_changed(self, value: int):
        self.audio.setVolume(max(0.0, min(1.0, value / 100.0)))
        if hasattr(self, "player_footer"):
            self.player_footer.setText(f"音量 {value}% · 点击字幕单词可直接搜索")
        if hasattr(self, "mute_btn") and self.mute_btn.isChecked() and value > 0:
            self.mute_btn.blockSignals(True)
            self.mute_btn.setChecked(False)
            self.mute_btn.blockSignals(False)
            self.mute_btn.setText("🔊")

    def toggle_mute(self, checked: bool):
        self.audio.setMuted(checked)
        if hasattr(self, "mute_btn"):
            self.mute_btn.setText("🔇" if checked else "🔊")
        if hasattr(self, "player_footer"):
            self.player_footer.setText("已静音" if checked else f"音量 {self.volume_slider.value()}% · 点击字幕单词可直接搜索")

    def on_seek_slider_moved(self, value: int):
        self.player.setPosition(value)

    def on_player_duration_changed(self, duration: int):
        if hasattr(self, "seek_slider"):
            self.seek_slider.blockSignals(True)
            self.seek_slider.setRange(0, max(0, duration))
            self.seek_slider.blockSignals(False)
        if hasattr(self, "total_time_label"):
            self.total_time_label.setText(self.format_ms(duration))

    def on_player_state_changed(self, state):
        if hasattr(self, "play_btn"):
            self.play_btn.setText("⏸ 暂停" if state == QMediaPlayer.PlayingState else "▶ 播放")
        if hasattr(self, 'clickable_subtitle_browser'):
            self.clickable_subtitle_browser.setVisible(state != QMediaPlayer.PlayingState and bool(self.clickable_subtitle_browser.toPlainText().strip()))
        if hasattr(self, "video_frame"):
            if state == QMediaPlayer.PlayingState:
                self.video_frame.hide_message()
            elif not getattr(self, "current_item", None):
                self.video_frame.show_message("双击搜索结果或点击“加入预览”开始播放")
        self.refresh_preview_subtitle_overlay()

    def on_player_position_changed(self, pos_ms: int):
        if hasattr(self, "seek_slider") and not self.seek_slider.isSliderDown():
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(pos_ms)
            self.seek_slider.blockSignals(False)
        if hasattr(self, "current_time_label"):
            self.current_time_label.setText(self.format_ms(pos_ms))
        self.refresh_preview_subtitle_overlay()

    def on_player_error(self, error, error_string):
        if error:
            self.append_log(f"播放器错误：{error_string or error}")
        item = getattr(self, 'current_item', None)
        if hasattr(self, "video_frame"):
            self.video_frame.show_message("播放器打开失败\n正在尝试使用本地缓存重新播放")
        if item and getattr(item, 'video_url', '').startswith('http'):
            cached = self.preview_cache_path(item)
            if os.path.exists(cached):
                self.append_log("检测到播放失败，自动切换到本地缓存")
                self.player.stop()
                self.player.setSource(QUrl.fromLocalFile(cached))
                self.player.play()
            else:
                self.append_log("检测到播放失败，自动下载本地缓存后再播放")
                self.preview_label.setText("远程播放失败，正在下载本地缓存...")
                self.request_preview_cache(item, autoplay=True, force_restart=False)

    def on_media_status_changed(self, status):
        if status != QMediaPlayer.EndOfMedia:
            return
        repeat_target = 999999 if getattr(self, "repeat_forever", False) else (self.repeat_count_spin.value() if hasattr(self, 'repeat_count_spin') else self.repeat_spin.value())
        current = getattr(self, "_repeat_count", 0) + 1
        self._repeat_count = current
        if current < repeat_target:
            self.player.setPosition(0)
            self.player.play()
            return
        self._repeat_count = 0
        if not self.auto_next_cb.isChecked():
            return

        if self.current_preview_from_queue and self.queue_items:
            row = self.queue_list.currentRow()
            next_row = row + 1 if row >= 0 else 0
            if next_row >= len(self.queue_items):
                if self.loop_scope_combo.currentIndex() == 1:
                    next_row = 0
                else:
                    return
            self.queue_list.setCurrentRow(next_row)
            self.preview_current_queue_item()
        elif self.results:
            row = self.result_list.currentRow()
            next_row = row + 1 if row >= 0 else 0
            if next_row >= len(self.results):
                if self.loop_scope_combo.currentIndex() == 1:
                    next_row = 0
                else:
                    return
            self.result_list.setCurrentRow(next_row)
            self.preview_current_result()

    def on_result_selection_changed(self):
        item = self.current_result_item()
        if item:
            self.current_item = item
            self.request_translation_for_item(item)
            self.request_preview_cache(item, autoplay=False)
            self.preview_label.setText(item.display_title())
        if hasattr(self, "player_title"):
            self.player_title.setText(item.display_title())
            self.refresh_preview_subtitle_overlay()
            words = extract_transcribed_text(item).split()
            word = (self.keyword_edit.text().strip() or (words[0] if words else "")).strip()
            self.schedule_bing_lookup(word)


    def schedule_bing_lookup(self, word: str):
        word = (word or "").strip()
        if not word:
            return
        self.pending_bing_word = word
        if hasattr(self, "bing_lookup_timer") and self.bing_lookup_timer:
            self.bing_lookup_timer.start(350)
        else:
            self._flush_pending_bing_lookup()

    def _flush_pending_bing_lookup(self):
        word = (getattr(self, "pending_bing_word", "") or "").strip()
        if not word:
            return
        view = getattr(self, "resource_views", {}).get("Bing词典")
        if WEB_OK and view is not None:
            try:
                view.setUrl(QUrl(f"https://cn.bing.com/dict/search?q={word}"))
            except Exception:
                pass
        self.pending_bing_word = ""

    def select_all_results(self):
        for i in range(self.result_list.count()):
            item = self.result_list.item(i)
            widget = self.result_list.itemWidget(item) if item else None
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(True)
        self.refresh_batch_preview()

    def invert_all_results(self):
        for i in range(self.result_list.count()):
            item = self.result_list.item(i)
            widget = self.result_list.itemWidget(item) if item else None
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(not widget.checkbox.isChecked())
        self.refresh_batch_preview()

    def unselect_all_results(self):
        for i in range(self.result_list.count()):
            item = self.result_list.item(i)
            widget = self.result_list.itemWidget(item) if item else None
            if widget and hasattr(widget, 'checkbox'):
                widget.checkbox.setChecked(False)
        self.refresh_batch_preview()

    def copy_current_result_line(self):
        item = self.current_result_item()
        if not item:
            QMessageBox.warning(self, "提示", "请先选中一条搜索结果")
            return
        QGuiApplication.clipboard().setText(extract_transcribed_text(item))
        self.append_log("已复制当前台词")

    def copy_checked_result_lines(self):
        items = self.checked_result_items()
        if not items:
            QMessageBox.warning(self, "提示", "请先勾选搜索结果")
            return
        text = "\n".join([extract_transcribed_text(it) for it in items])
        QGuiApplication.clipboard().setText(text)
        self.append_log(f"已复制 {len(items)} 条勾选台词")

    def checked_result_items(self) -> List[PhraseItem]:
        items = []
        for i in range(self.result_list.count()):
            lw = self.result_list.item(i)
            if lw and lw.checkState() == Qt.Checked:
                data = lw.data(Qt.UserRole)
                if isinstance(data, PhraseItem):
                    items.append(data)
                elif i < len(self.results):
                    items.append(self.results[i])
        return items

    def refresh_batch_preview(self):
        if not hasattr(self, "batch_preview"):
            return
        items = self.checked_result_items()
        lines = [it.display_title() for it in items[:300]]
        if len(items) > 300:
            lines.append(f"... 共 {len(items)} 条，仅预览前 300 条")
        self.batch_preview.setPlainText("\n".join(lines) if lines else "当前没有勾选项。")

    def add_selected_results(self):
        items = self.checked_result_items()
        if not items:
            current = self.current_result_item()
            if current:
                items = [current]
        if not items:
            self.append_log("加入预览失败：没有勾选也没有当前选中项")
            return
        existing = {q.source_id or q.video_url or extract_transcribed_text(q) for q in self.queue_items}
        added = 0
        last_idx = None
        for src in items:
            key = src.source_id or src.video_url or extract_transcribed_text(src)
            if key in existing:
                continue
            clone = PhraseItem(**asdict(src))
            clone.selected = True
            self.queue_items.append(clone)
            existing.add(key)
            added += 1
            last_idx = len(self.queue_items) - 1
        self.refresh_queue_list()
        if last_idx is not None:
            self.queue_list.setCurrentRow(last_idx)
        self.append_log(f"已加入预览列表 {added} 条")
        if added == 1 and last_idx is not None:
            self.preview_current_queue_item()

    def refresh_queue_list(self):
        self.queue_list.clear()
        for idx, item in enumerate(self.queue_items, start=1):
            txt = f"{idx:02d}. {item.display_title()}"
            self.queue_list.addItem(txt)

    def on_queue_selection_changed(self):
        item = self.current_queue_item()
        if not item:
            return
        self.current_item = item
        if hasattr(self, "subtitle_edit"):
            self.subtitle_edit.setPlainText(item.subtitle_override or extract_transcribed_text(item))
        if hasattr(self, "zh_subtitle_edit"):
            self.zh_subtitle_edit.setPlainText(item.zh_override or self.ensure_zh_text(item))
        if hasattr(self, "trim_start_spin"):
            self.trim_start_spin.setValue(int(item.trim_start))
        if hasattr(self, "trim_end_spin"):
            self.trim_end_spin.setValue(int(item.trim_end))
        self.preview_label.setText(item.display_title())
        if hasattr(self, "player_title"):
            self.player_title.setText(item.display_title())
        self.refresh_preview_subtitle_overlay()

    def save_current_queue_edits(self):
        item = self.current_queue_item()
        if not item:
            return
        item.subtitle_override = self.subtitle_edit.toPlainText().strip()
        item.zh_override = self.zh_subtitle_edit.toPlainText().strip()
        item.trim_start = float(self.trim_start_spin.value())
        item.trim_end = float(self.trim_end_spin.value())
        self.refresh_queue_list()
        self.refresh_preview_subtitle_overlay()
        self.append_log("当前编排项已保存修改")

    def move_queue_item(self, delta: int):
        row = self.queue_list.currentRow()
        new_row = row + delta
        if row < 0 or new_row < 0 or new_row >= len(self.queue_items):
            return
        self.queue_items[row], self.queue_items[new_row] = self.queue_items[new_row], self.queue_items[row]
        self.refresh_queue_list()
        self.queue_list.setCurrentRow(new_row)

    def remove_queue_item(self):
        row = self.queue_list.currentRow()
        if 0 <= row < len(self.queue_items):
            self.queue_items.pop(row)
            self.refresh_queue_list()
            self.append_log("已移除编排项")

    def clear_queue(self):
        self.queue_items.clear()
        self.refresh_queue_list()
        self.subtitle_edit.clear()
        self.zh_subtitle_edit.clear()
        self.trim_start_spin.setValue(0)
        self.trim_end_spin.setValue(0)
        self.append_log("已清空编排区")

    def toggle_result_tools(self):
        visible = self.result_tools_wrap.isVisible()
        self.result_tools_wrap.setVisible(not visible)
        self.toggle_result_tools_btn.setText("展开结果工具" if visible else "隐藏结果工具")

    def toggle_editor_panel(self):
        visible = self.editor_panel.isVisible()
        self.editor_panel.setVisible(not visible)
        self.toggle_editor_panel_btn.setText("展开剪辑区" if visible else "隐藏剪辑区")
        if visible:
            self.main_splitter.setSizes([80, 1700])
        else:
            self.main_splitter.setSizes([740, 980])

    def build_editor_form(self):
        box = QWidget()
        lay = QFormLayout(box)
        lay.setLabelAlignment(Qt.AlignRight)
        lay.addRow("项目名称", self.project_name_edit)
        lay.addRow("英文字幕", self.subtitle_edit)
        lay.addRow("中文字幕", self.zh_subtitle_edit)
        lay.addRow("裁剪起点(秒)", self.trim_start_spin)
        lay.addRow("裁剪终点(秒)", self.trim_end_spin)
        lay.addRow("字幕字号", self.subtitle_font_spin)
        lay.addRow("导出画幅", self.aspect_ratio_combo)
        lay.addRow("导出字幕", self.export_subtitle_mode)
        return box

    def show_editor_dialog(self):
        if not hasattr(self, "editor_dialog") or self.editor_dialog is None:
            self.editor_dialog = FloatingEditorDialog(self)
            self.editor_dialog.set_form_widget(self.build_editor_form())
            self.editor_dialog.applied.connect(self.apply_editor_dialog)
        self.editor_dialog.show()
        self.editor_dialog.raise_()
        self.editor_dialog.activateWindow()

    def apply_editor_dialog(self):
        self.save_current_queue_edits()
        if self.editor_dialog.hide_after_apply_cb.isChecked():
            self.editor_dialog.hide()

    def on_player_mode_changed(self, text_value: str):
        self.player_mode = "potplayer" if "PotPlayer" in text_value else "embedded"
        self.status_bar.showMessage("已切换播放模式", 3000)

    def apply_preview_aspect(self):
        name = self.preview_ratio_combo.currentText().strip()
        if name == "9:16 竖版":
            self.video_frame.setMinimumSize(QSize(520, 920))
        elif name == "16:9 横版":
            self.video_frame.setMinimumSize(QSize(900, 506))
        elif name == "1:1 方形":
            self.video_frame.setMinimumSize(QSize(760, 760))
        else:
            self.video_frame.setMinimumSize(QSize(700, 880))

    def choose_potplayer(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 PotPlayer", self.potplayer_edit.text().strip(), "PotPlayer (*.exe);;Executable (*.exe)")
        if path:
            self.potplayer_edit.setText(path)

    def _build_temp_subtitle_for_item(self, item: PhraseItem) -> str:
        mode = self.preview_subtitle_mode.currentText().strip()
        if mode == "无字幕" or not item:
            return ""
        out_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(out_dir)
        path = os.path.join(out_dir, f"_preview_{int(time.time()*1000)}.ass")
        en = item.subtitle_override or extract_transcribed_text(item)
        zh = item.zh_override or self.ensure_zh_text(item)
        generate_ass_from_text_mode(en, zh, path, self.subtitle_font_spin.value(), mode)
        self.current_temp_subtitle = path
        return path

    def open_current_in_potplayer(self):
        item = self.get_current_preview_item()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个结果或编排项")
            return
        try:
            sub = self._build_temp_subtitle_for_item(item)
            media = item.video_url
            if media.startswith("http"):
                out_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
                safe_mkdir(out_dir)
                local_name = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", extract_transcribed_text(item)[:40]).strip("_") or "preview"
                local_path = os.path.join(out_dir, f"_potplayer_{local_name}.mp4")
                if not os.path.exists(local_path):
                    self.append_log("正在为 PotPlayer 缓存当前视频...")
                    download_file(make_session(), media, local_path)
                media = local_path
            open_with_potplayer(self.potplayer_edit.text().strip(), media, sub, self.player.position())
            self.append_log(f"已通过 PotPlayer 打开：{item.display_title()}")
        except Exception as e:
            QMessageBox.critical(self, "PotPlayer 打开失败", str(e))

    def toggle_immersive_mode(self):
        self.set_immersive_mode(not self.immersive_mode)

    def set_immersive_mode(self, enabled: bool):
        self.immersive_mode = enabled
        if hasattr(self, 'player_badge'):
            self.player_badge.blockSignals(True)
            self.player_badge.setChecked(enabled)
            self.player_badge.setText('退出沉浸式学习' if enabled else '沉浸式学习')
            self.player_badge.blockSignals(False)
        if hasattr(self, 'immersive_side_panel'):
            self.immersive_side_panel.setVisible(enabled)
            self.video_splitter.setSizes([1100, 480] if enabled else [1600, 0])
        if enabled:
            self.set_bottom_controls_visible(True)
            self.player_hint.setText('暂停时点击下方单词，可查看音标、释义并播放发音')
        else:
            self.set_bottom_controls_visible(True)
            self.player_hint.setText('双击搜索结果可自动加入预览并播放；暂停时可点单词查释义')
        self.refresh_preview_subtitle_overlay()

    def set_top_controls_visible(self, visible: bool):
        self.top_controls_visible = visible
        if hasattr(self, 'player_mode_combo'):
            # preview_head layout widgets are toggled individually
            for w in [self.player_mode_combo, self.preview_ratio_combo, self.playback_options_btn, self.open_editor_popup_btn, self.max_preview_btn, self.fullscreen_btn, self.player_theme_combo]:
                w.setVisible(visible)

    def set_bottom_controls_visible(self, visible: bool):
        self.bottom_controls_visible = visible
        if hasattr(self, 'current_time_label'):
            self.current_time_label.parentWidget().setVisible(visible)
        if hasattr(self, 'play_btn'):
            self.play_btn.parentWidget().setVisible(visible)

    def set_control_bars_visible(self, top_visible: bool, bottom_visible: bool):
        self.set_top_controls_visible(top_visible)
        self.set_bottom_controls_visible(bottom_visible)

    def sync_immersive_queue_selection(self):
        row = self.immersive_queue_list.currentRow()
        if row >= 0 and self.queue_list.currentRow() != row:
            self.queue_list.blockSignals(True)
            self.queue_list.setCurrentRow(row)
            self.queue_list.blockSignals(False)
            self.on_queue_selection_changed()

    def on_subtitle_word_clicked(self, url: QUrl):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        word = (url.toString() or '').strip().lower()
        word = re.sub(r"[^a-zA-Z']", '', word)
        if not word:
            return
        self.word_info_browser.setHtml(f'<div style="padding:12px;">正在查询 <b>{html.escape(word)}</b> ...</div>')
        self.pronounce_btn.setEnabled(False)
        self.current_audio_url = ''
        self.dictionary_worker = DictionaryLookupWorker(word)
        self.dictionary_worker.finished_ok.connect(self.on_dictionary_lookup_done)
        self.dictionary_worker.failed.connect(self.on_dictionary_lookup_failed)
        self.dictionary_worker.start()

    def on_dictionary_lookup_done(self, word: str, payload: dict):
        ipa = payload.get('ipa') or '未提供音标'
        defs = payload.get('definitions') or []
        parts = [f'<h3 style="margin:0 0 8px 0;">{html.escape(word)}</h3>', f'<div style="color:#8cf2ff; margin-bottom:8px;">{html.escape(ipa)}</div>']
        if defs:
            for d in defs:
                part = html.escape(d.get('part') or '')
                defi = html.escape(d.get('definition') or '')
                ex = html.escape(d.get('example') or '')
                parts.append(f'<div style="margin-bottom:10px;"><b>{part}</b> {defi}</div>')
                if ex:
                    parts.append(f'<div style="color:#9ec6ff; margin-bottom:8px;">例句：{ex}</div>')
        else:
            parts.append('<div>没有查到更详细的释义。</div>')
        self.word_info_browser.setHtml(''.join(parts))
        self.current_audio_url = payload.get('audio') or ''
        self.pronounce_btn.setEnabled(bool(self.current_audio_url))

    def on_dictionary_lookup_failed(self, word: str, err: str):
        self.word_info_browser.setHtml(f'<div style="padding:12px;">查询 <b>{html.escape(word)}</b> 失败：{html.escape(err)}</div>')
        self.current_audio_url = ''
        self.pronounce_btn.setEnabled(False)

    def play_current_word_audio(self):
        if not getattr(self, 'current_audio_url', ''):
            return
        self.pron_player.stop()
        self.pron_player.setSource(QUrl(self.current_audio_url))
        self.pron_player.play()

    def open_last_export_in_potplayer(self):
        if not self.last_exported_video or not os.path.exists(self.last_exported_video):
            QMessageBox.warning(self, "提示", "当前还没有可打开的导出成片")
            return
        try:
            open_with_potplayer(self.potplayer_edit.text().strip(), self.last_exported_video)
        except Exception as e:
            QMessageBox.critical(self, "PotPlayer 打开失败", str(e))

    def open_current_in_browser(self):
        item = self.current_result_item() or self.current_queue_item()
        if item and item.video_url:
            QDesktopServices.openUrl(QUrl(item.video_url))

    def save_current_frame(self):
        item = self.get_current_preview_item()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个正在预览的条目")
            return
        if not ffmpeg_exists():
            QMessageBox.critical(self, "错误", "未检测到 ffmpeg")
            return
        out_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(out_dir)
        name = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", extract_transcribed_text(item)[:40]).strip("_") or "frame"
        out_path = os.path.join(out_dir, f"{name}_{int(time.time())}.jpg")
        sec = max(0.0, self.player.position() / 1000.0)
        cmd = ["ffmpeg", "-y", "-ss", str(sec), "-i", item.video_url, "-frames:v", "1", out_path]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if result.returncode != 0:
            QMessageBox.critical(self, "截图失败", (result.stderr or result.stdout or "截图失败")[-1200:])
            return
        self.append_log(f"截图已保存：{out_path}")
        QMessageBox.information(self, "完成", f"截图已保存：\n{out_path}")

    def start_batch_download(self):
        items = self.checked_result_items()
        if not items:
            QMessageBox.warning(self, "提示", "请先勾选搜索结果")
            return
        out_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(out_dir)
        self.batch_progress.show()
        self.batch_download_btn.setEnabled(False)
        self.append_log(f"开始批量下载，共 {len(items)} 条")
        self.download_worker = DownloadWorker(items, out_dir)
        self.download_worker.log_msg.connect(self.append_log)
        self.download_worker.done_ok.connect(self.on_batch_download_done)
        self.download_worker.failed.connect(self.on_batch_download_failed)
        self.download_worker.start()

    def on_batch_download_done(self, folder: str):
        self.batch_progress.hide()
        self.batch_download_btn.setEnabled(True)
        self.append_log(f"批量下载完成：{folder}")
        if QMessageBox.question(self, "完成", f"批量下载完成：\n{folder}\n\n是否打开目录？") == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def on_batch_download_failed(self, msg: str):
        self.batch_progress.hide()
        self.batch_download_btn.setEnabled(True)
        self.append_log(f"批量下载失败：{msg}")
        QMessageBox.critical(self, "批量下载失败", msg)

    def export_current_search_docs(self):
        if not self.results:
            QMessageBox.warning(self, "提示", "请先搜索结果")
            return
        export_formats = []
        if self.fmt_txt_cb.isChecked():
            export_formats.append("txt")
        if self.fmt_doc_cb.isChecked():
            export_formats.append("doc")
        if self.fmt_pdf_cb.isChecked():
            export_formats.append("pdf")
        if self.fmt_xlsx_cb.isChecked():
            export_formats.append("xlsx")
        if not export_formats:
            QMessageBox.warning(self, "提示", "请至少选择一种导出格式")
            return

        if self.field_sentence_cb.isChecked():
            field_keys = ["sentence"]
            if self.field_translation_cb.isChecked():
                field_keys.append("translation")
        else:
            field_keys = []
            if self.field_rank_cb.isChecked():
                field_keys.append("rank")
            field_keys.append("sentence")
            if self.field_translation_cb.isChecked():
                field_keys.append("translation")
            if self.field_year_cb.isChecked():
                field_keys.append("year")
            if self.field_movie_cb.isChecked():
                field_keys.append("movie")
            if self.field_url_cb.isChecked():
                field_keys.append("video_url")

        out_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(out_dir)
        name = self.doc_name_edit.text().strip() or self.keyword_edit.text().strip() or "搜索结果导出"
        do_translate = self.doc_translate_cb.isChecked() or self.field_translation_cb.isChecked()
        translate_engine = self.doc_translate_engine.currentText().strip() or "内置翻译"

        preview_headers, preview_rows = build_export_rows(self.results[:8], field_keys, do_translate, translate_engine)
        preview_text = "\n".join(["\t".join([str(x) for x in preview_headers])] + ["\t".join([str(x) for x in row]) for row in preview_rows])
        self.doc_preview.setPlainText(preview_text)

        self.doc_export_btn.setEnabled(False)
        self.append_log(f"开始导出搜索结果文档，格式={export_formats}")
        self.doc_worker = DocExportWorker(self.results, out_dir, name, export_formats, field_keys, do_translate, translate_engine)
        self.doc_worker.done_ok.connect(self.on_doc_export_done)
        self.doc_worker.failed.connect(self.on_doc_export_failed)
        self.doc_worker.start()

    def on_doc_export_done(self, paths: str):
        self.doc_export_btn.setEnabled(True)
        self.doc_preview.setPlainText(paths)
        self.append_log("搜索结果文档导出完成")
        QMessageBox.information(self, "完成", f"已导出：\n{paths}")

    def on_doc_export_failed(self, msg: str):
        self.doc_export_btn.setEnabled(True)
        self.append_log(f"文档导出失败：{msg}")
        QMessageBox.critical(self, "文档导出失败", msg)

    def start_export(self):
        if not self.queue_items:
            QMessageBox.warning(self, "提示", "请先把结果添加到编排区")
            return
        if not ffmpeg_exists():
            QMessageBox.critical(self, "错误", "未检测到 ffmpeg，请先安装并加入 PATH")
            return
        output_dir = self.output_edit.text().strip() or DEFAULT_OUTPUT_DIR
        safe_mkdir(output_dir)
        self.save_current_queue_edits()
        self.export_btn.setEnabled(False)
        self.export_progress.show()
        self.append_log("开始导出并合成...")
        self.export_worker = ExportWorker(
            self.queue_items,
            output_dir,
            self.project_name_edit.text().strip() or "商业成片",
            self.subtitle_font_spin.value(),
            self.export_subtitle_mode.currentText().strip(),
            self.aspect_ratio_combo.currentText().strip(),
            self.subtitle_translate_engine.currentText().strip(),
        )
        self.export_worker.log_msg.connect(self.append_log)
        self.export_worker.done_ok.connect(self.on_export_done)
        self.export_worker.failed.connect(self.on_export_failed)
        self.export_worker.start()

    def on_export_done(self, project_dir: str, final_path: str):
        self.export_btn.setEnabled(True)
        self.export_progress.hide()
        self.last_exported_video = final_path
        self.append_log(f"导出完成：{final_path}")
        if QMessageBox.question(self, "导出完成", f"项目目录：\n{project_dir}\n\n是否打开输出目录？") == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(project_dir))

    def on_export_failed(self, msg: str):
        self.export_btn.setEnabled(True)
        self.export_progress.hide()
        self.append_log(f"导出失败：{msg}")
        QMessageBox.critical(self, "导出失败", msg)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    win = ProWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

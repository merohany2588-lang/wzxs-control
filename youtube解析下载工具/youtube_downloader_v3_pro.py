
"""
🎬 多站点批量下载器 v3.10 Pro

新增：
  ✅ 高级 UI：彩色统计卡、彩色 ETA、任务数量、速度、剩余时间、已用时间
  ✅ 任务中心：待下载 / 任务中 / 已完成 三窗口
  ✅ 单任务控制：暂停 / 继续 / 取消；全局暂停 / 全局继续 / 全部取消
  ✅ 任务详情：文件来源、格式、时长、URL、输出路径、速度、ETA、状态
  ✅ 排序与分类：按格式 / 状态 / 标题 / 时长 / 进度 / 时间显示
  ✅ 已完成：按分类查看、关键词查找、打开输出目录
  ✅ 下载设置：画质、封装格式、分片并发、同时下载数、重试、限速、字幕/缩略图/说明文件等
  ✅ 一键启动 run.bat + 一键打包 build_exe.bat，支持 app.ico
  ✅ 30 套皮肤主题：深色/浅色/霓虹/商务/护眼/高对比
  ✅ 极速推荐配置：自动设置并发、分片、chunk、重试、播放器客户端优先级
  ✅ v3.3：文件大小列、直播结束友好提示、多站点 URL 通用解析入口
  ✅ v3.4：默认跳过直播/预约直播/直播回放，只保留普通视频源
  ✅ v3.6：新增平台解析适配层：YouTube/抖音/TikTok/B站/快手/Twitch/X/Facebook 独立规整、请求头、Cookie、fallback 解析策略
  ✅ v3.7：修复抖音标准 /video/数字 链接解析；强制使用当前 Python 环境的 yt-dlp 模块，避免调用系统旧版 yt-dlp
  ✅ v3.8：新增 Cookie 文件/浏览器 Profile/抖音 Cookie 诊断；修复 Fresh cookies 与超时提示；解析和下载统一使用 Cookie 配置
  ✅ v3.9：抖音 Fresh cookies 自动尝试 Edge/Chrome/Firefox；修复误报“不是普通视频”；新增 Cookie 状态任务提示
  ✅ v3.10：下载设置页改为可滚动布局，保存/恢复/诊断按钮固定到底部，避免小窗口点不到

依赖：
  pip install yt-dlp pyinstaller

说明：
  - “暂停”采用 yt-dlp progress hook 协作式暂停：下载过程中会阻塞 hook 等待继续。
  - “取消”对队列任务立即有效；对正在下载的任务会在下一次 progress hook 触发时中断。
"""

import os
import sys
import json
import time
import queue
import shutil
import threading
import subprocess
import re
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "多站点批量下载器 v3.10 Pro"
APP_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = APP_DIR / "settings.json"
COMPLETED_DB = APP_DIR / "completed_tasks.json"

T = {
    "bg": "#0B1020", "panel": "#111827", "panel2": "#162033", "card": "#1F2937",
    "border": "#374151", "text": "#F9FAFB", "muted": "#9CA3AF",
    "accent": "#EF4444", "accent2": "#F97316", "success": "#22C55E",
    "warning": "#FACC15", "error": "#FB7185", "blue": "#60A5FA",
    "purple": "#A78BFA", "cyan": "#22D3EE", "pink": "#F472B6",
    "check_on": "#EF4444", "check_off": "#6B7280",
}

THEMES = {
    "极夜霓虹": {"bg":"#0B1020","panel":"#111827","panel2":"#162033","card":"#1F2937","border":"#374151","text":"#F9FAFB","muted":"#9CA3AF","accent":"#EF4444","accent2":"#F97316","success":"#22C55E","warning":"#FACC15","error":"#FB7185","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "YouTube 红黑": {"bg":"#0F0F0F","panel":"#181818","panel2":"#202020","card":"#242424","border":"#3A3A3A","text":"#FFFFFF","muted":"#A3A3A3","accent":"#FF0033","accent2":"#FF4444","success":"#00C853","warning":"#FFD600","error":"#FF5252","blue":"#448AFF","purple":"#B388FF","cyan":"#18FFFF","pink":"#FF80AB"},
    "赛博蓝紫": {"bg":"#050816","panel":"#0B1026","panel2":"#151B3D","card":"#20275A","border":"#3949AB","text":"#EEF2FF","muted":"#A5B4FC","accent":"#7C3AED","accent2":"#06B6D4","success":"#10B981","warning":"#F59E0B","error":"#F43F5E","blue":"#38BDF8","purple":"#C084FC","cyan":"#67E8F9","pink":"#F0ABFC"},
    "翡翠暗夜": {"bg":"#061512","panel":"#0B241E","panel2":"#12352E","card":"#153E35","border":"#1F6F5B","text":"#ECFDF5","muted":"#8FDCC2","accent":"#10B981","accent2":"#34D399","success":"#22C55E","warning":"#FBBF24","error":"#FB7185","blue":"#2DD4BF","purple":"#A78BFA","cyan":"#5EEAD4","pink":"#FDA4AF"},
    "琥珀黑金": {"bg":"#11100B","panel":"#1C180F","panel2":"#2B2415","card":"#3A2F19","border":"#806A2E","text":"#FFF7ED","muted":"#D6B46B","accent":"#F59E0B","accent2":"#F97316","success":"#84CC16","warning":"#FDE047","error":"#F43F5E","blue":"#60A5FA","purple":"#C084FC","cyan":"#22D3EE","pink":"#F472B6"},
    "葡萄酒红": {"bg":"#17070D","panel":"#250B14","panel2":"#3A1020","card":"#4A1728","border":"#7F1D1D","text":"#FFF1F2","muted":"#FDA4AF","accent":"#E11D48","accent2":"#FB7185","success":"#4ADE80","warning":"#FACC15","error":"#F43F5E","blue":"#93C5FD","purple":"#D8B4FE","cyan":"#67E8F9","pink":"#F9A8D4"},
    "深海蓝": {"bg":"#061221","panel":"#0A1B2F","panel2":"#102A46","card":"#12385F","border":"#1D4E89","text":"#EFF6FF","muted":"#93C5FD","accent":"#2563EB","accent2":"#0EA5E9","success":"#22C55E","warning":"#F59E0B","error":"#EF4444","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "石墨灰": {"bg":"#111827","panel":"#1F2937","panel2":"#273244","card":"#374151","border":"#4B5563","text":"#F9FAFB","muted":"#D1D5DB","accent":"#6B7280","accent2":"#9CA3AF","success":"#22C55E","warning":"#EAB308","error":"#EF4444","blue":"#3B82F6","purple":"#8B5CF6","cyan":"#06B6D4","pink":"#EC4899"},
    "护眼墨绿": {"bg":"#101A13","panel":"#18251C","panel2":"#223227","card":"#2C4032","border":"#44624A","text":"#F0FDF4","muted":"#B7D7C0","accent":"#16A34A","accent2":"#65A30D","success":"#22C55E","warning":"#CA8A04","error":"#DC2626","blue":"#0EA5E9","purple":"#8B5CF6","cyan":"#14B8A6","pink":"#DB2777"},
    "商务靛蓝": {"bg":"#111827","panel":"#172033","panel2":"#202A44","card":"#2B3654","border":"#45537A","text":"#F8FAFC","muted":"#CBD5E1","accent":"#4F46E5","accent2":"#2563EB","success":"#16A34A","warning":"#D97706","error":"#DC2626","blue":"#3B82F6","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "浅色云白": {"bg":"#F8FAFC","panel":"#FFFFFF","panel2":"#EEF2FF","card":"#F1F5F9","border":"#CBD5E1","text":"#0F172A","muted":"#64748B","accent":"#2563EB","accent2":"#0EA5E9","success":"#16A34A","warning":"#D97706","error":"#DC2626","blue":"#2563EB","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "浅色樱花": {"bg":"#FFF7FB","panel":"#FFFFFF","panel2":"#FCE7F3","card":"#FDF2F8","border":"#F9A8D4","text":"#4A044E","muted":"#9D174D","accent":"#EC4899","accent2":"#F472B6","success":"#16A34A","warning":"#D97706","error":"#E11D48","blue":"#2563EB","purple":"#A855F7","cyan":"#0891B2","pink":"#DB2777"},
    "浅色薄荷": {"bg":"#F0FDF4","panel":"#FFFFFF","panel2":"#DCFCE7","card":"#ECFDF5","border":"#86EFAC","text":"#052E16","muted":"#166534","accent":"#16A34A","accent2":"#14B8A6","success":"#22C55E","warning":"#CA8A04","error":"#DC2626","blue":"#2563EB","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "浅色暖阳": {"bg":"#FFFBEB","panel":"#FFFFFF","panel2":"#FEF3C7","card":"#FEF9C3","border":"#FCD34D","text":"#451A03","muted":"#92400E","accent":"#F59E0B","accent2":"#F97316","success":"#16A34A","warning":"#D97706","error":"#DC2626","blue":"#2563EB","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "北欧冰蓝": {"bg":"#ECFEFF","panel":"#F8FAFC","panel2":"#CFFAFE","card":"#E0F2FE","border":"#7DD3FC","text":"#082F49","muted":"#0369A1","accent":"#0284C7","accent2":"#06B6D4","success":"#16A34A","warning":"#CA8A04","error":"#DC2626","blue":"#2563EB","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "紫罗兰": {"bg":"#110A1F","panel":"#1E1235","panel2":"#2D1B4E","card":"#3B2565","border":"#6D28D9","text":"#F5F3FF","muted":"#C4B5FD","accent":"#8B5CF6","accent2":"#A855F7","success":"#22C55E","warning":"#FACC15","error":"#F43F5E","blue":"#60A5FA","purple":"#C084FC","cyan":"#22D3EE","pink":"#F472B6"},
    "玫瑰霓虹": {"bg":"#190017","panel":"#26021F","panel2":"#3B0731","card":"#4A0B3F","border":"#BE185D","text":"#FDF2F8","muted":"#F9A8D4","accent":"#EC4899","accent2":"#DB2777","success":"#22C55E","warning":"#FACC15","error":"#FB7185","blue":"#60A5FA","purple":"#C084FC","cyan":"#22D3EE","pink":"#F472B6"},
    "橙色脉冲": {"bg":"#170C05","panel":"#241205","panel2":"#3A1C08","card":"#4B250B","border":"#EA580C","text":"#FFF7ED","muted":"#FDBA74","accent":"#F97316","accent2":"#FB923C","success":"#22C55E","warning":"#FACC15","error":"#EF4444","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "高对比黑白": {"bg":"#000000","panel":"#080808","panel2":"#101010","card":"#1A1A1A","border":"#FFFFFF","text":"#FFFFFF","muted":"#D4D4D4","accent":"#FFFFFF","accent2":"#FACC15","success":"#00FF66","warning":"#FFFF00","error":"#FF3333","blue":"#33AAFF","purple":"#CC88FF","cyan":"#00FFFF","pink":"#FF66CC"},
    "终端绿": {"bg":"#020A05","panel":"#06120A","panel2":"#0A1F10","card":"#0E2B18","border":"#22C55E","text":"#DCFCE7","muted":"#86EFAC","accent":"#22C55E","accent2":"#84CC16","success":"#00FF66","warning":"#FACC15","error":"#F87171","blue":"#38BDF8","purple":"#A78BFA","cyan":"#5EEAD4","pink":"#F472B6"},
    "代码黑客": {"bg":"#09090B","panel":"#18181B","panel2":"#27272A","card":"#3F3F46","border":"#52525B","text":"#FAFAFA","muted":"#A1A1AA","accent":"#A3E635","accent2":"#22D3EE","success":"#22C55E","warning":"#EAB308","error":"#F43F5E","blue":"#38BDF8","purple":"#A78BFA","cyan":"#67E8F9","pink":"#F472B6"},
    "午夜钴蓝": {"bg":"#07111F","panel":"#0E1B2D","panel2":"#162A45","card":"#1E3A5F","border":"#1D4ED8","text":"#EFF6FF","muted":"#BFDBFE","accent":"#1D4ED8","accent2":"#3B82F6","success":"#22C55E","warning":"#FACC15","error":"#F43F5E","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "银河星空": {"bg":"#05051A","panel":"#0B0B2E","panel2":"#14144A","card":"#1D1D63","border":"#4338CA","text":"#EEF2FF","muted":"#C7D2FE","accent":"#6366F1","accent2":"#EC4899","success":"#22C55E","warning":"#FACC15","error":"#FB7185","blue":"#60A5FA","purple":"#C084FC","cyan":"#22D3EE","pink":"#F472B6"},
    "咖啡棕": {"bg":"#140F0B","panel":"#21170F","panel2":"#322318","card":"#463222","border":"#7C4A27","text":"#FEF3C7","muted":"#D6A56D","accent":"#A16207","accent2":"#D97706","success":"#65A30D","warning":"#FACC15","error":"#EF4444","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "青柠黑": {"bg":"#090D03","panel":"#111A06","panel2":"#1B2A0C","card":"#263A13","border":"#65A30D","text":"#F7FEE7","muted":"#BEF264","accent":"#84CC16","accent2":"#A3E635","success":"#22C55E","warning":"#FACC15","error":"#EF4444","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "孔雀蓝绿": {"bg":"#031B1B","panel":"#082F2F","panel2":"#0F4545","card":"#155E5E","border":"#0F766E","text":"#ECFEFF","muted":"#99F6E4","accent":"#14B8A6","accent2":"#06B6D4","success":"#22C55E","warning":"#FACC15","error":"#F43F5E","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "沙漠暖黄": {"bg":"#1B1205","panel":"#2B1C08","panel2":"#3F2A0E","card":"#573B14","border":"#A16207","text":"#FFF7ED","muted":"#FCD34D","accent":"#EAB308","accent2":"#F59E0B","success":"#65A30D","warning":"#FACC15","error":"#EF4444","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
    "钢铁蓝灰": {"bg":"#0F172A","panel":"#1E293B","panel2":"#273449","card":"#334155","border":"#64748B","text":"#F8FAFC","muted":"#CBD5E1","accent":"#0F766E","accent2":"#0284C7","success":"#16A34A","warning":"#D97706","error":"#DC2626","blue":"#2563EB","purple":"#7C3AED","cyan":"#0891B2","pink":"#DB2777"},
    "粉蓝渐变": {"bg":"#101828","panel":"#182338","panel2":"#24304A","card":"#303C5C","border":"#818CF8","text":"#F8FAFC","muted":"#C4B5FD","accent":"#60A5FA","accent2":"#F472B6","success":"#22C55E","warning":"#FACC15","error":"#FB7185","blue":"#60A5FA","purple":"#C084FC","cyan":"#22D3EE","pink":"#F472B6"},
    "纯黑OLED": {"bg":"#000000","panel":"#050505","panel2":"#0A0A0A","card":"#111111","border":"#262626","text":"#FFFFFF","muted":"#A3A3A3","accent":"#22D3EE","accent2":"#F472B6","success":"#22C55E","warning":"#FACC15","error":"#FB7185","blue":"#60A5FA","purple":"#A78BFA","cyan":"#22D3EE","pink":"#F472B6"},
}
for _name, _theme in THEMES.items():
    _theme.setdefault("check_on", _theme.get("accent", "#EF4444"))
    _theme.setdefault("check_off", _theme.get("muted", "#6B7280"))

SPEED_PROFILES = {
    "稳速兼容": {"concurrent_fragments": 8, "max_concurrent_tasks": 2, "retries": 8, "fragment_retries": 10, "http_chunk_size_mb": 10, "socket_timeout": 20, "buffersize_kb": 128, "throttled_rate_limit": "512K", "youtube_client": "android,web"},
    "极速推荐": {"concurrent_fragments": 16, "max_concurrent_tasks": 3, "retries": 10, "fragment_retries": 15, "http_chunk_size_mb": 16, "socket_timeout": 25, "buffersize_kb": 256, "throttled_rate_limit": "1M", "youtube_client": "android,web,ios"},
    "极限压榨": {"concurrent_fragments": 24, "max_concurrent_tasks": 4, "retries": 12, "fragment_retries": 20, "http_chunk_size_mb": 32, "socket_timeout": 30, "buffersize_kb": 512, "throttled_rate_limit": "2M", "youtube_client": "android,ios,web"},
    "单任务满速": {"concurrent_fragments": 32, "max_concurrent_tasks": 1, "retries": 12, "fragment_retries": 20, "http_chunk_size_mb": 32, "socket_timeout": 30, "buffersize_kb": 512, "throttled_rate_limit": "1M", "youtube_client": "android,ios,web"},
}

QUALITY_OPTIONS = {
    "最佳画质（自动）": "bestvideo+bestaudio/best",
    "2160p / 4K": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p / 2K": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "仅音频 (MP3)": "bestaudio/best",
    "仅音频 (M4A)": "bestaudio[ext=m4a]/bestaudio",
}
FORMAT_OPTIONS = {
    "MP4  (兼容性最好)": "mp4",
    "MKV  (支持多字幕轨)": "mkv",
    "WebM (原生格式)": "webm",
    "原始 (不转封装)": "",
}
SORT_OPTIONS = ["添加顺序", "标题 A-Z", "标题 Z-A", "格式", "状态", "时长短→长", "时长长→短", "进度低→高", "进度高→低", "添加时间新→旧"]
FILTER_OPTIONS = ["全部", "视频", "音频", "MP4", "MKV", "WebM", "原始", "待下载", "排队中", "下载中", "暂停", "已完成", "失败", "已取消"]
PLATFORM_FILTERS = ["YouTube", "TikTok", "抖音", "Bilibili", "快手", "Twitch", "X/Twitter", "Facebook", "Instagram", "Vimeo", "通用站点"]
CHECK_ON, CHECK_OFF = "☑", "☐"

STATUS_PENDING = "待下载"
STATUS_QUEUED = "排队中"
STATUS_RUNNING = "下载中"
STATUS_PAUSED = "暂停"
STATUS_MERGING = "合并中"
STATUS_DONE = "已完成"
STATUS_FAILED = "失败"
STATUS_CANCELED = "已取消"


def get_ytdlp_cmd_base():
    """优先使用当前 Python/虚拟环境里的 yt_dlp 模块。
    之前直接调用 PATH 里的 yt-dlp，Windows 上很容易调用到全局旧版本，
    结果就是 YouTube 能解析、抖音 /video/数字 却显示 Unsupported URL。
    """
    try:
        import yt_dlp  # noqa
        return [sys.executable, "-m", "yt_dlp"], "module"
    except Exception:
        exe = shutil.which("yt-dlp")
        if exe:
            return [exe], "cli"
    return [], None


def check_ytdlp():
    return get_ytdlp_cmd_base()[1]


def get_ytdlp_version():
    base, kind = get_ytdlp_cmd_base()
    if not base:
        return "", ""
    try:
        r = subprocess.run(base + ["--version"], capture_output=True, text=True, timeout=8, encoding="utf-8", errors="replace")
        return (r.stdout or r.stderr or "").strip(), " ".join(base)
    except Exception:
        return "", " ".join(base)


def fmt_bytes(n):
    try: n = float(n or 0)
    except Exception: return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_speed(bps):
    s = fmt_bytes(bps)
    return f"{s}/s" if s else ""


def fmt_time(sec):
    try: sec = int(sec)
    except Exception: return "--"
    if sec < 0: return "--"
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", str(text or ""))


def friendly_error(text):
    msg = strip_ansi(text)
    low = msg.lower()
    if "this live event has ended" in low:
        return "直播活动已结束，当前链接没有可下载的回放文件；若频道稍后生成回放，请重新解析该视频链接。"
    if "private video" in low:
        return "公开视频不可访问：该视频可能是私密视频，需要账号/Cookie。"
    if "sign in" in low or "login" in low:
        return "需要登录或 Cookie 才能下载。"
    if "unavailable" in low:
        return "视频当前不可用，可能被删除、地区限制或平台暂时拦截。"
    return msg


def detect_platform(url):
    u = str(url or "").lower()
    rules = [
        ("YouTube", ["youtube.com", "youtu.be"]),
        ("TikTok", ["tiktok.com"]),
        ("抖音", ["douyin.com"]),
        ("Bilibili", ["bilibili.com", "b23.tv"]),
        ("快手", ["kuaishou.com", "kwai.com"]),
        ("Twitch", ["twitch.tv"]),
        ("X/Twitter", ["x.com", "twitter.com"]),
        ("Facebook", ["facebook.com", "fb.watch"]),
        ("Instagram", ["instagram.com"]),
        ("Vimeo", ["vimeo.com"]),
    ]
    for name, keys in rules:
        if any(k in u for k in keys):
            return name
    return "通用站点" if u.startswith("http") else "未知"




# ─── 平台解析适配层 v3.6 ─────────────────────────────────────────────────────
# 说明：不同网站不能只靠同一条 yt-dlp 命令硬解析；这里为每个平台做独立 URL 规整、请求头、Cookie、解析模式和错误提示。
# 仍以 yt-dlp extractor 作为底层下载内核，避免维护不稳定的私有接口/签名算法。
class PlatformAdapter:
    name = "通用站点"
    domains = []
    prefer_cookie = False
    referer = ""

    def matches(self, url: str) -> bool:
        u = str(url or "").lower()
        return any(d in u for d in self.domains)

    def normalize(self, url: str) -> str:
        return str(url or "").strip()

    def candidates(self, url: str):
        normalized = self.normalize(url)
        items = [normalized]
        raw = str(url or "").strip()
        if raw and raw not in items:
            items.append(raw)
        return items

    def common_headers(self):
        headers = [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
            "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        ]
        if self.referer:
            headers.append(f"Referer: {self.referer}")
        return headers

    def command_modes(self):
        # flat-playlist 用于列表/播放列表；fallback-no-flat 用于部分单视频页 extractor 不吃 flat 的情况。
        return [
            ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"],
            ["--dump-json", "--no-warnings", "--ignore-errors"],
        ]

    def extra_args(self):
        args = []
        for h in self.common_headers():
            args += ["--add-header", h]
        return args

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip()
        return err[:260]


class YouTubeAdapter(PlatformAdapter):
    name = "YouTube"
    domains = ["youtube.com", "youtu.be"]
    referer = "https://www.youtube.com/"

    def candidates(self, url: str):
        raw = str(url or "").strip()
        out = [raw]
        # youtu.be 短链规整成 watch 链接，减少列表/短链异常。
        try:
            p = urlparse(raw)
            if "youtu.be" in p.netloc.lower():
                vid = p.path.strip("/")
                if vid:
                    q = ("?" + p.query) if p.query else ""
                    out.insert(0, f"https://www.youtube.com/watch?v={vid}{q}")
        except Exception:
            pass
        return list(dict.fromkeys([x for x in out if x]))


class DouyinAdapter(PlatformAdapter):
    name = "抖音"
    domains = ["douyin.com", "v.douyin.com"]
    prefer_cookie = True
    referer = "https://www.douyin.com/"

    def extract_aweme_id(self, url: str) -> str:
        raw = str(url or "").strip()
        try:
            p = urlparse(raw)
            m = re.search(r"/(?:video|note)/(\d{8,})", p.path)
            if m:
                return m.group(1)
            q = parse_qs(p.query)
            for key in ("modal_id", "aweme_id", "item_id", "video_id"):
                val = (q.get(key) or [""])[0]
                if val and val.isdigit():
                    return val
        except Exception:
            pass
        m = re.search(r"(?:modal_id|aweme_id|item_id|video_id)[=/](\d{8,})", raw)
        return m.group(1) if m else ""

    def normalize(self, url: str) -> str:
        raw = str(url or "").strip()
        aweme_id = self.extract_aweme_id(raw)
        if aweme_id:
            # 标准作品页强制规整，去掉 query，避免 old yt-dlp/跳转参数误判 Unsupported URL。
            return f"https://www.douyin.com/video/{aweme_id}"
        return raw

    def candidates(self, url: str):
        raw = str(url or "").strip()
        normalized = self.normalize(raw)
        out = [normalized]
        aweme_id = self.extract_aweme_id(raw)
        if aweme_id:
            out += [
                f"https://www.douyin.com/video/{aweme_id}",
                f"https://www.douyin.com/discover?modal_id={aweme_id}",
                f"https://www.douyin.com/jingxuan?modal_id={aweme_id}",
            ]
        if raw:
            out.append(raw)
        return list(dict.fromkeys([x for x in out if x]))

    def command_modes(self):
        # 抖音标准作品页必须先完整解析；flat 对单视频页经常拿不到有效信息。
        return [
            ["--dump-single-json", "--no-warnings"],
            ["--dump-json", "--no-warnings"],
            ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"],
        ]

    def extra_args(self):
        args = super().extra_args()
        # 抖音对 Cookie/UA/Referer 敏感，给 extractor 更多重试机会。
        args += ["--extractor-retries", "5", "--retry-sleep", "linear=1:4:2"]
        return args

    def make_stub_info(self, original_url: str):
        aweme_id = self.extract_aweme_id(original_url)
        if not aweme_id:
            return None
        normalized = f"https://www.douyin.com/video/{aweme_id}"
        return {
            "id": aweme_id,
            "title": f"抖音视频_{aweme_id}",
            "webpage_url": normalized,
            "url": normalized,
            "_source_url": normalized,
            "_original_input_url": original_url,
            "_platform_adapter": self.name,
            "_stub_only": True,
        }

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip()
        low = err.lower()
        if "unsupported url" in low:
            return "抖音标准 /video/数字 链接仍被 Unsupported URL，多半是程序调用到了系统 PATH 里的旧版 yt-dlp。v3.7 已改为优先使用当前虚拟环境 python -m yt_dlp；请运行 update_ytdlp.bat 后重试。"
        if "cookie" in low or "login" in low or "captcha" in low or "verify" in low or "fresh" in low:
            return "抖音需要 Fresh cookies：先用 Chrome/Edge 打开 douyin.com 并播放一次该视频，再在下载设置里填 chrome/edge，或选择刚导出的 cookies.txt。浏览器正在运行导致读取失败时，可关闭浏览器后重试。"
        return err[:260]


class TikTokAdapter(PlatformAdapter):
    name = "TikTok"
    domains = ["tiktok.com", "vm.tiktok.com"]
    prefer_cookie = True
    referer = "https://www.tiktok.com/"

    def command_modes(self):
        return [["--dump-json", "--no-warnings", "--ignore-errors"], ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "cookie" in low or "login" in low or "captcha" in low:
            return "TikTok 需要登录/Cookie 或触发风控；建议设置浏览器 Cookie 后重试。"
        return err[:260]


class BilibiliAdapter(PlatformAdapter):
    name = "Bilibili"
    domains = ["bilibili.com", "b23.tv"]
    prefer_cookie = True
    referer = "https://www.bilibili.com/"

    def command_modes(self):
        # B站合集/分P保留 flat；单 BV 链接再 fallback 到完整解析。
        return [["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"], ["--dump-json", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "login" in low or "cookie" in low or "vip" in low:
            return "B站该视频可能需要登录/Cookie、会员权限或地区权限；在设置里填 chrome/edge 后重试。"
        return err[:260]


class KuaishouAdapter(PlatformAdapter):
    name = "快手"
    domains = ["kuaishou.com", "kwai.com"]
    prefer_cookie = True
    referer = "https://www.kuaishou.com/"

    def command_modes(self):
        return [["--dump-json", "--no-warnings", "--ignore-errors"], ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "unsupported" in low:
            return "快手链接可能是分享跳转/短链/主页入口，不是作品直链。请复制作品详情页链接，必要时启用浏览器 Cookie。"
        return err[:260]


class TwitchAdapter(PlatformAdapter):
    name = "Twitch"
    domains = ["twitch.tv"]
    referer = "https://www.twitch.tv/"

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "subscriber" in low or "login" in low or "token" in low:
            return "Twitch VOD/Clip 可能需要登录、订阅权限或地区权限；请启用浏览器 Cookie。"
        return err[:260]


class TwitterAdapter(PlatformAdapter):
    name = "X/Twitter"
    domains = ["x.com", "twitter.com"]
    prefer_cookie = True
    referer = "https://x.com/"

    def command_modes(self):
        return [["--dump-json", "--no-warnings", "--ignore-errors"], ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "login" in low or "cookie" in low or "guest token" in low or "authorization" in low:
            return "X/Twitter 经常需要登录态。请在浏览器登录 X 后，在设置里填写 chrome/edge/firefox 读取 Cookie。"
        return err[:260]


class FacebookAdapter(PlatformAdapter):
    name = "Facebook"
    domains = ["facebook.com", "fb.watch"]
    prefer_cookie = True
    referer = "https://www.facebook.com/"

    def command_modes(self):
        return [["--dump-json", "--no-warnings", "--ignore-errors"], ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "login" in low or "cookie" in low or "private" in low:
            return "Facebook 视频常需要登录态或公开权限。请确认浏览器能播放，再设置浏览器 Cookie。"
        return err[:260]


class InstagramAdapter(PlatformAdapter):
    name = "Instagram"
    domains = ["instagram.com"]
    prefer_cookie = True
    referer = "https://www.instagram.com/"

    def command_modes(self):
        return [["--dump-json", "--no-warnings", "--ignore-errors"], ["--dump-json", "--flat-playlist", "--no-warnings", "--ignore-errors"]]

    def hint(self, stderr: str) -> str:
        err = strip_ansi(stderr).strip(); low = err.lower()
        if "login" in low or "cookie" in low or "private" in low:
            return "Instagram 通常需要登录态/Cookie；请在浏览器登录并确认能播放，再设置浏览器 Cookie。"
        return err[:260]


class VimeoAdapter(PlatformAdapter):
    name = "Vimeo"
    domains = ["vimeo.com"]
    referer = "https://vimeo.com/"


PLATFORM_ADAPTERS = [
    YouTubeAdapter(), DouyinAdapter(), TikTokAdapter(), BilibiliAdapter(), KuaishouAdapter(),
    TwitchAdapter(), TwitterAdapter(), FacebookAdapter(), InstagramAdapter(), VimeoAdapter(), PlatformAdapter()
]


def get_adapter(url: str) -> PlatformAdapter:
    for a in PLATFORM_ADAPTERS:
        if a.matches(url):
            return a
    return PLATFORM_ADAPTERS[-1]


def normalize_source_url(url: str) -> str:
    return get_adapter(url).normalize(url)


def parse_error_hint(url: str, stderr: str) -> str:
    return get_adapter(url).hint(stderr)


def safe_filesize_from_info(info):
    for key in ("filesize", "filesize_approx", "total_bytes", "total_bytes_estimate"):
        v = safe_int(info.get(key), 0)
        if v > 0:
            return v
    # 有些 extractor 会把格式列表里的大小写在 formats 中，取最大的可用估算
    sizes = []
    for f in info.get("formats") or []:
        v = safe_int(f.get("filesize") or f.get("filesize_approx"), 0)
        if v > 0: sizes.append(v)
    return max(sizes) if sizes else 0


def is_live_content(info: dict) -> bool:
    """识别直播/预约直播/直播回放。用户当前需求是只下载普通视频源，默认过滤直播类内容。"""
    if not isinstance(info, dict):
        return False
    live_status = str(info.get("live_status") or "").lower().strip()
    if live_status in {"is_live", "is_upcoming", "post_live", "was_live"}:
        return True
    if info.get("is_live") is True or info.get("was_live") is True:
        return True
    # 有些 extractor 没给 live_status，但标题/类型可能直接标记为 live
    media_type = str(info.get("_type") or info.get("media_type") or "").lower()
    if media_type in {"live", "livestream"}:
        return True
    return False


def safe_int(v, default=0):
    try: return int(v)
    except Exception: return default


@dataclass
class DownloadSettings:
    output_dir: str = field(default_factory=lambda: str(Path.home() / "Downloads"))
    theme_name: str = "极夜霓虹"
    speed_profile: str = "极速推荐"
    quality_label: str = "最佳画质（自动）"
    format_label: str = "MP4  (兼容性最好)"
    concurrent_fragments: int = 16
    max_concurrent_tasks: int = 3
    retries: int = 10
    fragment_retries: int = 15
    http_chunk_size_mb: int = 16
    socket_timeout: int = 25
    buffersize_kb: int = 256
    throttled_rate_limit: str = "1M"   # 低于该速度时让 yt-dlp 认为被限速并重连/换策略
    youtube_client: str = "android,web,ios"
    rate_limit: str = ""               # example: 2M / 500K；为空不限速
    write_subs: bool = False
    write_auto_subs: bool = False
    sub_langs: str = "zh-Hans,en"
    embed_subs: bool = False
    write_thumbnail: bool = False
    write_description: bool = False
    restrict_filenames: bool = False
    continue_download: bool = True
    no_overwrites: bool = True
    skip_live_content: bool = True      # 默认只下载普通视频，跳过直播/预约直播/直播回放
    cookies_from_browser: str = ""       # 可选：chrome / edge / firefox；抖音、X、Facebook 等站点需要登录态时使用
    browser_profile: str = ""            # 可选：浏览器配置目录/Profile，例如 Default / Profile 1；为空自动
    cookie_file: str = ""                # 可选：Netscape cookies.txt 文件；优先级高于 cookies_from_browser
    parse_timeout: int = 240              # 解析超时秒数；抖音/海外站点网络慢时建议 240-360
    force_ipv4: bool = False              # 网络环境 IPv6 不稳时可打开
    auto_cookie_fallback: bool = True      # 未手动配置 Cookie 时，抖音自动尝试 edge/chrome/firefox


@dataclass
class TaskState:
    row_id: int
    url: str
    title: str = "未知标题"
    duration: int = 0
    uploader: str = ""
    source: str = ""
    platform: str = "YouTube"
    file_format: str = "mp4"
    media_type: str = "视频"
    is_live_content: bool = False
    status: str = STATUS_PENDING
    checked: bool = True
    progress: float = 0.0
    speed_bps: float = 0.0
    speed_text: str = ""
    eta_sec: int = -1
    eta_text: str = "--"
    elapsed_sec: int = 0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    output_path: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    finished_at: float = 0.0


class ParseWorker(threading.Thread):
    """多平台解析线程。

    v3.9 重点：抖音 Fresh cookies 不是 URL 解析算法问题，而是平台风控要求。
    若用户没有手动配置 Cookie，本线程会按 edge -> chrome -> firefox 自动尝试读取浏览器 Cookie；
    若仍失败，不再误报“不是普通视频”，而是回传一个 NEED_COOKIE 占位任务，方便用户在列表里看到问题。
    """
    NEED_COOKIE = "NEED_COOKIE"

    def __init__(self, urls, callback, log_fn, settings: DownloadSettings):
        super().__init__(daemon=True)
        self.urls = urls
        self.callback = callback
        self.log = log_fn
        self.settings = settings
        self.cookies_from_browser = str(getattr(settings, "cookies_from_browser", "") or "").strip().lower()
        self.browser_profile = str(getattr(settings, "browser_profile", "") or "").strip()
        self.cookie_file = str(getattr(settings, "cookie_file", "") or "").strip()
        self.parse_timeout = max(30, safe_int(getattr(settings, "parse_timeout", 240), 240))
        self.force_ipv4 = bool(getattr(settings, "force_ipv4", False))
        self.auto_cookie_fallback = bool(getattr(settings, "auto_cookie_fallback", True))

    def _cookie_cli_args(self, browser_override: str = ""):
        args = []
        if self.cookie_file and Path(self.cookie_file).exists():
            args += ["--cookies", self.cookie_file]
        else:
            browser = (browser_override or self.cookies_from_browser or "").strip().lower()
            if browser:
                browser_arg = browser
                if self.browser_profile and not browser_override:
                    browser_arg = f"{browser_arg}:{self.browser_profile}"
                args += ["--cookies-from-browser", browser_arg]
        return args

    def _build_cmd(self, adapter: PlatformAdapter, mode_args, url, browser_override: str = ""):
        base, _kind = get_ytdlp_cmd_base()
        cmd = base + list(mode_args) + adapter.extra_args()
        cmd += self._cookie_cli_args(browser_override=browser_override)
        if self.force_ipv4:
            cmd += ["--force-ipv4"]
        cmd += ["--socket-timeout", str(max(10, min(120, self.parse_timeout // 4)))]
        cmd.append(url)
        return cmd

    def _has_cookie_config(self):
        return bool((self.cookie_file and Path(self.cookie_file).exists()) or self.cookies_from_browser)

    def _cookie_attempts_for(self, adapter: PlatformAdapter):
        # 返回 (label, browser_override)。browser_override 为空表示使用用户手动配置。
        attempts = [("手动Cookie配置" if self._has_cookie_config() else "无Cookie", "")]
        if isinstance(adapter, DouyinAdapter) and (not self._has_cookie_config()) and self.auto_cookie_fallback:
            # Windows 用户常用 Edge/Chrome；逐个尝试。若浏览器未安装/无 Cookie，yt-dlp 会返回错误，再试下一个。
            attempts += [("自动 Edge Cookie", "edge"), ("自动 Chrome Cookie", "chrome"), ("自动 Firefox Cookie", "firefox")]
        return attempts

    def _make_cookie_required_info(self, adapter: PlatformAdapter, original_url: str, message: str):
        if isinstance(adapter, DouyinAdapter):
            aweme_id = adapter.extract_aweme_id(original_url) or "unknown"
            normalized = adapter.normalize(original_url) or original_url
            return {
                "id": aweme_id,
                "title": f"需要Cookie后重试_抖音视频_{aweme_id}",
                "webpage_url": normalized,
                "url": normalized,
                "_source_url": normalized,
                "_original_input_url": original_url,
                "_platform_adapter": adapter.name,
                "_cookie_required": True,
                "_parse_error": message,
            }
        return None

    def _parse_one_url(self, original_url: str):
        adapter = get_adapter(original_url)
        candidates = adapter.candidates(original_url)
        self.log(f"🧩 使用 {adapter.name} 专用解析器", "purple")

        if adapter.prefer_cookie and not self._has_cookie_config():
            self.log(f"💡 {adapter.name} 常需要新鲜 Cookie；v3.9 会先自动尝试 Edge/Chrome/Firefox。若仍失败，请导入 cookies.txt。", "warning")
        elif adapter.prefer_cookie:
            src = f"cookies.txt：{self.cookie_file}" if self.cookie_file else f"浏览器：{self.cookies_from_browser}{(' / '+self.browser_profile) if self.browser_profile else ''}"
            self.log(f"🍪 {adapter.name} 已启用 Cookie 来源：{src}", "purple")

        parsed_ok = False
        fresh_cookie_seen = False
        fresh_cookie_msg = ""
        unsupported_seen = False
        seen_cmds = set()

        for attempt_label, browser_override in self._cookie_attempts_for(adapter):
            if browser_override:
                self.log(f"🍪 {adapter.name} 尝试读取 {browser_override} 浏览器 Cookie", "purple")
            for url in candidates:
                if url != original_url:
                    self.log(f"🔁 已规整链接：{original_url[:72]} → {url}", "purple")
                for mode_args in adapter.command_modes():
                    key = (tuple(mode_args), url, browser_override)
                    if key in seen_cmds:
                        continue
                    seen_cmds.add(key)
                    self.log(f"🔍 解析中[{adapter.name}/{attempt_label}]：{url[:90]}…", "info")
                    try:
                        result = subprocess.run(
                            self._build_cmd(adapter, mode_args, url, browser_override=browser_override),
                            capture_output=True, text=True, timeout=self.parse_timeout,
                            encoding="utf-8", errors="replace"
                        )
                        stdout = result.stdout.strip()
                        stderr = result.stderr or ""
                        low = stderr.lower()
                        if "fresh cookies" in low or (isinstance(adapter, DouyinAdapter) and "cookies are needed" in low):
                            fresh_cookie_seen = True
                            fresh_cookie_msg = adapter.hint(stderr)
                            self.log(f"⚠️ {adapter.name} Cookie 不新鲜或不可读：{fresh_cookie_msg}", "warning")
                            # 当前 cookie 源无效，尝试下一个浏览器/cookie 源；不要再走 generic fallback。
                            break
                        if "unsupported url" in low:
                            unsupported_seen = True
                        if result.returncode != 0 and not stdout:
                            hint = adapter.hint(stderr)
                            self.log(f"⚠️ {adapter.name} 解析失败：{hint}", "warning")
                            continue
                        lines = [x for x in result.stdout.splitlines() if x.strip()]
                        if not lines:
                            self.log(f"⚠️ {adapter.name} 无结果：{url[:90]}", "warning")
                            continue
                        added_in_mode = 0
                        for line in lines:
                            try:
                                info = json.loads(line)
                                if not isinstance(info, dict):
                                    continue
                                info["_source_url"] = url
                                info["_original_input_url"] = original_url
                                info["_platform_adapter"] = adapter.name
                                self.callback(info)
                                added_in_mode += 1
                                parsed_ok = True
                            except json.JSONDecodeError:
                                continue
                        if added_in_mode:
                            self.log(f"✅ {adapter.name} 解析成功：{added_in_mode} 条", "success")
                            return True
                    except FileNotFoundError:
                        self.log("❌ 未找到 yt-dlp，请先安装：pip install yt-dlp", "error")
                        return False
                    except subprocess.TimeoutExpired:
                        self.log(f"⏱️ {adapter.name} 解析超时：{url[:90]}；可把解析超时秒数调到 300-360，并检查网络/代理。", "warning")
                    except Exception as e:
                        self.log(f"❌ {adapter.name} 解析异常：{e}", "error")
                # 如果是 fresh cookie，当前 candidate 的其他模式也没意义，换 cookie 源。
                if fresh_cookie_seen and isinstance(adapter, DouyinAdapter):
                    break

        if fresh_cookie_seen and isinstance(adapter, DouyinAdapter):
            msg = fresh_cookie_msg or "抖音需要 Fresh cookies。请先在浏览器打开并播放该视频，再使用 chrome/edge 或导入 cookies.txt。"
            self.log("🍪 抖音确认是 Cookie 问题，不是普通视频识别问题；已停止无效 fallback。", "error")
            stub = self._make_cookie_required_info(adapter, original_url, msg)
            if stub:
                self.callback(stub)
            return self.NEED_COOKIE

        # 抖音兜底：只有在不是 Fresh cookies 的情况下才创建普通兜底任务。
        if not parsed_ok and isinstance(adapter, DouyinAdapter) and not fresh_cookie_seen:
            stub = adapter.make_stub_info(original_url)
            if stub:
                if unsupported_seen:
                    stub["_parse_error"] = "yt-dlp 当前抖音 extractor 不支持该链接或版本过旧；请运行 update_ytdlp.bat。"
                self.log("⚠️ 抖音完整元数据暂未取到，已按作品 ID 创建任务；若下载失败，请更新 yt-dlp 或启用浏览器 Cookie。", "warning")
                self.callback(stub)
                return True
        return parsed_ok

    def run(self):
        for original_url in self.urls:
            original_url = original_url.strip()
            if not original_url:
                continue
            ok = self._parse_one_url(original_url)
            if ok is self.NEED_COOKIE:
                continue
            if not ok:
                adapter = get_adapter(original_url)
                self.log(f"❌ {adapter.name} 没有解析出可下载结果：若是抖音/X/Facebook/TikTok，请优先检查 Cookie；若是列表页，请换成作品详情页。", "error")


class DownloadWorker(threading.Thread):
    def __init__(self, items, settings: DownloadSettings, events, progress_cb, done_cb, log_fn, global_cancel, global_pause):
        super().__init__(daemon=True)
        self.items = items
        self.settings = settings
        self.events = events
        self.progress_cb = progress_cb
        self.done_cb = done_cb
        self.log = log_fn
        self.global_cancel = global_cancel
        self.global_pause = global_pause

    def _wait_if_paused(self, rid):
        ev = self.events[rid]
        while not self.global_cancel.is_set() and not ev["cancel"].is_set() and (self.global_pause.is_set() or ev["pause"].is_set()):
            self.progress_cb(rid, {"status": STATUS_PAUSED})
            time.sleep(0.25)

    @staticmethod
    def _parse_rate_to_bytes(value):
        txt = str(value or "").strip().upper()
        if not txt:
            return None
        try:
            if txt.endswith("K"):
                return int(float(txt[:-1]) * 1024)
            if txt.endswith("M"):
                return int(float(txt[:-1]) * 1024 * 1024)
            return int(float(txt))
        except Exception:
            return None

    def _build_ydl_opts(self, task: TaskState):
        s = self.settings
        fmt = QUALITY_OPTIONS.get(s.quality_label, QUALITY_OPTIONS["最佳画质（自动）"])
        outtmpl = os.path.join(s.output_dir, "%(title).180B [%(id)s].%(ext)s")
        is_audio = "bestaudio" in fmt and "bestvideo" not in fmt
        opts = {
            "format": fmt,
            "outtmpl": outtmpl,
            "progress_hooks": [self._make_hook(task.row_id)],
            "concurrent_fragment_downloads": max(1, min(32, int(s.concurrent_fragments))),
            "quiet": True,
            "no_warnings": True,
            "noprogress": False,
            "retries": max(0, int(s.retries)),
            "fragment_retries": max(0, int(s.fragment_retries)),
            "continuedl": bool(s.continue_download),
            "overwrites": not bool(s.no_overwrites),
            "restrictfilenames": bool(s.restrict_filenames),
            "windowsfilenames": True,
            "socket_timeout": max(5, int(s.socket_timeout)),
            "buffersize": max(16, int(s.buffersize_kb)) * 1024,
            "http_chunk_size": max(1, int(s.http_chunk_size_mb)) * 1024 * 1024,
            "throttledratelimit": self._parse_rate_to_bytes(s.throttled_rate_limit),
            "extractor_args": {"youtube": {"player_client": [x.strip() for x in s.youtube_client.split(",") if x.strip()]}},
        }
        cookie_file = str(getattr(s, "cookie_file", "") or "").strip()
        if cookie_file and Path(cookie_file).exists():
            opts["cookiefile"] = cookie_file
        elif str(getattr(s, "cookies_from_browser", "")).strip():
            browser = str(s.cookies_from_browser).strip().lower()
            profile = str(getattr(s, "browser_profile", "") or "").strip()
            opts["cookiesfrombrowser"] = (browser, profile, None, None) if profile else (browser,)
        if bool(getattr(s, "force_ipv4", False)):
            opts["forceipv4"] = True
        if s.rate_limit.strip():
            opts["ratelimit"] = s.rate_limit.strip()
        if is_audio:
            codec = "m4a" if "M4A" in s.quality_label else "mp3"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": codec, "preferredquality": "192"}]
        else:
            out_fmt = FORMAT_OPTIONS.get(s.format_label, "mp4")
            if out_fmt:
                opts["merge_output_format"] = out_fmt
        if s.write_subs:
            opts["writesubtitles"] = True
        if s.write_auto_subs:
            opts["writeautomaticsub"] = True
        if s.sub_langs.strip():
            opts["subtitleslangs"] = [x.strip() for x in s.sub_langs.split(",") if x.strip()]
        if s.embed_subs:
            opts["embedsubtitles"] = True
        if s.write_thumbnail:
            opts["writethumbnail"] = True
        if s.write_description:
            opts["writedescription"] = True
        return opts

    def _make_hook(self, rid):
        def hook(d):
            ev = self.events[rid]
            if self.global_cancel.is_set() or ev["cancel"].is_set():
                raise Exception("用户取消")
            self._wait_if_paused(rid)
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                speed = d.get("speed") or 0
                eta = d.get("eta")
                pct = (done / total * 100) if total else 0
                self.progress_cb(rid, {
                    "status": STATUS_RUNNING,
                    "progress": min(pct, 99),
                    "speed_bps": speed,
                    "speed_text": (d.get("_speed_str") or "").strip() or fmt_speed(speed),
                    "eta_sec": safe_int(eta, -1),
                    "eta_text": (d.get("_eta_str") or "").strip() or (fmt_time(eta) if eta is not None else "--"),
                    "downloaded_bytes": safe_int(done, 0),
                    "total_bytes": safe_int(total, 0),
                })
            elif d.get("status") == "finished":
                self.progress_cb(rid, {"status": STATUS_MERGING, "progress": 99, "eta_text": "合并中", "output_path": d.get("filename", "")})
        return hook

    def _dl_one(self, task: TaskState, ytdlp_mod):
        rid = task.row_id
        ev = self.events[rid]
        if self.settings.skip_live_content and getattr(task, "is_live_content", False):
            self.done_cb(rid, False, STATUS_CANCELED, "已跳过直播类内容")
            self.log(f"⏭ 已跳过直播类内容：{task.title[:60]}", "warning")
            return
        if self.global_cancel.is_set() or ev["cancel"].is_set():
            self.done_cb(rid, False, STATUS_CANCELED, "用户取消")
            return
        self._wait_if_paused(rid)
        self.progress_cb(rid, {"status": STATUS_RUNNING, "started_at": time.time(), "progress": 0})
        self.log(f"⬇️ 开始下载：{task.title[:70]}", "info")
        try:
            opts = self._build_ydl_opts(task)
            with ytdlp_mod.YoutubeDL(opts) as ydl:
                ydl.download([task.url])
            if ev["cancel"].is_set() or self.global_cancel.is_set():
                self.done_cb(rid, False, STATUS_CANCELED, "用户取消")
            else:
                self.progress_cb(rid, {"progress": 100, "eta_text": "0:00"})
                self.done_cb(rid, True, STATUS_DONE, "")
                self.log(f"✅ 完成：{task.title[:70]}", "success")
        except Exception as e:
            msg = friendly_error(e)
            if "用户取消" in msg:
                self.done_cb(rid, False, STATUS_CANCELED, msg)
                self.log(f"⏹ 已取消：{task.title[:60]}", "warning")
            else:
                self.done_cb(rid, False, STATUS_FAILED, msg)
                self.log(f"❌ 失败：{task.title[:50]} → {msg[:220]}", "error")

    def run(self):
        try:
            import yt_dlp as ytdlp_mod
        except Exception:
            self.log("❌ yt-dlp 模块未安装：pip install yt-dlp", "error")
            for task in self.items:
                self.done_cb(task.row_id, False, STATUS_FAILED, "yt-dlp 未安装")
            return
        max_workers = max(1, min(12, int(self.settings.max_concurrent_tasks)))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = []
            for t in self.items:
                if self.global_cancel.is_set():
                    self.done_cb(t.row_id, False, STATUS_CANCELED, "全局取消")
                    continue
                self.progress_cb(t.row_id, {"status": STATUS_QUEUED})
                futures.append(pool.submit(self._dl_one, t, ytdlp_mod))
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    self.log(f"⚠️ 下载线程异常：{e}", "warning")


class DetailsDialog(tk.Toplevel):
    def __init__(self, parent, task: TaskState):
        super().__init__(parent)
        self.title("任务详情")
        self.geometry("720x520")
        self.configure(bg=T["bg"])
        self.transient(parent)
        self.grab_set()
        box = tk.Frame(self, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        box.pack(fill="both", expand=True, padx=14, pady=14)
        title = tk.Label(box, text=task.title, bg=T["panel"], fg=T["text"], font=("Microsoft YaHei UI", 13, "bold"), wraplength=660, justify="left")
        title.pack(anchor="w", padx=14, pady=(14, 8))
        rows = [
            ("状态", task.status), ("进度", f"{task.progress:.1f}%"), ("速度", task.speed_text),
            ("剩余时间", task.eta_text), ("已用时间", fmt_time(task.elapsed_sec)), ("文件格式", task.file_format),
            ("媒体类型", task.media_type), ("站点", task.platform), ("时长", fmt_time(task.duration) if task.duration else "--"),
            ("文件大小", fmt_bytes(task.total_bytes) if task.total_bytes else "--"),
            ("上传者", task.uploader or "--"), ("文件来源", task.source or "--"),
            ("已下载", f"{fmt_bytes(task.downloaded_bytes)} / {fmt_bytes(task.total_bytes)}" if task.total_bytes else "--"),
            ("输出路径", task.output_path or "--"), ("错误信息", task.error or "--"),
            ("URL", task.url),
        ]
        grid = tk.Frame(box, bg=T["panel"])
        grid.pack(fill="both", expand=True, padx=14, pady=8)
        for i, (k, v) in enumerate(rows):
            tk.Label(grid, text=k+"：", bg=T["panel"], fg=T["muted"], width=12, anchor="e").grid(row=i, column=0, sticky="ne", pady=5)
            tk.Label(grid, text=str(v), bg=T["panel"], fg=T["text"], anchor="w", wraplength=540, justify="left").grid(row=i, column=1, sticky="nw", pady=5)
        ttk.Button(box, text="关闭", command=self.destroy).pack(anchor="e", padx=14, pady=(0,14))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1380x860")
        self.minsize(1120, 720)
        self.tasks = {}
        self.row_refs = {"pending": {}, "running": {}, "completed": {}}
        self.next_id = 0
        self.log_queue = queue.Queue()
        self.settings = self.load_settings()
        self.platform_filter_vars = {}
        self.apply_theme(self.settings.theme_name, rebuild=False)
        self.configure(bg=T["bg"])
        self.events = {}
        self.global_cancel = threading.Event()
        self.global_pause = threading.Event()
        self.worker = None
        self.total_start_at = 0.0
        self._setup_style()
        self._build_ui()
        self.load_completed_db()
        self.after(120, self.process_logs)
        self.after(500, self.tick)
        self.check_startup()
        self.bind_hotkeys()

    def apply_theme(self, theme_name=None, rebuild=True):
        """即时切换主题。
        rebuild=True 时重建所有界面控件，因此不需要重启软件。
        """
        name = theme_name if theme_name in THEMES else "极夜霓虹"
        T.update(THEMES[name])
        self.settings.theme_name = name
        if rebuild:
            self.save_settings()
            self.rebuild_ui_after_theme_change()
            self.log(f"🎨 已即时切换皮肤：{name}", "success")

    def rebuild_ui_after_theme_change(self):
        # 保存当前标签页，避免切换主题后跳回第一页
        current_text = ""
        try:
            current_text = self.nb.tab(self.nb.select(), "text")
        except Exception:
            pass
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=T["bg"])
        self._setup_style()
        self._build_ui()
        self.refresh_all_views()
        self.update_cards()
        self.check_startup()
        # 恢复用户正在看的标签页
        if current_text:
            for tab_id in self.nb.tabs():
                if self.nb.tab(tab_id, "text") == current_text:
                    self.nb.select(tab_id)
                    break

    def bind_hotkeys(self):
        # Ctrl+Tab / Ctrl+Shift+Tab 快速切换皮肤；F7/F8 也可切换，避免和输入框 Tab 缩进冲突。
        self.bind_all("<Control-Tab>", lambda e: self.next_theme())
        self.bind_all("<Control-Shift-Tab>", lambda e: self.prev_theme())
        self.bind_all("<F8>", lambda e: self.next_theme())
        self.bind_all("<F7>", lambda e: self.prev_theme())

    def next_theme(self):
        names = list(THEMES.keys())
        i = names.index(self.settings.theme_name) if self.settings.theme_name in names else 0
        self.apply_theme(names[(i + 1) % len(names)], rebuild=True)
        return "break"

    def prev_theme(self):
        names = list(THEMES.keys())
        i = names.index(self.settings.theme_name) if self.settings.theme_name in names else 0
        self.apply_theme(names[(i - 1) % len(names)], rebuild=True)
        return "break"

    def apply_speed_profile(self, profile_name=None, silent=False):
        name = profile_name if profile_name in SPEED_PROFILES else self.setting_vars.get("speed_profile", tk.StringVar(value="极速推荐")).get()
        if name not in SPEED_PROFILES:
            name = "极速推荐"
        prof = SPEED_PROFILES[name]
        for k, v in prof.items():
            if k in self.setting_vars:
                self.setting_vars[k].set(str(v))
            if hasattr(self.settings, k):
                setattr(self.settings, k, v)
        self.settings.speed_profile = name
        if "speed_profile" in self.setting_vars:
            self.setting_vars["speed_profile"].set(name)
        self.save_settings_from_ui(log_saved=False)
        if not silent:
            self.log(f"🚀 已应用下载提速配置：{name} | 同时任务×{self.settings.max_concurrent_tasks} | 分片×{self.settings.concurrent_fragments} | chunk={self.settings.http_chunk_size_mb}MB", "success")
            messagebox.showinfo("极速配置已应用", f"{name} 已应用。\n推荐起步：同时任务×{self.settings.max_concurrent_tasks}，分片×{self.settings.concurrent_fragments}。")

    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=T["bg"], foreground=T["text"], fieldbackground=T["card"], bordercolor=T["border"], font=("Microsoft YaHei UI", 10))
        s.configure("TFrame", background=T["bg"])
        s.configure("TLabel", background=T["bg"], foreground=T["text"])
        s.configure("TButton", background=T["card"], foreground=T["text"], borderwidth=0, padding=(10, 6))
        s.map("TButton", background=[("active", T["border"]), ("pressed", T["border"])])
        s.configure("TNotebook", background=T["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=T["card"], foreground=T["text"], padding=(16, 8), borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", T["accent"]), ("active", T["panel2"])] )
        s.configure("TCombobox", fieldbackground=T["card"], background=T["card"], foreground=T["text"], arrowcolor=T["text"])
        for name, color in [("Red", T["accent"]), ("Green", T["success"]), ("Blue", T["blue"]), ("Yellow", T["warning"]), ("Purple", T["purple"]), ("Cyan", T["cyan"]), ("Pink", T["pink"] )]:
            s.configure(f"{name}.Horizontal.TProgressbar", troughcolor=T["border"], background=color, thickness=10, borderwidth=0)
        s.configure("Treeview", background=T["panel"], fieldbackground=T["panel"], foreground=T["text"], rowheight=31, borderwidth=0)
        s.configure("Treeview.Heading", background=T["card"], foreground=T["text"], relief="flat", font=("Microsoft YaHei UI", 9, "bold"))
        s.map("Treeview", background=[("selected", T["accent"])], foreground=[("selected", "white")])

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=8)
        left = tk.Frame(body, bg=T["bg"])
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg=T["bg"], width=330)
        right.pack(side="right", fill="y", padx=(8,0))
        right.pack_propagate(False)
        self._build_url_panel(left)
        self._build_filter_bar(left)
        # 固定操作按钮放在任务表格上方，避免窗口缩放后被 Treeview 挤出可视区域。
        self._build_bottom_controls(left)
        self._build_notebook(left)
        self._build_log_panel(right)

    def _build_header(self):
        head = tk.Frame(self, bg=T["panel"], height=78, highlightthickness=1, highlightbackground=T["border"])
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text="▶ 多站点批量下载器  v3.10 Pro", bg=T["panel"], fg=T["text"], font=("Microsoft YaHei UI", 18, "bold")).pack(side="left", padx=18)
        self.badge = tk.Label(head, text="检测中…", bg=T["panel"], fg=T["warning"], font=("Microsoft YaHei UI", 10, "bold"))
        self.badge.pack(side="right", padx=18)
        self.cards = {}
        cardrow = tk.Frame(head, bg=T["panel"])
        cardrow.pack(side="right", padx=10)
        for key, label, color in [("total", "任务", T["cyan"]), ("running", "任务中", T["warning"]), ("done", "完成", T["success"]), ("speed", "总速度", T["blue"]), ("eta", "剩余", T["purple"]), ("elapsed", "已用", T["pink"] )]:
            c = tk.Frame(cardrow, bg=T["card"], highlightthickness=1, highlightbackground=color)
            c.pack(side="left", padx=4, pady=8)
            tk.Label(c, text=label, bg=T["card"], fg=T["muted"], font=("Microsoft YaHei UI", 8)).pack(padx=10, pady=(4,0))
            val = tk.Label(c, text="0", bg=T["card"], fg=color, font=("Consolas", 12, "bold"))
            val.pack(padx=10, pady=(0,4))
            self.cards[key] = val

    def _build_url_panel(self, parent):
        p = tk.Frame(parent, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        p.pack(fill="x", pady=(0,8))
        top = tk.Frame(p, bg=T["panel"]); top.pack(fill="x", padx=10, pady=(8,4))
        tk.Label(top, text="📋 URL 输入区（YouTube / TikTok / 抖音 / B站 / 快手 / Twitch / X / Facebook，每行一个）", bg=T["panel"], fg=T["muted"], font=("Microsoft YaHei UI", 9, "bold")).pack(side="left")
        btns = tk.Frame(top, bg=T["panel"]); btns.pack(side="right")
        ttk.Button(btns, text="粘贴", command=self.paste_urls).pack(side="left", padx=3)
        ttk.Button(btns, text="清空URL", command=lambda: self.url_text.delete("1.0", "end")).pack(side="left", padx=3)
        ttk.Button(btns, text="🔍 解析", command=self.start_parse).pack(side="left", padx=3)
        self.url_text = tk.Text(p, height=4, bg=T["card"], fg=T["text"], insertbackground=T["text"], relief="flat", wrap="none", font=("Consolas", 10), selectbackground=T["accent"])
        self.url_text.pack(fill="x", padx=10, pady=(0,10), ipady=5, ipadx=6)

    def _build_filter_bar(self, parent):
        box = tk.Frame(parent, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        box.pack(fill="x", pady=(0,8))
        p = tk.Frame(box, bg=T["panel"]); p.pack(fill="x")
        for txt, cmd in [("☑ 全选当前筛选", self.select_all), ("☐ 全不选当前筛选", self.deselect_all), ("⇅ 反选当前筛选", self.invert_select), ("🗑 清空待下载", self.clear_pending)]:
            tk.Button(p, text=txt, command=cmd, bg=T["card"], fg=T["text"], relief="flat", padx=10, pady=6, cursor="hand2").pack(side="left", padx=4, pady=8)
        tk.Label(p, text="排序：", bg=T["panel"], fg=T["muted"]).pack(side="left", padx=(18,2))
        self.sort_var = tk.StringVar(value="添加顺序")
        ttk.Combobox(p, textvariable=self.sort_var, values=SORT_OPTIONS, width=14, state="readonly").pack(side="left", padx=3)
        tk.Label(p, text="分类/格式：", bg=T["panel"], fg=T["muted"]).pack(side="left", padx=(14,2))
        self.filter_var = tk.StringVar(value="全部")
        ttk.Combobox(p, textvariable=self.filter_var, values=FILTER_OPTIONS, width=12, state="readonly").pack(side="left", padx=3)
        self.search_var = tk.StringVar()
        tk.Entry(p, textvariable=self.search_var, bg=T["card"], fg=T["text"], relief="flat", width=24, insertbackground=T["text"]).pack(side="left", padx=8, ipady=5)
        ttk.Button(p, text="应用筛选", command=self.refresh_all_views).pack(side="left", padx=3)

        src = tk.Frame(box, bg=T["panel"]); src.pack(fill="x", padx=6, pady=(0,8))
        tk.Label(src, text="源筛选：", bg=T["panel"], fg=T["muted"], font=("Microsoft YaHei UI", 9, "bold")).pack(side="left", padx=(2,6))
        self.platform_all_var = tk.BooleanVar(value=True)
        tk.Checkbutton(src, text="全部", variable=self.platform_all_var, command=self.toggle_all_platforms,
                       bg=T["panel"], fg=T["text"], selectcolor=T["card"], activebackground=T["panel"], activeforeground=T["text"]).pack(side="left", padx=2)
        self.platform_filter_vars = {}
        for name in PLATFORM_FILTERS:
            v = tk.BooleanVar(value=True)
            self.platform_filter_vars[name] = v
            cb = tk.Checkbutton(src, text=name, variable=v, command=self.on_platform_filter_changed,
                                bg=T["panel"], fg=T["text"], selectcolor=T["card"], activebackground=T["panel"], activeforeground=T["text"])
            cb.pack(side="left", padx=2)
        ttk.Button(src, text="只看抖音", command=lambda: self.only_platform("抖音")).pack(side="left", padx=(8,2))
        ttk.Button(src, text="只看 YouTube", command=lambda: self.only_platform("YouTube")).pack(side="left", padx=2)
        ttk.Button(src, text="只看 B站", command=lambda: self.only_platform("Bilibili")).pack(side="left", padx=2)

        self.sort_var.trace_add("write", lambda *_: self.refresh_all_views())
        self.filter_var.trace_add("write", lambda *_: self.refresh_all_views())
        self.search_var.trace_add("write", lambda *_: self.refresh_all_views())

    def _build_notebook(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill="both", expand=True)
        self.tabs = {}
        for key, name in [("pending", "待下载"), ("running", "任务中"), ("completed", "已完成"), ("settings", "下载设置"), ("themes", "主题皮肤")]:
            f = tk.Frame(self.nb, bg=T["bg"])
            self.nb.add(f, text=name)
            self.tabs[key] = f
        self.pending_tree = self.make_tree(self.tabs["pending"], "pending")
        self.running_tree = self.make_tree(self.tabs["running"], "running")
        self.completed_tree = self.make_tree(self.tabs["completed"], "completed")
        self._build_settings_tab(self.tabs["settings"])
        self._build_theme_tab(self.tabs["themes"])

    def make_tree(self, parent, key):
        cols = ("check", "id", "title", "site", "format", "type", "duration", "size", "progress", "speed", "eta", "elapsed", "status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        names = {"check":"选", "id":"#", "title":"标题", "site":"站点", "format":"格式", "type":"分类", "duration":"时长", "size":"大小", "progress":"进度", "speed":"速度", "eta":"剩余", "elapsed":"已用", "status":"状态"}
        widths = {"check":44, "id":48, "title":430, "site":86, "format":70, "type":64, "duration":80, "size":95, "progress":80, "speed":110, "eta":90, "elapsed":90, "status":90}
        for c in cols:
            tree.heading(c, text=names[c])
            tree.column(c, width=widths[c], minwidth=40, anchor="w")
        tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=sb.set)
        tree.bind("<Double-1>", lambda e, k=key: self.open_selected_detail(k))
        tree.bind("<Button-1>", lambda e, k=key: self.on_tree_click(e, k))
        menu = tk.Menu(tree, tearoff=0, bg=T["card"], fg=T["text"])
        menu.add_command(label="查看详情", command=lambda k=key: self.open_selected_detail(k))
        if key in ("pending", "running"):
            menu.add_command(label="暂停任务", command=self.pause_selected)
            menu.add_command(label="继续任务", command=self.resume_selected)
            menu.add_command(label="取消任务", command=self.cancel_selected)
        if key == "completed":
            menu.add_command(label="打开输出目录", command=self.open_selected_output)
        tree.bind("<Button-3>", lambda e, m=menu: m.tk_popup(e.x_root, e.y_root))
        return tree

    def _build_theme_tab(self, parent):
        wrap = tk.Frame(parent, bg=T["bg"])
        wrap.pack(fill="both", expand=True, padx=12, pady=12)
        top = tk.Frame(wrap, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        top.pack(fill="x", pady=(0,10))
        tk.Label(top, text="🎨 主题皮肤中心", bg=T["panel"], fg=T["text"], font=("Microsoft YaHei UI", 15, "bold")).pack(side="left", padx=14, pady=12)
        tk.Label(top, text="Ctrl+Tab / F8 下一套；Ctrl+Shift+Tab / F7 上一套；无需重启", bg=T["panel"], fg=T["muted"], font=("Microsoft YaHei UI", 10)).pack(side="left", padx=12)
        ttk.Button(top, text="◀ 上一套", command=self.prev_theme).pack(side="right", padx=6)
        ttk.Button(top, text="下一套 ▶", command=self.next_theme).pack(side="right", padx=6)

        canvas = tk.Canvas(wrap, bg=T["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        grid = tk.Frame(canvas, bg=T["bg"])
        win = canvas.create_window((0,0), window=grid, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        grid.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        for idx, (name, th) in enumerate(THEMES.items()):
            card = tk.Frame(grid, bg=th["panel"], highlightthickness=2, highlightbackground=th["accent"], cursor="hand2")
            card.grid(row=idx//3, column=idx%3, sticky="nsew", padx=8, pady=8)
            grid.grid_columnconfigure(idx%3, weight=1)
            tk.Label(card, text=name, bg=th["panel"], fg=th["text"], font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", padx=12, pady=(10,6))
            sample = tk.Frame(card, bg=th["card"]); sample.pack(fill="x", padx=12, pady=(0,8))
            for c in ["accent", "success", "warning", "blue", "purple", "pink"]:
                tk.Frame(sample, bg=th[c], width=34, height=18).pack(side="left", padx=3, pady=8)
            tk.Label(card, text="点击立即应用", bg=th["panel"], fg=th["muted"], font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=12, pady=(0,10))
            for w in (card,):
                w.bind("<Button-1>", lambda e, n=name: self.apply_theme(n, rebuild=True))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, n=name: self.apply_theme(n, rebuild=True))

    def _build_settings_tab(self, parent):
        """下载设置页：v3.10 改为可滚动 + 底部固定按钮栏。
        解决小窗口/低分辨率下右侧设置和“保存设置”按钮被挤出屏幕的问题。
        """
        root = tk.Frame(parent, bg=T["bg"])
        root.pack(fill="both", expand=True)

        # 顶部提示条，始终可见
        tip = tk.Frame(root, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        tip.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(
            tip,
            text="⚙ 下载设置中心  ·  鼠标滚轮可上下滚动  ·  Ctrl+S 保存设置  ·  按钮固定在底部不再丢失",
            bg=T["panel"], fg=T["text"], font=("Microsoft YaHei UI", 10, "bold")
        ).pack(side="left", padx=12, pady=8)

        # 中间滚动区
        body = tk.Frame(root, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        canvas = tk.Canvas(body, bg=T["bg"], highlightthickness=0)
        vbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        hbar = ttk.Scrollbar(body, orient="horizontal", command=canvas.xview)
        scroll_frame = tk.Frame(canvas, bg=T["bg"])
        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        def _sync_scroll_region(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 宽屏时让内容区自动撑满；窄屏时保留横向滚动条
            try:
                canvas_width = canvas.winfo_width()
                required_width = max(scroll_frame.winfo_reqwidth(), canvas_width)
                canvas.itemconfigure(window_id, width=required_width)
            except Exception:
                pass

        scroll_frame.bind("<Configure>", _sync_scroll_region)
        canvas.bind("<Configure>", _sync_scroll_region)

        def _wheel(e):
            # Windows / macOS 鼠标滚轮
            delta = -1 * int(e.delta / 120) if getattr(e, "delta", 0) else 0
            if delta:
                canvas.yview_scroll(delta, "units")

        def _wheel_linux_up(_):
            canvas.yview_scroll(-3, "units")

        def _wheel_linux_down(_):
            canvas.yview_scroll(3, "units")

        for widget in (canvas, scroll_frame):
            widget.bind("<MouseWheel>", _wheel)
            widget.bind("<Button-4>", _wheel_linux_up)
            widget.bind("<Button-5>", _wheel_linux_down)

        columns = tk.Frame(scroll_frame, bg=T["bg"])
        columns.pack(fill="both", expand=True)
        columns.grid_columnconfigure(0, weight=1, uniform="settings_cols")
        columns.grid_columnconfigure(1, weight=1, uniform="settings_cols")

        left = tk.Frame(columns, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        right = tk.Frame(columns, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        self.setting_vars = {}

        def row(parent, label, varname, widget="entry", values=None, width=34):
            r = tk.Frame(parent, bg=T["panel"])
            r.pack(fill="x", padx=14, pady=6)
            tk.Label(r, text=label, bg=T["panel"], fg=T["muted"], width=16, anchor="e").pack(side="left", padx=(0, 8))
            val = getattr(self.settings, varname)
            v = tk.BooleanVar(value=val) if isinstance(val, bool) else tk.StringVar(value=str(val))
            self.setting_vars[varname] = v
            if widget == "combo":
                w = ttk.Combobox(r, textvariable=v, values=values, width=width, state="readonly")
                w.pack(side="left", fill="x", expand=True)
            elif widget == "check":
                w = tk.Checkbutton(r, variable=v, bg=T["panel"], fg=T["text"], selectcolor=T["card"], activebackground=T["panel"], activeforeground=T["text"])
                w.pack(side="left")
            else:
                w = tk.Entry(r, textvariable=v, bg=T["card"], fg=T["text"], relief="flat", insertbackground=T["text"])
                w.pack(side="left", fill="x", expand=True, ipady=5)
            # 让鼠标在输入框/下拉框上滚动时也能滚动页面
            try:
                w.bind("<MouseWheel>", _wheel, add="+")
                w.bind("<Button-4>", _wheel_linux_up, add="+")
                w.bind("<Button-5>", _wheel_linux_down, add="+")
            except Exception:
                pass
            return v

        tk.Label(left, text="基础下载设置", bg=T["panel"], fg=T["cyan"], font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        row(left, "皮肤主题", "theme_name", "combo", list(THEMES.keys()))
        ttk.Button(left, text="应用皮肤", command=lambda: self.apply_theme(self.setting_vars["theme_name"].get(), rebuild=True)).pack(anchor="e", padx=14, pady=(0, 4))
        row(left, "速度配置", "speed_profile", "combo", list(SPEED_PROFILES.keys()))
        ttk.Button(left, text="🚀 应用极速推荐配置", command=lambda: self.apply_speed_profile(self.setting_vars["speed_profile"].get())).pack(anchor="e", padx=14, pady=(0, 8))
        row(left, "保存目录", "output_dir")
        ttk.Button(left, text="选择保存目录", command=self.choose_output_dir).pack(anchor="e", padx=14, pady=(0, 8))
        row(left, "画质", "quality_label", "combo", list(QUALITY_OPTIONS.keys()))
        row(left, "输出格式", "format_label", "combo", list(FORMAT_OPTIONS.keys()))
        row(left, "分片并发", "concurrent_fragments")
        row(left, "同时任务数", "max_concurrent_tasks")
        row(left, "失败重试", "retries")
        row(left, "分片重试", "fragment_retries")
        row(left, "HTTP chunk(MB)", "http_chunk_size_mb")
        row(left, "超时秒数", "socket_timeout")
        row(left, "缓冲KB", "buffersize_kb")
        row(left, "限速重连阈值", "throttled_rate_limit")
        row(left, "YouTube客户端", "youtube_client")
        row(left, "主动限速", "rate_limit")
        tk.Label(
            left,
            text="主动限速例：2M / 500K；为空不限速。低速重连阈值建议 1M。",
            bg=T["panel"], fg=T["muted"], justify="left", wraplength=560
        ).pack(anchor="w", padx=32, pady=(0, 14))

        tk.Label(right, text="附加下载设置", bg=T["panel"], fg=T["purple"], font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=14, pady=(14, 8))
        for label, name in [
            ("跳过直播/回放", "skip_live_content"),
            ("下载人工字幕", "write_subs"),
            ("下载自动字幕", "write_auto_subs"),
            ("嵌入字幕", "embed_subs"),
            ("下载缩略图", "write_thumbnail"),
            ("下载简介文件", "write_description"),
            ("限制安全文件名", "restrict_filenames"),
            ("断点续传", "continue_download"),
            ("不覆盖已有文件", "no_overwrites"),
            ("抖音自动尝试浏览器Cookie", "auto_cookie_fallback"),
        ]:
            row(right, label, name, "check")
        row(right, "字幕语言", "sub_langs")
        row(right, "浏览器Cookie", "cookies_from_browser")
        row(right, "浏览器Profile", "browser_profile")
        row(right, "cookies.txt", "cookie_file")
        row(right, "解析超时秒数", "parse_timeout")
        row(right, "强制 IPv4", "force_ipv4", "check")
        tk.Label(
            right,
            text="Cookie 可填 chrome / edge / firefox；Profile 可填 Default / Profile 1。cookies.txt 优先级高于浏览器 Cookie。抖音 Fresh cookies 要先用浏览器打开 douyin.com 并播放一次。",
            bg=T["panel"], fg=T["muted"], wraplength=560, justify="left"
        ).pack(anchor="w", padx=32, pady=(0, 10))
        cookie_tools = tk.Frame(right, bg=T["panel"])
        cookie_tools.pack(fill="x", padx=32, pady=(0, 18))
        ttk.Button(cookie_tools, text="选择 cookies.txt", command=self.choose_cookie_file).pack(side="left", padx=3)
        ttk.Button(cookie_tools, text="Cookie诊断", command=self.cookie_diagnose).pack(side="left", padx=3)

        # 底部固定按钮栏，不参与滚动，低分辨率也能点到
        fixed = tk.Frame(root, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        fixed.pack(fill="x", side="bottom", padx=12, pady=(0, 12))
        tk.Label(fixed, text="设置修改后点右侧保存；也可按 Ctrl+S。", bg=T["panel"], fg=T["muted"]).pack(side="left", padx=12, pady=10)
        ttk.Button(fixed, text="保存设置", command=self.save_settings_from_ui).pack(side="right", padx=(4, 12), pady=8)
        ttk.Button(fixed, text="恢复默认", command=self.reset_settings).pack(side="right", padx=4, pady=8)
        ttk.Button(fixed, text="Cookie诊断", command=self.cookie_diagnose).pack(side="right", padx=4, pady=8)
        ttk.Button(fixed, text="选择 cookies.txt", command=self.choose_cookie_file).pack(side="right", padx=4, pady=8)

        # 绑定保存快捷键
        self.bind_all("<Control-s>", lambda e: (self.save_settings_from_ui(), "break"))
        self.bind_all("<Control-S>", lambda e: (self.save_settings_from_ui(), "break"))

    def _build_bottom_controls(self, parent):
        p = tk.Frame(parent, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        p.pack(fill="x", pady=(8,0))
        tk.Button(p, text="⬇ 开始下载选中任务", bg=T["success"], fg="#07110A", relief="flat", padx=18, pady=9, font=("Microsoft YaHei UI", 11, "bold"), command=self.start_download).pack(side="left", padx=8, pady=8)
        for txt, cmd, color in [("⏸ 全部暂停", self.pause_all, T["warning"]), ("▶ 全部继续", self.resume_all, T["blue"]), ("⏹ 全部取消", self.cancel_all, T["error"]), ("📂 打开目录", self.open_output_dir, T["purple"] )]:
            tk.Button(p, text=txt, bg=T["card"], fg=color, relief="flat", padx=12, pady=8, command=cmd).pack(side="left", padx=4, pady=8)
        self.total_bar = ttk.Progressbar(p, style="Green.Horizontal.TProgressbar", maximum=100)
        self.total_bar.pack(side="left", fill="x", expand=True, padx=12)
        self.total_pct = tk.Label(p, text="0%", bg=T["panel"], fg=T["success"], font=("Consolas", 12, "bold"))
        self.total_pct.pack(side="left", padx=10)

    def _build_log_panel(self, parent):
        p = tk.Frame(parent, bg=T["panel"], highlightthickness=1, highlightbackground=T["border"])
        p.pack(fill="both", expand=True)
        tk.Label(p, text="📋 实时日志", bg=T["panel"], fg=T["muted"], font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10,4))
        self.log_text = tk.Text(p, bg="#070B14", fg=T["text"], relief="flat", wrap="word", font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0,8))
        for tag, color in [("success", T["success"]), ("error", T["error"]), ("warning", T["warning"]), ("info", T["blue"]), ("muted", T["muted"]), ("purple", T["purple"] )]:
            self.log_text.tag_configure(tag, foreground=color)
        ttk.Button(p, text="清空日志", command=self.clear_log).pack(fill="x", padx=10, pady=(0,10))

    # settings
    def load_settings(self):
        if SETTINGS_PATH.exists():
            try:
                data = json.loads(SETTINGS_PATH.read_text("utf-8"))
                base = asdict(DownloadSettings())
                base.update(data)
                return DownloadSettings(**base)
            except Exception:
                pass
        return DownloadSettings()

    def save_settings(self):
        SETTINGS_PATH.write_text(json.dumps(asdict(self.settings), ensure_ascii=False, indent=2), "utf-8")

    def save_settings_from_ui(self, log_saved=True):
        for k, v in self.setting_vars.items():
            cur = getattr(self.settings, k)
            raw = v.get()
            if isinstance(cur, bool): setattr(self.settings, k, bool(raw))
            elif isinstance(cur, int): setattr(self.settings, k, max(0, safe_int(raw, cur)))
            else: setattr(self.settings, k, str(raw))
        self.settings.concurrent_fragments = max(1, min(32, int(self.settings.concurrent_fragments)))
        self.settings.max_concurrent_tasks = max(1, min(12, int(self.settings.max_concurrent_tasks)))
        self.settings.http_chunk_size_mb = max(1, min(64, int(self.settings.http_chunk_size_mb)))
        self.settings.socket_timeout = max(5, min(120, int(self.settings.socket_timeout)))
        self.settings.parse_timeout = max(30, min(600, int(self.settings.parse_timeout)))
        self.settings.buffersize_kb = max(16, min(2048, int(self.settings.buffersize_kb)))
        if self.settings.theme_name not in THEMES:
            self.settings.theme_name = "极夜霓虹"
        if self.settings.speed_profile not in SPEED_PROFILES:
            self.settings.speed_profile = "极速推荐"
        self.save_settings()
        if log_saved:
            self.log("✅ 下载设置已保存", "success")

    def reset_settings(self):
        self.settings = DownloadSettings()
        self.save_settings()
        messagebox.showinfo("已恢复", "已恢复默认设置，重启后全部控件显示为默认值。")

    def choose_output_dir(self):
        d = filedialog.askdirectory(initialdir=self.setting_vars["output_dir"].get() or str(Path.home()))
        if d:
            self.setting_vars["output_dir"].set(d)

    def choose_cookie_file(self):
        f = filedialog.askopenfilename(
            title="选择 Netscape cookies.txt",
            filetypes=[("Cookie 文件", "*.txt *.cookies"), ("所有文件", "*.*")]
        )
        if f and "cookie_file" in self.setting_vars:
            self.setting_vars["cookie_file"].set(f)

    def cookie_diagnose(self):
        self.save_settings_from_ui(log_saved=False)
        s = self.settings
        self.log("🍪 Cookie 诊断开始", "purple")
        if str(s.cookie_file).strip():
            if Path(str(s.cookie_file)).exists():
                self.log(f"✅ cookies.txt 存在：{s.cookie_file}", "success")
            else:
                self.log(f"❌ cookies.txt 不存在：{s.cookie_file}", "error")
        elif str(s.cookies_from_browser).strip():
            prof = f" / Profile={s.browser_profile}" if str(s.browser_profile).strip() else ""
            self.log(f"✅ 将从浏览器读取 Cookie：{s.cookies_from_browser}{prof}", "success")
            self.log("提示：若浏览器 Cookie 仍报 Fresh cookies，请先用该浏览器打开 douyin.com 并播放目标视频；若 Chrome/Edge 正在运行导致读取失败，关闭浏览器后重试，或导出 cookies.txt。", "warning")
        else:
            self.log("❌ 未配置 Cookie。抖音/X/Facebook/TikTok 很可能解析或下载失败。", "error")
            self.log("建议：下载设置 → 浏览器Cookie 填 chrome 或 edge；或者选择 cookies.txt。", "warning")

    # parsing/task creation
    def paste_urls(self):
        try:
            self.url_text.insert("end", self.clipboard_get().strip() + "\n")
        except Exception:
            pass

    def start_parse(self):
        raw = self.url_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("提示", "请先粘贴 URL。")
            return
        urls = [x.strip() for x in raw.splitlines() if x.strip()]
        self.save_settings_from_ui(log_saved=False)
        w = ParseWorker(urls, lambda info: self.after(0, self.add_task_from_info, info), self.log, self.settings)
        w.start()
        self.log(f"📡 开始解析 {len(urls)} 个链接", "info")
        self.log("🌐 多站点模式：已启用平台专用解析器，不再只用一套 YouTube 解析逻辑。", "purple")

    def build_url(self, info):
        for k in ("webpage_url", "original_url", "url"):
            v = info.get(k, "")
            if isinstance(v, str) and v.startswith("http"):
                return v
        source = info.get("_source_url", "")
        vid = info.get("id", "")
        # flat-playlist 下 YouTube 只有 id，可以安全拼回 watch URL；其他站点尽量交回原 URL 给 yt-dlp 通用解析。
        if vid and detect_platform(source) == "YouTube":
            return f"https://www.youtube.com/watch?v={vid}"
        if source and source.startswith("http") and not vid:
            return source
        return source if source.startswith("http") and detect_platform(source) != "YouTube" else ""

    def add_task_from_info(self, info):
        if self.settings.skip_live_content and is_live_content(info):
            title = info.get("title") or info.get("id") or info.get("webpage_url") or "直播内容"
            status = info.get("live_status") or ("is_live" if info.get("is_live") else "was_live")
            self.log(f"⏭ 已跳过直播类内容：{str(title)[:70]} [{status}]", "warning")
            return
        url = self.build_url(info)
        if not url: return
        for t in self.tasks.values():
            if t.url == url:
                self.log(f"⚠️ 跳过重复：{info.get('title', url)[:60]}", "warning")
                return
        rid = self.next_id; self.next_id += 1
        is_audio = "仅音频" in self.settings.quality_label
        fmt = FORMAT_OPTIONS.get(self.settings.format_label, "mp4") or "raw"
        task = TaskState(
            row_id=rid, url=url, title=info.get("title") or info.get("id") or "未知标题",
            duration=safe_int(info.get("duration"), 0), uploader=info.get("uploader") or info.get("channel") or "",
            source=info.get("_original_input_url") or info.get("_source_url") or url, platform=info.get("_platform_adapter") or detect_platform(info.get("_source_url") or info.get("_original_input_url") or url),
            total_bytes=safe_filesize_from_info(info),
            file_format=("mp3" if "MP3" in self.settings.quality_label else "m4a" if "M4A" in self.settings.quality_label else fmt),
            media_type="音频" if is_audio else "视频",
            is_live_content=is_live_content(info),
        )
        self.tasks[rid] = task
        if info.get("_cookie_required"):
            task.checked = False
            task.status = STATUS_FAILED
            task.error = info.get("_parse_error") or "该任务需要 Cookie 后重新解析。"
            task.progress = 0
            self.log(f"🍪 已加入 Cookie 提示任务：{task.title[:70]}；配置 Cookie 后重新解析即可。", "warning")
        elif info.get("_stub_only"):
            task.error = "抖音元数据兜底任务：解析器未返回标题/大小；下载时建议启用浏览器 Cookie。"
        self.events[rid] = {"pause": threading.Event(), "cancel": threading.Event()}
        self.refresh_all_views()
        self.update_cards()
        self.log(f"＋ 已添加：{task.title[:70]}", "muted")

    # filtering/rendering
    def task_visible(self, t: TaskState, group):
        if group == "pending" and t.status not in (STATUS_PENDING,): return False
        if group == "running" and t.status not in (STATUS_QUEUED, STATUS_RUNNING, STATUS_PAUSED, STATUS_MERGING): return False
        if group == "completed" and t.status not in (STATUS_DONE, STATUS_FAILED, STATUS_CANCELED): return False
        # 源筛选：先选平台源，再做格式/状态/关键词筛选。全选/反选按钮也只作用于当前筛选结果。
        if hasattr(self, "platform_filter_vars") and self.platform_filter_vars:
            enabled = {name for name, var in self.platform_filter_vars.items() if var.get()}
            if enabled and t.platform not in enabled:
                return False
            if not enabled:
                return False
        f = self.filter_var.get()
        if f != "全部":
            if f in ["视频", "音频"] and t.media_type != f: return False
            if f in ["MP4", "MKV", "WebM", "原始"] and t.file_format.lower() != {"MP4":"mp4", "MKV":"mkv", "WebM":"webm", "原始":"raw"}[f]: return False
            if f in [STATUS_PENDING, STATUS_QUEUED, STATUS_RUNNING, STATUS_PAUSED, STATUS_DONE, STATUS_FAILED, STATUS_CANCELED] and t.status != f: return False
        q = self.search_var.get().strip().lower()
        if q and q not in t.title.lower() and q not in t.url.lower() and q not in t.uploader.lower(): return False
        return True

    def on_platform_filter_changed(self):
        if hasattr(self, "platform_all_var"):
            self.platform_all_var.set(all(v.get() for v in self.platform_filter_vars.values()))
        self.refresh_all_views()

    def toggle_all_platforms(self):
        val = bool(self.platform_all_var.get())
        for v in self.platform_filter_vars.values():
            v.set(val)
        self.refresh_all_views()

    def only_platform(self, platform_name):
        if hasattr(self, "platform_all_var"):
            self.platform_all_var.set(False)
        for name, v in self.platform_filter_vars.items():
            v.set(name == platform_name)
        self.refresh_all_views()

    def visible_pending_tasks(self):
        return [t for t in self.tasks.values() if t.status == STATUS_PENDING and self.task_visible(t, "pending")]

    def sorted_tasks(self, tasks):
        s = self.sort_var.get()
        rev = False
        key = lambda t: t.row_id
        if s == "标题 A-Z": key = lambda t: t.title.lower()
        elif s == "标题 Z-A": key = lambda t: t.title.lower(); rev = True
        elif s == "格式": key = lambda t: t.file_format
        elif s == "状态": key = lambda t: t.status
        elif s == "时长短→长": key = lambda t: t.duration
        elif s == "时长长→短": key = lambda t: t.duration; rev = True
        elif s == "进度低→高": key = lambda t: t.progress
        elif s == "进度高→低": key = lambda t: t.progress; rev = True
        elif s == "添加时间新→旧": key = lambda t: t.created_at; rev = True
        return sorted(tasks, key=key, reverse=rev)

    def refresh_all_views(self):
        for key, tree in [("pending", self.pending_tree), ("running", self.running_tree), ("completed", self.completed_tree)]:
            tree.delete(*tree.get_children())
            self.row_refs[key].clear()
            tasks = self.sorted_tasks([t for t in self.tasks.values() if self.task_visible(t, key)])
            for t in tasks:
                iid = str(t.row_id)
                vals = (CHECK_ON if t.checked else CHECK_OFF, t.row_id+1, t.title[:92], t.platform, t.file_format, t.media_type, fmt_time(t.duration) if t.duration else "--", fmt_bytes(t.total_bytes) if t.total_bytes else "--", f"{t.progress:.0f}%", t.speed_text or "--", t.eta_text or "--", fmt_time(t.elapsed_sec), t.status)
                tree.insert("", "end", iid=iid, values=vals)
                self.row_refs[key][t.row_id] = iid
        self.update_cards()

    def update_task_row(self, rid):
        t = self.tasks.get(rid)
        if not t: return
        # status may move between tabs; easiest safe refresh for current row movements
        self.refresh_all_views()

    def on_tree_click(self, event, key):
        tree = {"pending": self.pending_tree, "running": self.running_tree, "completed": self.completed_tree}[key]
        region = tree.identify("region", event.x, event.y)
        col = tree.identify_column(event.x)
        iid = tree.identify_row(event.y)
        if region == "cell" and col == "#1" and iid:
            rid = int(iid)
            if rid in self.tasks and self.tasks[rid].status == STATUS_PENDING:
                self.tasks[rid].checked = not self.tasks[rid].checked
                self.refresh_all_views()

    # download actions
    def selected_rid(self):
        for tree in (self.pending_tree, self.running_tree, self.completed_tree):
            sel = tree.selection()
            if sel:
                return int(sel[0])
        return None

    def start_download(self):
        self.save_settings_from_ui()
        selected = [t for t in self.tasks.values() if t.checked and t.status == STATUS_PENDING]
        if not selected:
            messagebox.showwarning("未选择", "请至少选择一个待下载任务。")
            return
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        self.global_cancel.clear(); self.global_pause.clear()
        for t in selected:
            self.events[t.row_id]["cancel"].clear(); self.events[t.row_id]["pause"].clear()
            t.status = STATUS_QUEUED; t.progress = 0; t.error = ""; t.speed_text = ""; t.eta_text = "--"
        self.total_start_at = time.time()
        self.worker = DownloadWorker(selected, self.settings, self.events, self.on_progress_threadsafe, self.on_done_threadsafe, self.log, self.global_cancel, self.global_pause)
        self.worker.start()
        self.refresh_all_views()
        self.nb.select(self.tabs["running"])
        self.log(f"🚀 启动下载：{len(selected)} 个任务 | 配置={self.settings.speed_profile} | 同时任务×{self.settings.max_concurrent_tasks} | 分片×{self.settings.concurrent_fragments} | chunk={self.settings.http_chunk_size_mb}MB", "info")
        self.log("⚡ 提速提示：若单个视频低于 2MB/s，优先试‘单任务满速’；若多个短视频，试‘极速推荐/极限压榨’。", "purple")

    def on_progress_threadsafe(self, rid, data):
        self.after(0, self.apply_progress, rid, data)

    def apply_progress(self, rid, data):
        t = self.tasks.get(rid)
        if not t: return
        for k, v in data.items():
            if hasattr(t, k): setattr(t, k, v)
        if t.started_at:
            t.elapsed_sec = int(time.time() - t.started_at)
        self.update_cards()
        self.update_task_row(rid)

    def on_done_threadsafe(self, rid, success, status, error):
        self.after(0, self.apply_done, rid, success, status, error)

    def apply_done(self, rid, success, status, error):
        t = self.tasks.get(rid)
        if not t: return
        t.status = status
        t.finished_at = time.time()
        if t.started_at: t.elapsed_sec = int(t.finished_at - t.started_at)
        if success:
            t.progress = 100
            t.speed_bps = 0
            t.speed_text = "--"
            t.eta_text = "0:00"
        else:
            t.error = error or status
        self.save_completed_db()
        self.refresh_all_views()

    def pause_selected(self):
        rid = self.selected_rid()
        if rid is not None and rid in self.events:
            self.events[rid]["pause"].set(); self.tasks[rid].status = STATUS_PAUSED; self.refresh_all_views()

    def resume_selected(self):
        rid = self.selected_rid()
        if rid is not None and rid in self.events:
            self.events[rid]["pause"].clear()
            if self.tasks[rid].status == STATUS_PAUSED: self.tasks[rid].status = STATUS_RUNNING
            self.refresh_all_views()

    def cancel_selected(self):
        rid = self.selected_rid()
        if rid is not None and rid in self.events:
            self.events[rid]["cancel"].set(); self.tasks[rid].status = STATUS_CANCELED; self.refresh_all_views()

    def pause_all(self):
        self.global_pause.set()
        for t in self.tasks.values():
            if t.status in (STATUS_QUEUED, STATUS_RUNNING, STATUS_MERGING): t.status = STATUS_PAUSED
        self.refresh_all_views(); self.log("⏸ 已暂停全部任务", "warning")

    def resume_all(self):
        self.global_pause.clear()
        for ev in self.events.values(): ev["pause"].clear()
        for t in self.tasks.values():
            if t.status == STATUS_PAUSED: t.status = STATUS_RUNNING
        self.refresh_all_views(); self.log("▶ 已继续全部任务", "info")

    def cancel_all(self):
        self.global_cancel.set()
        for ev in self.events.values(): ev["cancel"].set()
        for t in self.tasks.values():
            if t.status in (STATUS_PENDING, STATUS_QUEUED, STATUS_RUNNING, STATUS_PAUSED, STATUS_MERGING): t.status = STATUS_CANCELED
        self.refresh_all_views(); self.log("⏹ 已取消全部任务", "warning")

    # selection/list ops
    def select_all(self):
        count = 0
        for t in self.visible_pending_tasks():
            t.checked = True; count += 1
        self.refresh_all_views(); self.log(f"☑ 已全选当前筛选结果：{count} 个待下载任务", "info")
    def deselect_all(self):
        count = 0
        for t in self.visible_pending_tasks():
            t.checked = False; count += 1
        self.refresh_all_views(); self.log(f"☐ 已取消当前筛选结果：{count} 个待下载任务", "info")
    def invert_select(self):
        count = 0
        for t in self.visible_pending_tasks():
            t.checked = not t.checked; count += 1
        self.refresh_all_views(); self.log(f"⇅ 已反选当前筛选结果：{count} 个待下载任务", "info")
    def clear_pending(self):
        for rid in [rid for rid,t in self.tasks.items() if t.status == STATUS_PENDING]:
            self.tasks.pop(rid, None); self.events.pop(rid, None)
        self.refresh_all_views()

    # detail/open
    def open_selected_detail(self, key=None):
        rid = self.selected_rid()
        if rid is not None and rid in self.tasks:
            DetailsDialog(self, self.tasks[rid])
    def open_output_dir(self):
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        self.open_path(self.settings.output_dir)
    def open_selected_output(self):
        rid = self.selected_rid()
        if rid is not None and rid in self.tasks:
            p = self.tasks[rid].output_path or self.settings.output_dir
            self.open_path(str(Path(p).parent if Path(p).suffix else Path(p)))
    def open_path(self, p):
        try:
            if sys.platform == "win32": os.startfile(p)
            elif sys.platform == "darwin": subprocess.Popen(["open", p])
            else: subprocess.Popen(["xdg-open", p])
        except Exception as e:
            messagebox.showerror("无法打开", str(e))

    # stats/log/db
    def update_cards(self):
        total = len(self.tasks)
        running = sum(1 for t in self.tasks.values() if t.status in (STATUS_QUEUED, STATUS_RUNNING, STATUS_PAUSED, STATUS_MERGING))
        done = sum(1 for t in self.tasks.values() if t.status == STATUS_DONE)
        speed = sum(t.speed_bps for t in self.tasks.values() if t.status == STATUS_RUNNING)
        running_etas = [t.eta_sec for t in self.tasks.values() if t.status == STATUS_RUNNING and t.eta_sec and t.eta_sec > 0]
        eta = max(running_etas) if running_etas else -1
        elapsed = int(time.time() - self.total_start_at) if self.total_start_at else 0
        avg_progress = sum(t.progress for t in self.tasks.values()) / total if total else 0
        self.cards["total"].config(text=str(total))
        self.cards["running"].config(text=str(running))
        self.cards["done"].config(text=str(done))
        self.cards["speed"].config(text=fmt_speed(speed) or "0")
        self.cards["eta"].config(text=fmt_time(eta) if eta > 0 else "--")
        self.cards["elapsed"].config(text=fmt_time(elapsed))
        self.total_bar["value"] = avg_progress
        self.total_pct.config(text=f"{avg_progress:.0f}%")

    def tick(self):
        changed = False
        for t in self.tasks.values():
            if t.started_at and t.status in (STATUS_RUNNING, STATUS_PAUSED, STATUS_MERGING):
                t.elapsed_sec = int(time.time() - t.started_at); changed = True
        if changed: self.refresh_all_views()
        else: self.update_cards()
        self.after(1000, self.tick)

    def log(self, msg, tag=""):
        self.log_queue.put((f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n", tag))

    def process_logs(self):
        while not self.log_queue.empty():
            msg, tag = self.log_queue.get_nowait()
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg, tag if tag else None)
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.after(150, self.process_logs)

    def clear_log(self):
        self.log_text.config(state="normal"); self.log_text.delete("1.0", "end"); self.log_text.config(state="disabled")

    def save_completed_db(self):
        data = [asdict(t) for t in self.tasks.values() if t.status in (STATUS_DONE, STATUS_FAILED, STATUS_CANCELED)]
        try: COMPLETED_DB.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        except Exception: pass

    def load_completed_db(self):
        if not COMPLETED_DB.exists(): return
        try:
            data = json.loads(COMPLETED_DB.read_text("utf-8"))
            for item in data[-500:]:
                rid = self.next_id; self.next_id += 1
                item["row_id"] = rid
                t = TaskState(**{**asdict(TaskState(row_id=rid, url="")), **item})
                self.tasks[rid] = t
                self.events[rid] = {"pause": threading.Event(), "cancel": threading.Event()}
            self.refresh_all_views()
        except Exception:
            pass

    def check_startup(self):
        found = check_ytdlp()
        if found:
            ver, cmdline = get_ytdlp_version()
            self.badge.config(text=f"yt-dlp {ver or found} ✓", fg=T["success"])
            self.log(f"✅ yt-dlp {ver or found} 已就绪", "success")
            self.log(f"🧭 yt-dlp 调用路径：{cmdline}", "muted")
            self.log(f"🚀 当前速度配置：{self.settings.speed_profile} | 同时任务×{self.settings.max_concurrent_tasks} | 分片×{self.settings.concurrent_fragments} | chunk={self.settings.http_chunk_size_mb}MB", "info")
        else:
            self.badge.config(text="未检测到 yt-dlp", fg=T["error"])
            self.log("❌ 未检测到 yt-dlp：请运行 pip install yt-dlp", "error")
            messagebox.showwarning("缺少依赖", "未检测到 yt-dlp。\n请运行：pip install yt-dlp")


if __name__ == "__main__":
    app = App()
    app.mainloop()

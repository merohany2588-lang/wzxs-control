"""
磁盘空间深度分析与安全清理工具 v2.0
Disk Space Deep Analyzer & Safe Cleaner
安全第一 | Safety First

新增功能 (v2.0):
  ✅ 深度清理标签页（14 个新清理类别）
  ✅ 三级风险分类：安全 / 中等 / 谨慎
  ✅ 更多浏览器缓存（Firefox / Brave / Opera）
  ✅ 开发工具缓存（npm / pip / Yarn / Maven / Gradle）
  ✅ DISM 组件存储清理
  ✅ 休眠文件管理
  ✅ 大文件搜索新增"文件年龄"过滤
  ✅ Windows.old / 系统转储 / IIS 日志等高级清理项
"""

import os
import sys
import shutil
import threading
import subprocess
import tempfile
import winreg
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes

# ─── 安全检查 ────────────────────────────────────────────────────────────────
PROTECTED_PATHS = {
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Users\\Default",
    "C:\\ProgramData\\Microsoft",
    "C:\\System Volume Information",
    "C:\\$Recycle.Bin",
    "C:\\Recovery",
    "C:\\Boot",
}

def is_safe_to_delete(path: str) -> bool:
    """三重安全检查，防止误删系统文件"""
    p = Path(path).resolve()
    p_str = str(p).upper()
    for protected in PROTECTED_PATHS:
        if p_str == protected.upper() or p_str.startswith(protected.upper() + "\\"):
            return False
    if len(str(p)) <= 3:
        return False
    return True

def format_size(bytes_val: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"

def get_folder_size(path: str) -> int:
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_folder_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

# ─── 标准清理目标 ─────────────────────────────────────────────────────────────
CLEAN_TARGETS = {
    "Windows 临时文件": {
        "paths": [tempfile.gettempdir(), "C:\\Windows\\Temp"],
        "description": "系统和用户临时文件夹，安全可删",
        "color": "#4CAF50",
        "safe": True,
    },
    "Windows Update 缓存": {
        "paths": ["C:\\Windows\\SoftwareDistribution\\Download"],
        "description": "Windows 更新下载缓存，清理后可重新下载",
        "color": "#2196F3",
        "safe": True,
    },
    "预读取文件 (Prefetch)": {
        "paths": ["C:\\Windows\\Prefetch"],
        "description": "应用程序预读文件，删除后会自动重建",
        "color": "#9C27B0",
        "safe": True,
    },
    "缩略图缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Explorer")
        ],
        "description": "文件夹图标缩略图缓存，删除后自动重建",
        "color": "#FF9800",
        "safe": True,
    },
    "Chrome 缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache"),
        ],
        "description": "Chrome 浏览器缓存文件",
        "color": "#F44336",
        "safe": True,
    },
    "Edge 缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache"),
        ],
        "description": "Edge 浏览器缓存文件",
        "color": "#00BCD4",
        "safe": True,
    },
    "Firefox 缓存": {
        "paths": [os.path.expandvars(r"%LOCALAPPDATA%\Mozilla\Firefox\Profiles")],
        "subdirs": ["cache2", "startupCache"],
        "description": "Firefox 浏览器缓存，删除后自动重建",
        "color": "#FF6D00",
        "safe": True,
    },
    "Brave 缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Code Cache"),
        ],
        "description": "Brave 浏览器缓存文件",
        "color": "#FF6D00",
        "safe": True,
    },
    "Opera 缓存": {
        "paths": [
            os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable\Cache"),
        ],
        "description": "Opera 浏览器缓存文件",
        "color": "#FF6D00",
        "safe": True,
    },
    "回收站": {
        "paths": ["RECYCLE_BIN"],
        "description": "清空回收站中所有文件",
        "color": "#607D8B",
        "safe": True,
    },
    "错误报告文件": {
        "paths": [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\WER\ReportQueue"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\WER"),
            "C:\\ProgramData\\Microsoft\\Windows\\WER\\ReportQueue",
        ],
        "description": "Windows 错误报告，可安全删除",
        "color": "#795548",
        "safe": True,
    },
    "日志文件": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\CrashDumps"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Recent"),
        ],
        "description": "崩溃转储和最近访问记录",
        "color": "#FF5722",
        "safe": True,
    },
    "Delivery Optimization 缓存": {
        "paths": ["C:\\Windows\\SoftwareDistribution\\DeliveryOptimization"],
        "description": "Windows 点对点更新传输缓存",
        "color": "#2196F3",
        "safe": True,
    },
    "Microsoft Store 缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.WindowsStore_8wekyb3d8bbwe\LocalCache"),
        ],
        "description": "Microsoft Store 下载缓存",
        "color": "#00B4D8",
        "safe": True,
    },
    "DirectX Shader 缓存": {
        "paths": [os.path.expandvars(r"%LOCALAPPDATA%\D3DSCache")],
        "description": "显卡着色器编译缓存，删除后自动重建",
        "color": "#7B2FBE",
        "safe": True,
    },
    "Windows Defender 历史": {
        "paths": [r"C:\ProgramData\Microsoft\Windows Defender\Scans\History"],
        "description": "Windows Defender 扫描历史记录",
        "color": "#00695C",
        "safe": True,
    },
}

# ─── 深度清理目标（带风险等级） ───────────────────────────────────────────────
# risk: "safe"(绿) / "moderate"(橙) / "caution"(红)
DEEP_CLEAN_TARGETS = {
    # ── 安全级 ────────────────────────────────────────────────────────────────
    "npm 缓存": {
        "paths": [os.path.expandvars(r"%APPDATA%\npm-cache")],
        "description": "Node.js npm 包管理器缓存，删除后重新 install 会重建",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "pip 缓存": {
        "paths": [os.path.expandvars(r"%LOCALAPPDATA%\pip\Cache")],
        "description": "Python pip 包管理器缓存，删除后重新 install 会重建",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "Yarn 缓存": {
        "paths": [os.path.expandvars(r"%LOCALAPPDATA%\Yarn\Cache")],
        "description": "Yarn 包管理器缓存",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "Maven 仓库缓存": {
        "paths": [os.path.join(os.path.expanduser("~"), ".m2", "repository")],
        "description": "Maven Java 依赖本地仓库，删除后会从远程重新下载",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "Gradle 构建缓存": {
        "paths": [os.path.join(os.path.expanduser("~"), ".gradle", "caches")],
        "description": "Gradle 构建工具缓存",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "Visual Studio 组件缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\VisualStudio"),
        ],
        "subdirs": ["ComponentModelCache"],
        "description": "VS 组件模型缓存，删后首次启动 VS 稍慢",
        "risk": "safe",
        "color": "#4CAF50",
    },
    "字体缓存": {
        "paths": [
            r"C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache",
        ],
        "description": "字体渲染缓存，删除后系统自动重建（需管理员）",
        "risk": "safe",
        "color": "#4CAF50",
        "requires_admin": True,
    },
    "Steam 下载缓存": {
        "paths": [
            os.path.expandvars(r"%LOCALAPPDATA%\Steam\htmlcache"),
            r"C:\Program Files (x86)\Steam\appcache",
        ],
        "description": "Steam 客户端 HTML 缓存和应用缓存",
        "risk": "safe",
        "color": "#4CAF50",
    },
    # ── 中等风险级 ────────────────────────────────────────────────────────────
    "系统崩溃转储": {
        "paths": [
            r"C:\Windows\Minidump",
            r"C:\Windows\memory.dmp",
        ],
        "description": "蓝屏崩溃转储文件，如不需诊断可安全删除",
        "risk": "moderate",
        "color": "#FF9800",
    },
    "IIS 日志文件": {
        "paths": [r"C:\inetpub\logs\LogFiles"],
        "description": "IIS Web 服务器运行日志，仅在不需追溯时删除",
        "risk": "moderate",
        "color": "#FF9800",
    },
    "Windows 系统事件日志": {
        "paths": [r"C:\Windows\System32\winevt\Logs"],
        "description": "系统/应用事件日志，删除后无法追溯历史错误（需管理员）",
        "risk": "moderate",
        "color": "#FF9800",
        "requires_admin": True,
    },
    # ── 谨慎级 ────────────────────────────────────────────────────────────────
    "Windows.old（旧系统残留）": {
        "paths": [r"C:\Windows.old"],
        "description": "⚠️ Windows 升级保留的旧系统，删除后无法回滚到上一版本！",
        "risk": "caution",
        "color": "#F44336",
    },
    "旧版系统组件存储": {
        "paths": [],              # 通过 DISM 命令处理，不直接删路径
        "dism_action": True,
        "description": "⚠️ 通过 DISM 清理 WinSxS 冗余组件，操作时间较长（需管理员）",
        "risk": "caution",
        "color": "#F44336",
        "requires_admin": True,
    },
}

# ─── 主题颜色 ─────────────────────────────────────────────────────────────────
THEME = {
    "bg_dark":    "#0D1117",
    "bg_card":    "#161B22",
    "bg_hover":   "#1C2128",
    "border":     "#30363D",
    "text_main":  "#E6EDF3",
    "text_muted": "#8B949E",
    "accent":     "#58A6FF",
    "danger":     "#F85149",
    "success":    "#3FB950",
    "warning":    "#D29922",
    "purple":     "#BC8CFF",
    "bar_used":   "#F85149",
    "bar_free":   "#3FB950",
}

RISK_COLORS = {
    "safe":     "#3FB950",
    "moderate": "#D29922",
    "caution":  "#F85149",
}
RISK_LABELS = {
    "safe":     "安全",
    "moderate": "中等",
    "caution":  "谨慎",
}
RISK_ICONS = {
    "safe":     "✅",
    "moderate": "⚠️",
    "caution":  "🔴",
}


# ─── 主应用 ───────────────────────────────────────────────────────────────────
class DiskCleanerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🛡️  磁盘空间深度分析与安全清理工具 v2.0")
        self.geometry("1160x800")
        self.minsize(960, 640)
        self.configure(bg=THEME["bg_dark"])
        self._setup_style()
        self._build_ui()
        self.after(300, self._auto_scan)

    # ── 样式 ──────────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        bg, card, text, accent = (
            THEME["bg_dark"], THEME["bg_card"],
            THEME["text_main"], THEME["accent"],
        )
        s.configure(".", background=bg, foreground=text,
                     fieldbackground=card, bordercolor=THEME["border"],
                     troughcolor=card, selectbackground=accent,
                     selectforeground=bg, font=("Microsoft YaHei UI", 10))
        s.configure("TFrame", background=bg)
        s.configure("Card.TFrame", background=card, relief="flat", borderwidth=1)
        s.configure("TLabel", background=bg, foreground=text,
                     font=("Microsoft YaHei UI", 10))
        s.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"),
                     foreground=text)
        s.configure("Sub.TLabel", font=("Microsoft YaHei UI", 11),
                     foreground=THEME["text_muted"])
        s.configure("Accent.TLabel", foreground=accent,
                     font=("Microsoft YaHei UI", 10, "bold"))
        s.configure("Success.TLabel", foreground=THEME["success"],
                     font=("Microsoft YaHei UI", 10, "bold"))
        s.configure("Danger.TLabel", foreground=THEME["danger"],
                     font=("Microsoft YaHei UI", 10, "bold"))
        s.configure("Warning.TLabel", foreground=THEME["warning"],
                     font=("Microsoft YaHei UI", 10, "bold"))
        s.configure("TButton", background=THEME["bg_hover"],
                     foreground=text, borderwidth=0, focusthickness=0,
                     padding=(12, 6), font=("Microsoft YaHei UI", 10))
        s.map("TButton", background=[("active", accent), ("pressed", accent)],
              foreground=[("active", bg)])
        s.configure("Primary.TButton", background=accent,
                     foreground=bg, font=("Microsoft YaHei UI", 10, "bold"))
        s.map("Primary.TButton",
              background=[("active", "#79BFFF"), ("pressed", "#3D8FE0")])
        s.configure("Danger.TButton", background=THEME["danger"],
                     foreground="white", font=("Microsoft YaHei UI", 10, "bold"))
        s.map("Danger.TButton",
              background=[("active", "#FF6B63"), ("pressed", "#D03030")])
        s.configure("Warning.TButton", background=THEME["warning"],
                     foreground="white", font=("Microsoft YaHei UI", 10, "bold"))
        s.map("Warning.TButton",
              background=[("active", "#E5B333"), ("pressed", "#B5831A")])
        s.configure("Treeview", background=card, foreground=text,
                     rowheight=26, fieldbackground=card, borderwidth=0)
        s.configure("Treeview.Heading", background=THEME["bg_hover"],
                     foreground=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9))
        s.map("Treeview", background=[("selected", THEME["bg_hover"])],
              foreground=[("selected", accent)])
        s.configure("Horizontal.TProgressbar", troughcolor=THEME["border"],
                     background=accent, thickness=8, borderwidth=0)
        s.configure("Red.Horizontal.TProgressbar", troughcolor=THEME["border"],
                     background=THEME["danger"], thickness=14)
        s.configure("Green.Horizontal.TProgressbar", troughcolor=THEME["border"],
                     background=THEME["success"], thickness=14)
        s.configure("TNotebook", background=bg, borderwidth=0)
        s.configure("TNotebook.Tab", background=THEME["bg_hover"],
                     foreground=THEME["text_muted"], padding=(16, 8),
                     font=("Microsoft YaHei UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", card)],
              foreground=[("selected", text)])
        s.configure("TCheckbutton", background=card, foreground=text,
                     font=("Microsoft YaHei UI", 10))
        s.map("TCheckbutton", background=[("active", card)],
              indicatorcolor=[("selected", accent), ("!selected", THEME["border"])])

    # ── UI 构建 ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        header = tk.Frame(self, bg=THEME["bg_card"],
                          highlightthickness=1,
                          highlightbackground=THEME["border"])
        header.pack(fill="x")

        tk.Label(header, text="🛡️  磁盘深度分析 & 安全清理  v2.0",
                 font=("Microsoft YaHei UI", 16, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left", padx=20, pady=12)
        tk.Label(header, text="安全第一 · 深度清理三级风险分类",
                 font=("Microsoft YaHei UI", 9),
                 bg=THEME["bg_card"], fg=THEME["text_muted"]).pack(side="left", padx=5)

        # 管理员状态徽章
        admin_text = "🔓 管理员模式" if is_admin() else "🔒 普通模式（部分清理受限）"
        admin_color = THEME["success"] if is_admin() else THEME["warning"]
        tk.Label(header, text=admin_text, font=("Microsoft YaHei UI", 9, "bold"),
                 bg=THEME["bg_card"], fg=admin_color).pack(side="right", padx=16)

        self.status_var = tk.StringVar(value="就绪，正在读取磁盘信息…")
        status_bar = tk.Label(self, textvariable=self.status_var,
                              bg=THEME["bg_card"], fg=THEME["text_muted"],
                              font=("Microsoft YaHei UI", 9), anchor="w", padx=12,
                              highlightthickness=1,
                              highlightbackground=THEME["border"])
        status_bar.pack(side="bottom", fill="x", ipady=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_overview = ttk.Frame(nb)
        self.tab_analyze  = ttk.Frame(nb)
        self.tab_clean    = ttk.Frame(nb)
        self.tab_large    = ttk.Frame(nb)
        self.tab_deep     = ttk.Frame(nb)

        nb.add(self.tab_overview, text="  📊 磁盘概览  ")
        nb.add(self.tab_analyze,  text="  🔍 文件夹分析  ")
        nb.add(self.tab_clean,    text="  🧹 安全清理  ")
        nb.add(self.tab_large,    text="  📦 大文件搜索  ")
        nb.add(self.tab_deep,     text="  🔬 深度清理  ")

        self._build_overview_tab()
        self._build_analyze_tab()
        self._build_clean_tab()
        self._build_large_tab()
        self._build_deep_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — 磁盘概览
    # ══════════════════════════════════════════════════════════════════════════
    def _build_overview_tab(self):
        frame = self.tab_overview
        tk.Label(frame, text="所有驱动器空间使用情况",
                 font=("Microsoft YaHei UI", 13, "bold"),
                 bg=THEME["bg_dark"], fg=THEME["text_main"]).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(frame, text="实时读取 Windows 磁盘分区信息",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=16)

        self.overview_scroll_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        self.overview_scroll_frame.pack(fill="both", expand=True, padx=12, pady=10)

        btn_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text="🔄  刷新磁盘信息",
                   style="Primary.TButton",
                   command=self._refresh_overview).pack()

    def _refresh_overview(self):
        for w in self.overview_scroll_frame.winfo_children():
            w.destroy()
        self._set_status("正在读取磁盘信息…")
        try:
            import psutil
            partitions = psutil.disk_partitions()
        except ImportError:
            partitions = self._get_drives_fallback()

        cols = 2
        for idx, part in enumerate(partitions):
            try:
                usage = shutil.disk_usage(part.mountpoint if hasattr(part, "mountpoint") else part)
                mount = part.mountpoint if hasattr(part, "mountpoint") else part
                fstype = getattr(part, "fstype", "NTFS")
                total, used, free = usage.total, usage.used, usage.free
                pct = used / total * 100 if total > 0 else 0
            except Exception:
                continue

            row, col = divmod(idx, cols)
            card = tk.Frame(self.overview_scroll_frame, bg=THEME["bg_card"],
                            highlightthickness=1, highlightbackground=THEME["border"])
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            self.overview_scroll_frame.columnconfigure(col, weight=1)

            title_row = tk.Frame(card, bg=THEME["bg_card"])
            title_row.pack(fill="x", padx=14, pady=(12, 4))
            tk.Label(title_row, text=f"💾  {mount}",
                     font=("Microsoft YaHei UI", 13, "bold"),
                     bg=THEME["bg_card"], fg=THEME["text_main"]).pack(side="left")
            color = THEME["danger"] if pct > 85 else THEME["warning"] if pct > 70 else THEME["success"]
            tk.Label(title_row, text=f"{pct:.1f}%",
                     font=("Microsoft YaHei UI", 13, "bold"),
                     bg=THEME["bg_card"], fg=color).pack(side="right")

            bar_frame = tk.Frame(card, bg=THEME["bg_dark"], height=12)
            bar_frame.pack(fill="x", padx=14, pady=2)
            bar_frame.pack_propagate(False)
            canvas = tk.Canvas(bar_frame, height=12, bg=THEME["border"],
                               highlightthickness=0, bd=0)
            canvas.pack(fill="both")
            canvas.update_idletasks()
            w = canvas.winfo_width() or 400
            fill_w = int(w * pct / 100)
            canvas.create_rectangle(0, 0, fill_w, 12, fill=color, outline="")

            info_row = tk.Frame(card, bg=THEME["bg_card"])
            info_row.pack(fill="x", padx=14, pady=(4, 10))
            tk.Label(info_row, text=f"已用: {format_size(used)}",
                     bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9)).pack(side="left")
            tk.Label(info_row, text=f"可用: {format_size(free)}",
                     bg=THEME["bg_card"], fg=THEME["success"],
                     font=("Microsoft YaHei UI", 9)).pack(side="left", padx=20)
            tk.Label(info_row, text=f"总计: {format_size(total)}",
                     bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9)).pack(side="right")

        self._set_status("磁盘信息读取完毕")

    def _get_drives_fallback(self):
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if bitmask & 1:
                drives.append(type("P", (), {"mountpoint": f"{letter}:\\", "fstype": "NTFS"})())
            bitmask >>= 1
        return drives

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — 文件夹分析
    # ══════════════════════════════════════════════════════════════════════════
    def _build_analyze_tab(self):
        frame = self.tab_analyze

        top = tk.Frame(frame, bg=THEME["bg_dark"])
        top.pack(fill="x", padx=14, pady=12)
        tk.Label(top, text="选择要分析的文件夹：",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.analyze_path_var = tk.StringVar(value="C:\\")
        tk.Entry(top, textvariable=self.analyze_path_var,
                 bg=THEME["bg_card"], fg=THEME["text_main"],
                 insertbackground=THEME["text_main"],
                 relief="flat", bd=0, font=("Microsoft YaHei UI", 10),
                 width=40).pack(side="left", padx=8, ipady=6, ipadx=4)
        ttk.Button(top, text="📂 浏览", command=self._browse_analyze).pack(side="left")
        ttk.Button(top, text="🔍 开始分析", style="Primary.TButton",
                   command=self._start_analyze).pack(side="left", padx=8)

        self.analyze_progress = ttk.Progressbar(frame, mode="indeterminate",
                                                 style="Horizontal.TProgressbar")
        self.analyze_progress.pack(fill="x", padx=14, pady=2)

        tree_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        tree_frame.pack(fill="both", expand=True, padx=14, pady=4)

        self.analyze_tree = ttk.Treeview(tree_frame,
                                          columns=("size", "pct", "items"),
                                          show="tree headings")
        self.analyze_tree.heading("#0",    text="文件夹")
        self.analyze_tree.heading("size",  text="大小")
        self.analyze_tree.heading("pct",   text="占比")
        self.analyze_tree.heading("items", text="子项数")
        self.analyze_tree.column("#0",    width=400, stretch=True)
        self.analyze_tree.column("size",  width=100, anchor="e")
        self.analyze_tree.column("pct",   width=80,  anchor="e")
        self.analyze_tree.column("items", width=80,  anchor="e")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.analyze_tree.yview)
        self.analyze_tree.configure(yscrollcommand=vsb.set)
        self.analyze_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _browse_analyze(self):
        path = filedialog.askdirectory(initialdir=self.analyze_path_var.get())
        if path:
            self.analyze_path_var.set(path)

    def _start_analyze(self):
        path = self.analyze_path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("错误", f"路径不存在：{path}")
            return
        self.analyze_tree.delete(*self.analyze_tree.get_children())
        self.analyze_progress.start(10)
        self._set_status(f"正在分析 {path}，请稍候…")
        threading.Thread(target=self._run_analyze, args=(path,), daemon=True).start()

    def _run_analyze(self, root_path):
        try:
            entries = []
            with os.scandir(root_path) as it:
                for entry in it:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            sz = get_folder_size(entry.path)
                            try:
                                items = len(os.listdir(entry.path))
                            except Exception:
                                items = 0
                            entries.append((entry.path, entry.name, sz, items))
                        elif entry.is_file(follow_symlinks=False):
                            sz = entry.stat().st_size
                            entries.append((entry.path, entry.name, sz, 0))
                    except (PermissionError, OSError):
                        pass
            entries.sort(key=lambda x: x[2], reverse=True)
            total_sz = sum(e[2] for e in entries) or 1
            self.after(0, self._populate_analyze_tree, entries, total_sz, root_path)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("分析错误", str(e)))
        finally:
            self.after(0, self.analyze_progress.stop)
            self.after(0, self._set_status, "分析完成")

    def _populate_analyze_tree(self, entries, total_sz, root_path):
        self.analyze_tree.delete(*self.analyze_tree.get_children())
        root_sz = get_folder_size(root_path)
        self.analyze_tree.insert("", "end", text=f"📁 {root_path}",
                                  values=(format_size(root_sz), "100%", len(entries)))
        for path, name, sz, items in entries[:80]:
            icon = "📁" if os.path.isdir(path) else "📄"
            pct = sz / total_sz * 100
            self.analyze_tree.insert("", "end",
                                      text=f"  {icon} {name}",
                                      values=(format_size(sz),
                                              f"{pct:.1f}%",
                                              items if os.path.isdir(path) else "-"))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — 安全清理
    # ══════════════════════════════════════════════════════════════════════════
    def _build_clean_tab(self):
        frame = self.tab_clean

        tk.Label(frame, text="🛡️  安全清理 — 所有操作均需二次确认",
                 font=("Microsoft YaHei UI", 13, "bold"),
                 bg=THEME["bg_dark"], fg=THEME["text_main"]).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(frame, text="✅ 仅包含可安全删除的缓存与临时文件，不涉及系统核心文件",
                 bg=THEME["bg_dark"], fg=THEME["success"],
                 font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=16, pady=(0, 8))

        top_btn = tk.Frame(frame, bg=THEME["bg_dark"])
        top_btn.pack(fill="x", padx=14, pady=4)
        ttk.Button(top_btn, text="🔎  扫描可清理空间",
                   style="Primary.TButton",
                   command=self._scan_clean_targets).pack(side="left")
        self.scan_result_label = tk.Label(top_btn, text="",
                                           bg=THEME["bg_dark"],
                                           fg=THEME["warning"],
                                           font=("Microsoft YaHei UI", 10, "bold"))
        self.scan_result_label.pack(side="left", padx=16)

        # 清理项列表（可滚动）
        outer = tk.Frame(frame, bg=THEME["bg_dark"])
        outer.pack(fill="both", expand=True, padx=14, pady=4)

        canvas = tk.Canvas(outer, bg=THEME["bg_dark"], highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        list_frame = tk.Frame(canvas, bg=THEME["bg_dark"])
        canvas_win = canvas.create_window((0, 0), window=list_frame, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_win, width=e.width)
        list_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # 表头
        header_row = tk.Frame(list_frame, bg=THEME["bg_card"],
                               highlightthickness=1,
                               highlightbackground=THEME["border"])
        header_row.pack(fill="x", pady=(0, 2))
        for txt, w in [("选择", 5), ("清理项目", 22), ("可释放空间", 14), ("说明", 0)]:
            tk.Label(header_row, text=txt, width=w,
                     bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9)).pack(side="left", padx=10, pady=6)

        self.clean_vars = {}
        self.clean_size_labels = {}

        for name, info in CLEAN_TARGETS.items():
            var = tk.BooleanVar(value=True)
            self.clean_vars[name] = var

            row = tk.Frame(list_frame, bg=THEME["bg_card"],
                           highlightthickness=1, highlightbackground=THEME["border"])
            row.pack(fill="x", pady=1)

            tk.Checkbutton(row, variable=var, bg=THEME["bg_card"],
                           activebackground=THEME["bg_card"],
                           selectcolor=THEME["bg_dark"],
                           fg=THEME["accent"], width=3).pack(side="left", padx=8, pady=8)
            tk.Label(row, text="●", fg=info["color"],
                     bg=THEME["bg_card"], font=("", 8)).pack(side="left")
            tk.Label(row, text=name, width=21, anchor="w",
                     bg=THEME["bg_card"], fg=THEME["text_main"],
                     font=("Microsoft YaHei UI", 10)).pack(side="left", padx=6, pady=8)

            size_lbl = tk.Label(row, text="待扫描", width=14, anchor="e",
                                bg=THEME["bg_card"], fg=THEME["warning"],
                                font=("Microsoft YaHei UI", 10, "bold"))
            size_lbl.pack(side="left", padx=4)
            self.clean_size_labels[name] = size_lbl

            tk.Label(row, text=info["description"], anchor="w",
                     bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9)).pack(side="left", padx=8, fill="x")

        btn_row = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_row.pack(fill="x", padx=14, pady=10)
        ttk.Button(btn_row, text="☑  全选",
                   command=lambda: [v.set(True) for v in self.clean_vars.values()]).pack(side="left")
        ttk.Button(btn_row, text="☐  全不选",
                   command=lambda: [v.set(False) for v in self.clean_vars.values()]).pack(side="left", padx=6)
        ttk.Button(btn_row, text="🧹  执行清理（需确认）",
                   style="Danger.TButton",
                   command=self._execute_clean).pack(side="right")

        self.clean_progress = ttk.Progressbar(frame, mode="indeterminate",
                                               style="Horizontal.TProgressbar")
        self.clean_progress.pack(fill="x", padx=14, pady=2)

    def _scan_clean_targets(self):
        self._set_status("正在扫描可清理空间…")
        self.clean_progress.start(10)
        threading.Thread(target=self._run_scan_clean, daemon=True).start()

    def _get_target_size(self, info: dict) -> int:
        """计算一个清理目标的磁盘占用大小（支持 subdirs 过滤）"""
        sz = 0
        subdirs = info.get("subdirs")
        for p in info.get("paths", []):
            if not os.path.exists(p):
                continue
            if subdirs:
                # 仅扫描指定子目录
                for root, dirs, _ in os.walk(p):
                    dirs[:] = [d for d in dirs if d in subdirs]
                    for d in dirs:
                        sz += get_folder_size(os.path.join(root, d))
            else:
                sz += get_folder_size(p)
        return sz

    def _run_scan_clean(self):
        total_freeable = 0
        for name, info in CLEAN_TARGETS.items():
            if "RECYCLE_BIN" in info["paths"]:
                sz = self._get_recycle_bin_size()
            else:
                sz = self._get_target_size(info)
            total_freeable += sz
            lbl = self.clean_size_labels[name]
            color = THEME["success"] if sz == 0 else THEME["warning"]
            self.after(0, lbl.config, {"text": format_size(sz), "fg": color})

        self.after(0, self.scan_result_label.config,
                   {"text": f"💡 可释放空间：{format_size(total_freeable)}"})
        self.after(0, self.clean_progress.stop)
        self.after(0, self._set_status, f"扫描完成，可释放 {format_size(total_freeable)}")

    def _get_recycle_bin_size(self) -> int:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject Shell.Application).Namespace(10).Items() | "
                 "Measure-Object -Property Size -Sum | Select -ExpandProperty Sum"],
                capture_output=True, text=True, timeout=10
            )
            val = result.stdout.strip()
            return int(val) if val.isdigit() else 0
        except Exception:
            return 0

    def _execute_clean(self):
        selected = [name for name, var in self.clean_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("未选择", "请至少选择一项清理内容！")
            return
        msg = "确认清理以下项目？\n\n" + "\n".join(f"  • {n}" for n in selected)
        msg += "\n\n⚠️ 此操作不可撤销。系统核心文件不受影响。"
        if not messagebox.askyesno("🛡️ 安全确认", msg, icon="warning"):
            return
        self.clean_progress.start(10)
        self._set_status("正在清理…")
        threading.Thread(target=self._run_clean, args=(selected,), daemon=True).start()

    def _run_clean(self, selected):
        results = []
        total_freed = 0

        for name in selected:
            info = CLEAN_TARGETS[name]
            freed = 0

            if "RECYCLE_BIN" in info["paths"]:
                try:
                    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                    results.append(f"✅ {name}：已清空")
                except Exception as e:
                    results.append(f"⚠️ {name}：{e}")
                continue

            subdirs = info.get("subdirs")
            for path in info["paths"]:
                if not os.path.exists(path):
                    continue
                if not is_safe_to_delete(path):
                    results.append(f"🛡️ {name} ({path})：受保护路径，已跳过")
                    continue
                try:
                    scan_root = path
                    if subdirs:
                        # 仅删除指定子目录内容
                        for root, dirs, files in os.walk(scan_root):
                            for d in list(dirs):
                                if d in subdirs:
                                    full = os.path.join(root, d)
                                    sz = get_folder_size(full)
                                    shutil.rmtree(full, ignore_errors=True)
                                    freed += sz
                                    total_freed += sz
                            dirs[:] = []  # 不递归进非目标子目录
                    else:
                        for item in os.scandir(path):
                            try:
                                sz = get_folder_size(item.path) if item.is_dir() else item.stat().st_size
                                if item.is_dir(follow_symlinks=False):
                                    shutil.rmtree(item.path, ignore_errors=True)
                                else:
                                    os.remove(item.path)
                                freed += sz
                                total_freed += sz
                            except Exception:
                                pass
                except Exception as ex:
                    results.append(f"⚠️ {name} 部分失败：{ex}")
                    continue

            results.append(f"✅ {name}：释放 {format_size(freed)}")

        for name in selected:
            lbl = self.clean_size_labels.get(name)
            if lbl:
                self.after(0, lbl.config, {"text": "0 B", "fg": THEME["success"]})

        self.after(0, self.clean_progress.stop)
        self.after(0, self._set_status,
                   f"清理完成！共释放 {format_size(total_freed)}")
        report = "\n".join(results) + f"\n\n共释放：{format_size(total_freed)}"
        self.after(0, messagebox.showinfo, "清理完成", report)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — 大文件搜索
    # ══════════════════════════════════════════════════════════════════════════
    def _build_large_tab(self):
        frame = self.tab_large

        top = tk.Frame(frame, bg=THEME["bg_dark"])
        top.pack(fill="x", padx=14, pady=12)

        tk.Label(top, text="搜索路径：", bg=THEME["bg_dark"],
                 fg=THEME["text_muted"], font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.large_path_var = tk.StringVar(value="C:\\Users")
        tk.Entry(top, textvariable=self.large_path_var,
                 bg=THEME["bg_card"], fg=THEME["text_main"],
                 insertbackground=THEME["text_main"],
                 relief="flat", bd=0, font=("Microsoft YaHei UI", 10),
                 width=30).pack(side="left", padx=6, ipady=6, ipadx=4)
        ttk.Button(top, text="📂", command=self._browse_large).pack(side="left")

        tk.Label(top, text="最小大小(MB)：",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 10)).pack(side="left", padx=(10, 4))
        self.min_size_var = tk.StringVar(value="100")
        tk.Entry(top, textvariable=self.min_size_var, width=6,
                 bg=THEME["bg_card"], fg=THEME["text_main"],
                 insertbackground=THEME["text_main"],
                 relief="flat", bd=0, font=("Microsoft YaHei UI", 10)).pack(
            side="left", ipady=6, ipadx=4)

        # ── 新增：文件年龄过滤 ──
        tk.Label(top, text="超过(天)未访问：",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 10)).pack(side="left", padx=(10, 4))
        self.min_age_var = tk.StringVar(value="0")
        tk.Entry(top, textvariable=self.min_age_var, width=5,
                 bg=THEME["bg_card"], fg=THEME["text_main"],
                 insertbackground=THEME["text_main"],
                 relief="flat", bd=0, font=("Microsoft YaHei UI", 10)).pack(
            side="left", ipady=6, ipadx=4)
        tk.Label(top, text="（0=不过滤）",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 8)).pack(side="left")

        ttk.Button(top, text="🔍 搜索大文件",
                   style="Primary.TButton",
                   command=self._start_large_search).pack(side="left", padx=8)

        self.large_progress = ttk.Progressbar(frame, mode="indeterminate",
                                               style="Horizontal.TProgressbar")
        self.large_progress.pack(fill="x", padx=14, pady=2)

        tree_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        tree_frame.pack(fill="both", expand=True, padx=14, pady=4)

        self.large_tree = ttk.Treeview(tree_frame,
                                        columns=("size", "modified", "last_access", "path"),
                                        show="headings")
        self.large_tree.heading("size",        text="文件大小")
        self.large_tree.heading("modified",    text="修改时间")
        self.large_tree.heading("last_access", text="最后访问")
        self.large_tree.heading("path",        text="完整路径")
        self.large_tree.column("size",        width=100, anchor="e")
        self.large_tree.column("modified",    width=140, anchor="center")
        self.large_tree.column("last_access", width=140, anchor="center")
        self.large_tree.column("path",        width=480, stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.large_tree.yview)
        self.large_tree.configure(yscrollcommand=vsb.set)
        self.large_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btn_row = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_row.pack(fill="x", padx=14, pady=6)
        ttk.Button(btn_row, text="📂 在文件夹中打开",
                   command=self._open_selected_location).pack(side="left")
        ttk.Button(btn_row, text="🗑️ 安全删除选中文件",
                   style="Danger.TButton",
                   command=self._delete_selected_large).pack(side="left", padx=8)

        self.large_count_label = tk.Label(btn_row, text="",
                                           bg=THEME["bg_dark"],
                                           fg=THEME["text_muted"],
                                           font=("Microsoft YaHei UI", 9))
        self.large_count_label.pack(side="right")

    def _browse_large(self):
        path = filedialog.askdirectory(initialdir=self.large_path_var.get())
        if path:
            self.large_path_var.set(path)

    def _start_large_search(self):
        path = self.large_path_var.get()
        if not os.path.exists(path):
            messagebox.showerror("错误", f"路径不存在：{path}")
            return
        try:
            min_mb = float(self.min_size_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字（MB）")
            return
        try:
            min_age = int(self.min_age_var.get())
        except ValueError:
            min_age = 0

        self.large_tree.delete(*self.large_tree.get_children())
        self.large_count_label.config(text="")
        self.large_progress.start(10)
        self._set_status(f"正在搜索 {path} 中大于 {min_mb}MB 的文件…")
        threading.Thread(target=self._run_large_search,
                          args=(path, min_mb * 1024 * 1024, min_age), daemon=True).start()

    def _run_large_search(self, root_path, min_bytes, min_age_days):
        results = []
        cutoff_time = (datetime.now() - timedelta(days=min_age_days)).timestamp() if min_age_days > 0 else 0
        try:
            for dirpath, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs
                           if is_safe_to_delete(os.path.join(dirpath, d))]
                for fname in files:
                    fpath = os.path.join(dirpath, fname)
                    try:
                        st = os.stat(fpath)
                        if st.st_size < min_bytes:
                            continue
                        if min_age_days > 0 and st.st_atime > cutoff_time:
                            continue
                        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                        atime = datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M")
                        results.append((st.st_size, mtime, atime, fpath))
                    except (PermissionError, OSError):
                        pass
        except Exception as e:
            self.after(0, lambda: self._set_status(f"搜索出错：{e}"))

        results.sort(key=lambda x: x[0], reverse=True)
        self.after(0, self._populate_large_tree, results)

    def _populate_large_tree(self, results):
        self.large_tree.delete(*self.large_tree.get_children())
        total_sz = sum(r[0] for r in results)
        for sz, mtime, atime, fpath in results[:500]:
            self.large_tree.insert("", "end",
                                    values=(format_size(sz), mtime, atime, fpath))
        self.large_progress.stop()
        self.large_count_label.config(
            text=f"共找到 {len(results)} 个文件，合计 {format_size(total_sz)}")
        self._set_status(f"搜索完成，找到 {len(results)} 个大文件")

    def _open_selected_location(self):
        sel = self.large_tree.selection()
        if not sel:
            return
        fpath = self.large_tree.item(sel[0])["values"][3]
        try:
            subprocess.Popen(f'explorer /select,"{fpath}"')
        except Exception:
            os.startfile(os.path.dirname(fpath))

    def _delete_selected_large(self):
        sel = self.large_tree.selection()
        if not sel:
            messagebox.showwarning("未选择", "请先选择要删除的文件")
            return
        files = [self.large_tree.item(s)["values"][3] for s in sel]
        unsafe = [f for f in files if not is_safe_to_delete(f)]
        if unsafe:
            messagebox.showerror("安全阻止",
                                  "以下文件属于受保护路径，不可删除：\n" +
                                  "\n".join(unsafe))
            return

        msg = f"确认删除以下 {len(files)} 个文件？\n"
        msg += "\n".join(f"  • {os.path.basename(f)}" for f in files[:10])
        if len(files) > 10:
            msg += f"\n  …及其余 {len(files)-10} 个"
        msg += "\n\n⚠️ 此操作不可撤销！"
        if not messagebox.askyesno("确认删除", msg, icon="warning"):
            return

        freed = 0
        failed = []
        for f in files:
            try:
                sz = os.path.getsize(f)
                os.remove(f)
                freed += sz
                for item in self.large_tree.get_children():
                    if self.large_tree.item(item)["values"][3] == f:
                        self.large_tree.delete(item)
                        break
            except Exception as e:
                failed.append(f"{os.path.basename(f)}: {e}")

        msg_done = f"✅ 成功删除 {len(files)-len(failed)} 个文件\n释放空间：{format_size(freed)}"
        if failed:
            msg_done += f"\n\n⚠️ {len(failed)} 个文件删除失败：\n" + "\n".join(failed[:5])
        messagebox.showinfo("删除完成", msg_done)
        self._set_status(f"删除完成，释放 {format_size(freed)}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — 深度清理（新增）
    # ══════════════════════════════════════════════════════════════════════════
    def _build_deep_tab(self):
        frame = self.tab_deep

        # 标题区
        tk.Label(frame,
                 text="🔬  深度清理 — 高级清理项，请仔细阅读风险说明",
                 font=("Microsoft YaHei UI", 13, "bold"),
                 bg=THEME["bg_dark"], fg=THEME["text_main"]).pack(anchor="w", padx=16, pady=(14, 2))

        legend = tk.Frame(frame, bg=THEME["bg_dark"])
        legend.pack(anchor="w", padx=16, pady=(0, 8))
        for risk, label in RISK_LABELS.items():
            tk.Label(legend,
                     text=f"{RISK_ICONS[risk]} {label}  ",
                     bg=THEME["bg_dark"], fg=RISK_COLORS[risk],
                     font=("Microsoft YaHei UI", 9, "bold")).pack(side="left")

        # 风险过滤
        filter_row = tk.Frame(frame, bg=THEME["bg_dark"])
        filter_row.pack(fill="x", padx=14, pady=4)
        tk.Label(filter_row, text="风险过滤：",
                 bg=THEME["bg_dark"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 10)).pack(side="left")

        self.deep_filter_var = tk.StringVar(value="all")
        for val, lbl in [("all", "显示全部"), ("safe", "仅安全"), ("moderate", "安全+中等")]:
            tk.Radiobutton(filter_row, text=lbl, variable=self.deep_filter_var,
                           value=val, bg=THEME["bg_dark"], fg=THEME["text_main"],
                           activebackground=THEME["bg_dark"],
                           selectcolor=THEME["bg_card"],
                           font=("Microsoft YaHei UI", 10),
                           command=self._apply_deep_filter).pack(side="left", padx=8)

        # 扫描 & 汇总
        top_btn = tk.Frame(frame, bg=THEME["bg_dark"])
        top_btn.pack(fill="x", padx=14, pady=4)
        ttk.Button(top_btn, text="🔎  扫描深度清理空间",
                   style="Primary.TButton",
                   command=self._scan_deep_targets).pack(side="left")
        self.deep_scan_label = tk.Label(top_btn, text="",
                                         bg=THEME["bg_dark"],
                                         fg=THEME["warning"],
                                         font=("Microsoft YaHei UI", 10, "bold"))
        self.deep_scan_label.pack(side="left", padx=16)

        # 可滚动清理列表
        outer = tk.Frame(frame, bg=THEME["bg_dark"])
        outer.pack(fill="both", expand=True, padx=14, pady=4)

        canvas = tk.Canvas(outer, bg=THEME["bg_dark"], highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.deep_list_frame = tk.Frame(canvas, bg=THEME["bg_dark"])
        canvas_win = canvas.create_window((0, 0), window=self.deep_list_frame, anchor="nw")

        def _on_cf(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_cc(e):
            canvas.itemconfig(canvas_win, width=e.width)
        self.deep_list_frame.bind("<Configure>", _on_cf)
        canvas.bind("<Configure>", _on_cc)

        # 表头
        hdr = tk.Frame(self.deep_list_frame, bg=THEME["bg_card"],
                       highlightthickness=1, highlightbackground=THEME["border"])
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("选", 3), ("风险", 6), ("清理项目", 22), ("可释放", 12), ("说明", 0)]:
            tk.Label(hdr, text=txt, width=w,
                     bg=THEME["bg_card"], fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 9)).pack(side="left", padx=8, pady=6)

        self.deep_vars       = {}
        self.deep_size_lbls  = {}
        self.deep_row_frames = {}

        for name, info in DEEP_CLEAN_TARGETS.items():
            self._build_deep_row(name, info)

        # 底部操作区
        btn_row = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_row.pack(fill="x", padx=14, pady=8)

        ttk.Button(btn_row, text="☑ 全选安全项",
                   command=self._deep_select_safe).pack(side="left")
        ttk.Button(btn_row, text="☐ 全不选",
                   command=lambda: [v.set(False) for v in self.deep_vars.values()]).pack(side="left", padx=6)

        ttk.Button(btn_row, text="🗄  DISM 组件存储清理（需管理员）",
                   style="Warning.TButton",
                   command=self._run_dism_cleanup).pack(side="left", padx=16)

        self.hiber_btn_var = tk.StringVar()
        self._update_hiber_btn_text()
        ttk.Button(btn_row, textvariable=self.hiber_btn_var,
                   command=self._toggle_hibernation).pack(side="left")

        ttk.Button(btn_row, text="🔴  执行深度清理（需确认）",
                   style="Danger.TButton",
                   command=self._execute_deep_clean).pack(side="right")

        self.deep_progress = ttk.Progressbar(frame, mode="indeterminate",
                                              style="Horizontal.TProgressbar")
        self.deep_progress.pack(fill="x", padx=14, pady=2)

    def _build_deep_row(self, name: str, info: dict):
        risk    = info["risk"]
        r_color = RISK_COLORS[risk]
        r_icon  = RISK_ICONS[risk]
        r_label = RISK_LABELS[risk]

        var = tk.BooleanVar(value=(risk == "safe"))
        self.deep_vars[name] = var

        row = tk.Frame(self.deep_list_frame, bg=THEME["bg_card"],
                       highlightthickness=1, highlightbackground=THEME["border"])
        row.pack(fill="x", pady=1)
        self.deep_row_frames[name] = row

        tk.Checkbutton(row, variable=var, bg=THEME["bg_card"],
                       activebackground=THEME["bg_card"],
                       selectcolor=THEME["bg_dark"],
                       fg=THEME["accent"], width=2).pack(side="left", padx=6, pady=8)

        # 风险徽章
        badge = tk.Label(row, text=f"{r_icon} {r_label}", width=7,
                         bg=THEME["bg_card"], fg=r_color,
                         font=("Microsoft YaHei UI", 9, "bold"))
        badge.pack(side="left", padx=4)

        tk.Label(row, text=name, width=21, anchor="w",
                 bg=THEME["bg_card"], fg=THEME["text_main"],
                 font=("Microsoft YaHei UI", 10)).pack(side="left", padx=6, pady=8)

        size_lbl = tk.Label(row, text="待扫描", width=12, anchor="e",
                            bg=THEME["bg_card"], fg=THEME["warning"],
                            font=("Microsoft YaHei UI", 10, "bold"))
        size_lbl.pack(side="left", padx=4)
        self.deep_size_lbls[name] = size_lbl

        # 需要管理员标记
        if info.get("requires_admin") and not is_admin():
            tk.Label(row, text="🔒需管理员", bg=THEME["bg_card"],
                     fg=THEME["text_muted"],
                     font=("Microsoft YaHei UI", 8)).pack(side="left", padx=4)

        tk.Label(row, text=info["description"], anchor="w",
                 bg=THEME["bg_card"], fg=THEME["text_muted"],
                 font=("Microsoft YaHei UI", 9)).pack(side="left", padx=8, fill="x")

    def _apply_deep_filter(self):
        mode = self.deep_filter_var.get()
        for name, info in DEEP_CLEAN_TARGETS.items():
            row = self.deep_row_frames[name]
            risk = info["risk"]
            show = (mode == "all") or \
                   (mode == "safe" and risk == "safe") or \
                   (mode == "moderate" and risk in ("safe", "moderate"))
            if show:
                row.pack(fill="x", pady=1)
            else:
                row.pack_forget()

    def _deep_select_safe(self):
        for name, info in DEEP_CLEAN_TARGETS.items():
            self.deep_vars[name].set(info["risk"] == "safe")

    def _scan_deep_targets(self):
        self._set_status("正在扫描深度清理空间…")
        self.deep_progress.start(10)
        threading.Thread(target=self._run_deep_scan, daemon=True).start()

    def _run_deep_scan(self):
        total = 0
        for name, info in DEEP_CLEAN_TARGETS.items():
            if info.get("dism_action"):
                # DISM 项无法预先量化大小，显示特殊标签
                self.after(0, self.deep_size_lbls[name].config,
                           {"text": "DISM清理", "fg": THEME["warning"]})
                continue

            sz = self._get_target_size(info)
            total += sz
            color = THEME["success"] if sz == 0 else THEME["warning"]
            self.after(0, self.deep_size_lbls[name].config,
                       {"text": format_size(sz), "fg": color})

        self.after(0, self.deep_scan_label.config,
                   {"text": f"💡 可释放空间（不含DISM）：{format_size(total)}"})
        self.after(0, self.deep_progress.stop)
        self.after(0, self._set_status, f"深度扫描完成，约可释放 {format_size(total)}")

    def _execute_deep_clean(self):
        selected = [n for n, v in self.deep_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("未选择", "请至少选择一项深度清理内容！")
            return

        caution_items = [n for n in selected
                         if DEEP_CLEAN_TARGETS[n]["risk"] == "caution"]
        if caution_items:
            warn = ("⚠️ 您选择了以下【谨慎】级清理项，操作不可逆：\n\n" +
                    "\n".join(f"  🔴 {n}" for n in caution_items) +
                    "\n\n确认要继续吗？建议先备份重要数据。")
            if not messagebox.askyesno("⚠️ 高风险操作确认", warn, icon="warning"):
                return

        admin_required = [n for n in selected
                          if DEEP_CLEAN_TARGETS[n].get("requires_admin") and not is_admin()]
        if admin_required:
            messagebox.showwarning("权限不足",
                                   "以下项目需要管理员权限，将被跳过：\n" +
                                   "\n".join(f"  🔒 {n}" for n in admin_required) +
                                   "\n\n请以管理员身份重新运行本程序。")
            selected = [n for n in selected if n not in admin_required]
            if not selected:
                return

        msg = "最终确认清理以下项目？\n\n" + "\n".join(f"  • {n}" for n in selected)
        msg += "\n\n⚠️ 此操作不可撤销！"
        if not messagebox.askyesno("🔬 深度清理最终确认", msg, icon="warning"):
            return

        self.deep_progress.start(10)
        self._set_status("正在执行深度清理…")
        threading.Thread(target=self._run_deep_clean, args=(selected,), daemon=True).start()

    def _run_deep_clean(self, selected):
        results = []
        total_freed = 0

        for name in selected:
            info = DEEP_CLEAN_TARGETS[name]

            if info.get("dism_action"):
                # DISM 操作通过命令行执行
                results.append(f"ℹ️ {name}：请使用下方「DISM 组件存储清理」按钮单独执行")
                continue

            freed = 0
            subdirs = info.get("subdirs")
            for path in info["paths"]:
                if not os.path.exists(path):
                    continue
                if not is_safe_to_delete(path):
                    results.append(f"🛡️ {name} ({path})：受保护，已跳过")
                    continue
                try:
                    if subdirs:
                        for root, dirs, files in os.walk(path):
                            for d in list(dirs):
                                if d in subdirs:
                                    full = os.path.join(root, d)
                                    sz = get_folder_size(full)
                                    shutil.rmtree(full, ignore_errors=True)
                                    freed += sz
                                    total_freed += sz
                            dirs[:] = []
                    else:
                        # 谨慎项：整体删除路径（如 Windows.old）
                        if info["risk"] == "caution" and os.path.isdir(path):
                            sz = get_folder_size(path)
                            shutil.rmtree(path, ignore_errors=True)
                            freed += sz
                            total_freed += sz
                        else:
                            for item in os.scandir(path):
                                try:
                                    sz = get_folder_size(item.path) if item.is_dir() else item.stat().st_size
                                    if item.is_dir(follow_symlinks=False):
                                        shutil.rmtree(item.path, ignore_errors=True)
                                    else:
                                        os.remove(item.path)
                                    freed += sz
                                    total_freed += sz
                                except Exception:
                                    pass
                except Exception as ex:
                    results.append(f"⚠️ {name} 部分失败：{ex}")
                    continue

            results.append(f"✅ {name}：释放 {format_size(freed)}")
            lbl = self.deep_size_lbls.get(name)
            if lbl:
                self.after(0, lbl.config, {"text": "0 B", "fg": THEME["success"]})

        self.after(0, self.deep_progress.stop)
        self.after(0, self._set_status, f"深度清理完成，共释放 {format_size(total_freed)}")
        report = "\n".join(results) + f"\n\n共释放：{format_size(total_freed)}"
        self.after(0, messagebox.showinfo, "深度清理完成", report)

    # ── 特殊操作：DISM 组件存储清理 ──────────────────────────────────────────
    def _run_dism_cleanup(self):
        if not is_admin():
            messagebox.showerror("权限不足",
                                  "DISM 清理需要管理员权限。\n请右键程序选择「以管理员身份运行」。")
            return
        if not messagebox.askyesno("DISM 组件清理",
                                    "将运行 DISM /Online /Cleanup-Image /StartComponentCleanup\n\n"
                                    "此操作会清理 Windows 更新遗留的冗余组件，\n"
                                    "通常可释放 1~5 GB 空间，耗时可能较长（5~20分钟）。\n\n"
                                    "确认继续？",
                                    icon="info"):
            return

        self._set_status("正在执行 DISM 组件清理，请勿关闭程序…")
        threading.Thread(target=self._do_dism, daemon=True).start()

    def _do_dism(self):
        try:
            result = subprocess.run(
                ["dism", "/Online", "/Cleanup-Image", "/StartComponentCleanup"],
                capture_output=True, text=True, timeout=1200
            )
            if result.returncode == 0:
                self.after(0, messagebox.showinfo, "DISM 完成",
                           "✅ DISM 组件存储清理成功完成！\n\n" + result.stdout[-800:])
                self.after(0, self._set_status, "DISM 清理完成")
            else:
                self.after(0, messagebox.showerror, "DISM 失败",
                           f"❌ DISM 返回错误：{result.returncode}\n{result.stderr[-400:]}")
                self.after(0, self._set_status, "DISM 清理失败")
        except subprocess.TimeoutExpired:
            self.after(0, messagebox.showwarning, "DISM 超时",
                       "DISM 操作超时（20分钟）。可在命令行手动运行。")
        except Exception as e:
            self.after(0, messagebox.showerror, "DISM 错误", str(e))

    # ── 特殊操作：休眠文件管理 ───────────────────────────────────────────────
    def _update_hiber_btn_text(self):
        hiber_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "hiberfil.sys")
        exists = os.path.exists(hiber_path)
        try:
            size = os.path.getsize(hiber_path) if exists else 0
        except Exception:
            size = 0
        if exists and size > 0:
            self.hiber_btn_var.set(f"💤 禁用休眠（节省 {format_size(size)}）")
        else:
            self.hiber_btn_var.set("💤 启用休眠")

    def _toggle_hibernation(self):
        if not is_admin():
            messagebox.showerror("权限不足",
                                  "休眠文件管理需要管理员权限。\n请右键程序选择「以管理员身份运行」。")
            return
        hiber_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "hiberfil.sys")
        enabled = os.path.exists(hiber_path) and os.path.getsize(hiber_path) > 0

        if enabled:
            if not messagebox.askyesno("禁用休眠",
                                        "禁用休眠将删除 hiberfil.sys，释放等于内存大小的磁盘空间。\n"
                                        "⚠️ 禁用后无法使用休眠功能（快速启动也会受影响）。\n\n确认继续？",
                                        icon="warning"):
                return
            try:
                subprocess.run(["powercfg", "/h", "off"],
                               check=True, capture_output=True, timeout=15)
                messagebox.showinfo("完成", "✅ 休眠已禁用，hiberfil.sys 已删除。")
            except Exception as e:
                messagebox.showerror("失败", f"操作失败：{e}")
        else:
            if not messagebox.askyesno("启用休眠",
                                        "启用休眠会创建 hiberfil.sys，占用等于内存大小的磁盘空间。\n\n确认继续？"):
                return
            try:
                subprocess.run(["powercfg", "/h", "on"],
                               check=True, capture_output=True, timeout=15)
                messagebox.showinfo("完成", "✅ 休眠已启用。")
            except Exception as e:
                messagebox.showerror("失败", f"操作失败：{e}")

        self._update_hiber_btn_text()
        self._set_status("休眠设置已更新")

    # ── 辅助 ──────────────────────────────────────────────────────────────────
    def _set_status(self, msg: str):
        self.status_var.set(f"  {msg}")

    def _auto_scan(self):
        self._refresh_overview()


# ─── 入口 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not is_admin():
        print("提示：以管理员身份运行可解锁更多清理项目（DISM、休眠文件、字体缓存等）")

    try:
        import psutil
    except ImportError:
        pass

    app = DiskCleanerApp()
    app.mainloop()

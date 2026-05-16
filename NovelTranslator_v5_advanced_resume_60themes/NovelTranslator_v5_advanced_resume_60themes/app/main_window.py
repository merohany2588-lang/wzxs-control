from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QProgressBar, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QLineEdit, QGridLayout, QMessageBox, QGroupBox,
    QTabWidget, QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea
)

from app.task.translate_worker import TranslateWorker
from app.utils import load_config, save_config, open_dir, fmt_time, OUTPUT_DIR


ENGINE_LABELS = {
    "tencent": "腾讯云 API",
    "baidu": "百度翻译 API",
    "google_free": "Google 免费",
    "mymemory": "MyMemory 免费",
    "opus_mt": "OPUS-MT 本地",
}

STRATEGY_DESCRIPTIONS = {
    "stable_api": "稳定 API：腾讯云 → 百度 → Google 免费 → OPUS-MT → MyMemory。适合大多数正式任务。",
    "api_offline": "API 优先 + 离线兜底：腾讯云 → 百度 → OPUS-MT → 免费接口。适合优先稳定和速度。",
    "free_first": "免费优先：Google 免费 → MyMemory → Libre → OPUS-MT。本模式成本低，但稳定性一般。",
    "free_offline": "免费优先 + 离线兜底：Google 免费 → MyMemory → OPUS-MT → API。适合省钱且保留本地兜底。",
    "free_api_offline": "免费 + API + 离线兜底：Google 免费 → MyMemory → 腾讯云 → 百度 → OPUS-MT。",
    "offline_first": "离线优先：OPUS-MT → Google 免费 → MyMemory。适合断网或尽量本地跑。",
    "tencent_first": "腾讯优先：腾讯云 → 百度 → OPUS-MT → 免费接口。",
    "baidu_first": "百度优先：百度 → 腾讯云 → OPUS-MT → 免费接口。",
    "custom": "自定义顺序：按下方“手动排序列表”的顺序执行。你可以上移/下移来自由排列。",
}

THEMES = {
    "deep_blue": {"name": "深海蓝", "bg": "#0d111a", "panel": "#151a25", "input": "#1a2033", "line": "#26324d", "accent": "#f2b84b", "accent2": "#3d7eff", "text": "#dce7ff", "subtext": "#8d9aba", "success_bg": "#151a25", "success_text": "#f2b84b", "tab": "#1a2033", "tab_active": "#3d7eff"},
    "emerald": {"name": "祖母绿", "bg": "#0d1714", "panel": "#16211d", "input": "#1d2d27", "line": "#2f4f45", "accent": "#4fe39a", "accent2": "#12b981", "text": "#e8fff5", "subtext": "#98b9aa", "success_bg": "#16211d", "success_text": "#4fe39a", "tab": "#1d2d27", "tab_active": "#12b981"},
    "violet": {"name": "紫晶夜", "bg": "#120f1d", "panel": "#1c1730", "input": "#272041", "line": "#403463", "accent": "#b990ff", "accent2": "#8b5cf6", "text": "#f0eaff", "subtext": "#b8acd8", "success_bg": "#1c1730", "success_text": "#b990ff", "tab": "#272041", "tab_active": "#8b5cf6"},
    "amber": {"name": "琥珀金", "bg": "#17120b", "panel": "#241b11", "input": "#302316", "line": "#51402a", "accent": "#ffce6b", "accent2": "#f59e0b", "text": "#fff8e6", "subtext": "#d7c3a1", "success_bg": "#241b11", "success_text": "#ffce6b", "tab": "#302316", "tab_active": "#f59e0b"},
    "crimson": {"name": "赤焰红", "bg": "#1b0e10", "panel": "#281619", "input": "#3a2025", "line": "#5c3038", "accent": "#ff6b7a", "accent2": "#ef4444", "text": "#fff1f3", "subtext": "#e3a9b0", "success_bg": "#281619", "success_text": "#ff6b7a", "tab": "#3a2025", "tab_active": "#ef4444"},
    "cyan": {"name": "赛博青", "bg": "#071519", "panel": "#0d2228", "input": "#132f38", "line": "#24505d", "accent": "#67e8f9", "accent2": "#06b6d4", "text": "#e6fbff", "subtext": "#9ccbd4", "success_bg": "#0d2228", "success_text": "#67e8f9", "tab": "#132f38", "tab_active": "#06b6d4"},
    "indigo": {"name": "靛蓝星", "bg": "#0d1020", "panel": "#151a33", "input": "#1e2549", "line": "#354078", "accent": "#a5b4fc", "accent2": "#6366f1", "text": "#eef0ff", "subtext": "#adb5dd", "success_bg": "#151a33", "success_text": "#a5b4fc", "tab": "#1e2549", "tab_active": "#6366f1"},
    "rose": {"name": "玫瑰雾", "bg": "#1b1018", "panel": "#2a1925", "input": "#3a2333", "line": "#5f3852", "accent": "#f9a8d4", "accent2": "#ec4899", "text": "#fff0f8", "subtext": "#e2adc9", "success_bg": "#2a1925", "success_text": "#f9a8d4", "tab": "#3a2333", "tab_active": "#ec4899"},
    "slate": {"name": "石墨灰", "bg": "#0f1217", "panel": "#171b22", "input": "#202632", "line": "#343d4d", "accent": "#cbd5e1", "accent2": "#64748b", "text": "#eef2f7", "subtext": "#a8b3c2", "success_bg": "#171b22", "success_text": "#cbd5e1", "tab": "#202632", "tab_active": "#64748b"},
    "forest": {"name": "森林绿", "bg": "#0c150d", "panel": "#152318", "input": "#1f3423", "line": "#385a40", "accent": "#86efac", "accent2": "#22c55e", "text": "#f0fff4", "subtext": "#a9cbb2", "success_bg": "#152318", "success_text": "#86efac", "tab": "#1f3423", "tab_active": "#22c55e"},
    "ocean": {"name": "海洋蓝", "bg": "#07131f", "panel": "#0e1f33", "input": "#142d49", "line": "#27527c", "accent": "#7dd3fc", "accent2": "#0ea5e9", "text": "#eaf8ff", "subtext": "#a7c8dd", "success_bg": "#0e1f33", "success_text": "#7dd3fc", "tab": "#142d49", "tab_active": "#0ea5e9"},
    "gold": {"name": "王者金", "bg": "#181204", "panel": "#261d08", "input": "#33270c", "line": "#5b4514", "accent": "#facc15", "accent2": "#ca8a04", "text": "#fffbea", "subtext": "#d5bd73", "success_bg": "#261d08", "success_text": "#facc15", "tab": "#33270c", "tab_active": "#ca8a04"},
    "deep_blue_2": {"name": "深海蓝·极夜", "bg": "#0d111a", "panel": "#151a25", "input": "#1a2033", "line": "#26324d", "accent": "#f2b84b", "accent2": "#3d7eff", "text": "#dce7ff", "subtext": "#8d9aba", "success_bg": "#151a25", "success_text": "#f2b84b", "tab": "#1a2033", "tab_active": "#3d7eff"},
    "emerald_2": {"name": "祖母绿·极夜", "bg": "#0d1714", "panel": "#16211d", "input": "#1d2d27", "line": "#2f4f45", "accent": "#4fe39a", "accent2": "#12b981", "text": "#e8fff5", "subtext": "#98b9aa", "success_bg": "#16211d", "success_text": "#4fe39a", "tab": "#1d2d27", "tab_active": "#12b981"},
    "violet_2": {"name": "紫晶夜·极夜", "bg": "#120f1d", "panel": "#1c1730", "input": "#272041", "line": "#403463", "accent": "#b990ff", "accent2": "#8b5cf6", "text": "#f0eaff", "subtext": "#b8acd8", "success_bg": "#1c1730", "success_text": "#b990ff", "tab": "#272041", "tab_active": "#8b5cf6"},
    "amber_2": {"name": "琥珀金·极夜", "bg": "#17120b", "panel": "#241b11", "input": "#302316", "line": "#51402a", "accent": "#ffce6b", "accent2": "#f59e0b", "text": "#fff8e6", "subtext": "#d7c3a1", "success_bg": "#241b11", "success_text": "#ffce6b", "tab": "#302316", "tab_active": "#f59e0b"},
    "crimson_2": {"name": "赤焰红·极夜", "bg": "#1b0e10", "panel": "#281619", "input": "#3a2025", "line": "#5c3038", "accent": "#ff6b7a", "accent2": "#ef4444", "text": "#fff1f3", "subtext": "#e3a9b0", "success_bg": "#281619", "success_text": "#ff6b7a", "tab": "#3a2025", "tab_active": "#ef4444"},
    "cyan_2": {"name": "赛博青·极夜", "bg": "#071519", "panel": "#0d2228", "input": "#132f38", "line": "#24505d", "accent": "#67e8f9", "accent2": "#06b6d4", "text": "#e6fbff", "subtext": "#9ccbd4", "success_bg": "#0d2228", "success_text": "#67e8f9", "tab": "#132f38", "tab_active": "#06b6d4"},
    "indigo_2": {"name": "靛蓝星·极夜", "bg": "#0d1020", "panel": "#151a33", "input": "#1e2549", "line": "#354078", "accent": "#a5b4fc", "accent2": "#6366f1", "text": "#eef0ff", "subtext": "#adb5dd", "success_bg": "#151a33", "success_text": "#a5b4fc", "tab": "#1e2549", "tab_active": "#6366f1"},
    "rose_2": {"name": "玫瑰雾·极夜", "bg": "#1b1018", "panel": "#2a1925", "input": "#3a2333", "line": "#5f3852", "accent": "#f9a8d4", "accent2": "#ec4899", "text": "#fff0f8", "subtext": "#e2adc9", "success_bg": "#2a1925", "success_text": "#f9a8d4", "tab": "#3a2333", "tab_active": "#ec4899"},
    "slate_2": {"name": "石墨灰·极夜", "bg": "#0f1217", "panel": "#171b22", "input": "#202632", "line": "#343d4d", "accent": "#cbd5e1", "accent2": "#64748b", "text": "#eef2f7", "subtext": "#a8b3c2", "success_bg": "#171b22", "success_text": "#cbd5e1", "tab": "#202632", "tab_active": "#64748b"},
    "forest_2": {"name": "森林绿·极夜", "bg": "#0c150d", "panel": "#152318", "input": "#1f3423", "line": "#385a40", "accent": "#86efac", "accent2": "#22c55e", "text": "#f0fff4", "subtext": "#a9cbb2", "success_bg": "#152318", "success_text": "#86efac", "tab": "#1f3423", "tab_active": "#22c55e"},
    "ocean_2": {"name": "海洋蓝·极夜", "bg": "#07131f", "panel": "#0e1f33", "input": "#142d49", "line": "#27527c", "accent": "#7dd3fc", "accent2": "#0ea5e9", "text": "#eaf8ff", "subtext": "#a7c8dd", "success_bg": "#0e1f33", "success_text": "#7dd3fc", "tab": "#142d49", "tab_active": "#0ea5e9"},
    "gold_2": {"name": "王者金·极夜", "bg": "#181204", "panel": "#261d08", "input": "#33270c", "line": "#5b4514", "accent": "#facc15", "accent2": "#ca8a04", "text": "#fffbea", "subtext": "#d5bd73", "success_bg": "#261d08", "success_text": "#facc15", "tab": "#33270c", "tab_active": "#ca8a04"},
    "deep_blue_3": {"name": "深海蓝·星辉", "bg": "#0d111a", "panel": "#151a25", "input": "#1a2033", "line": "#26324d", "accent": "#f2b84b", "accent2": "#3d7eff", "text": "#dce7ff", "subtext": "#8d9aba", "success_bg": "#151a25", "success_text": "#f2b84b", "tab": "#1a2033", "tab_active": "#3d7eff"},
    "emerald_3": {"name": "祖母绿·星辉", "bg": "#0d1714", "panel": "#16211d", "input": "#1d2d27", "line": "#2f4f45", "accent": "#4fe39a", "accent2": "#12b981", "text": "#e8fff5", "subtext": "#98b9aa", "success_bg": "#16211d", "success_text": "#4fe39a", "tab": "#1d2d27", "tab_active": "#12b981"},
    "violet_3": {"name": "紫晶夜·星辉", "bg": "#120f1d", "panel": "#1c1730", "input": "#272041", "line": "#403463", "accent": "#b990ff", "accent2": "#8b5cf6", "text": "#f0eaff", "subtext": "#b8acd8", "success_bg": "#1c1730", "success_text": "#b990ff", "tab": "#272041", "tab_active": "#8b5cf6"},
    "amber_3": {"name": "琥珀金·星辉", "bg": "#17120b", "panel": "#241b11", "input": "#302316", "line": "#51402a", "accent": "#ffce6b", "accent2": "#f59e0b", "text": "#fff8e6", "subtext": "#d7c3a1", "success_bg": "#241b11", "success_text": "#ffce6b", "tab": "#302316", "tab_active": "#f59e0b"},
    "crimson_3": {"name": "赤焰红·星辉", "bg": "#1b0e10", "panel": "#281619", "input": "#3a2025", "line": "#5c3038", "accent": "#ff6b7a", "accent2": "#ef4444", "text": "#fff1f3", "subtext": "#e3a9b0", "success_bg": "#281619", "success_text": "#ff6b7a", "tab": "#3a2025", "tab_active": "#ef4444"},
    "cyan_3": {"name": "赛博青·星辉", "bg": "#071519", "panel": "#0d2228", "input": "#132f38", "line": "#24505d", "accent": "#67e8f9", "accent2": "#06b6d4", "text": "#e6fbff", "subtext": "#9ccbd4", "success_bg": "#0d2228", "success_text": "#67e8f9", "tab": "#132f38", "tab_active": "#06b6d4"},
    "indigo_3": {"name": "靛蓝星·星辉", "bg": "#0d1020", "panel": "#151a33", "input": "#1e2549", "line": "#354078", "accent": "#a5b4fc", "accent2": "#6366f1", "text": "#eef0ff", "subtext": "#adb5dd", "success_bg": "#151a33", "success_text": "#a5b4fc", "tab": "#1e2549", "tab_active": "#6366f1"},
    "rose_3": {"name": "玫瑰雾·星辉", "bg": "#1b1018", "panel": "#2a1925", "input": "#3a2333", "line": "#5f3852", "accent": "#f9a8d4", "accent2": "#ec4899", "text": "#fff0f8", "subtext": "#e2adc9", "success_bg": "#2a1925", "success_text": "#f9a8d4", "tab": "#3a2333", "tab_active": "#ec4899"},
    "slate_3": {"name": "石墨灰·星辉", "bg": "#0f1217", "panel": "#171b22", "input": "#202632", "line": "#343d4d", "accent": "#cbd5e1", "accent2": "#64748b", "text": "#eef2f7", "subtext": "#a8b3c2", "success_bg": "#171b22", "success_text": "#cbd5e1", "tab": "#202632", "tab_active": "#64748b"},
    "forest_3": {"name": "森林绿·星辉", "bg": "#0c150d", "panel": "#152318", "input": "#1f3423", "line": "#385a40", "accent": "#86efac", "accent2": "#22c55e", "text": "#f0fff4", "subtext": "#a9cbb2", "success_bg": "#152318", "success_text": "#86efac", "tab": "#1f3423", "tab_active": "#22c55e"},
    "ocean_3": {"name": "海洋蓝·星辉", "bg": "#07131f", "panel": "#0e1f33", "input": "#142d49", "line": "#27527c", "accent": "#7dd3fc", "accent2": "#0ea5e9", "text": "#eaf8ff", "subtext": "#a7c8dd", "success_bg": "#0e1f33", "success_text": "#7dd3fc", "tab": "#142d49", "tab_active": "#0ea5e9"},
    "gold_3": {"name": "王者金·星辉", "bg": "#181204", "panel": "#261d08", "input": "#33270c", "line": "#5b4514", "accent": "#facc15", "accent2": "#ca8a04", "text": "#fffbea", "subtext": "#d5bd73", "success_bg": "#261d08", "success_text": "#facc15", "tab": "#33270c", "tab_active": "#ca8a04"},
    "deep_blue_4": {"name": "深海蓝·柔光", "bg": "#0d111a", "panel": "#151a25", "input": "#1a2033", "line": "#26324d", "accent": "#f2b84b", "accent2": "#3d7eff", "text": "#dce7ff", "subtext": "#8d9aba", "success_bg": "#151a25", "success_text": "#f2b84b", "tab": "#1a2033", "tab_active": "#3d7eff"},
    "emerald_4": {"name": "祖母绿·柔光", "bg": "#0d1714", "panel": "#16211d", "input": "#1d2d27", "line": "#2f4f45", "accent": "#4fe39a", "accent2": "#12b981", "text": "#e8fff5", "subtext": "#98b9aa", "success_bg": "#16211d", "success_text": "#4fe39a", "tab": "#1d2d27", "tab_active": "#12b981"},
    "violet_4": {"name": "紫晶夜·柔光", "bg": "#120f1d", "panel": "#1c1730", "input": "#272041", "line": "#403463", "accent": "#b990ff", "accent2": "#8b5cf6", "text": "#f0eaff", "subtext": "#b8acd8", "success_bg": "#1c1730", "success_text": "#b990ff", "tab": "#272041", "tab_active": "#8b5cf6"},
    "amber_4": {"name": "琥珀金·柔光", "bg": "#17120b", "panel": "#241b11", "input": "#302316", "line": "#51402a", "accent": "#ffce6b", "accent2": "#f59e0b", "text": "#fff8e6", "subtext": "#d7c3a1", "success_bg": "#241b11", "success_text": "#ffce6b", "tab": "#302316", "tab_active": "#f59e0b"},
    "crimson_4": {"name": "赤焰红·柔光", "bg": "#1b0e10", "panel": "#281619", "input": "#3a2025", "line": "#5c3038", "accent": "#ff6b7a", "accent2": "#ef4444", "text": "#fff1f3", "subtext": "#e3a9b0", "success_bg": "#281619", "success_text": "#ff6b7a", "tab": "#3a2025", "tab_active": "#ef4444"},
    "cyan_4": {"name": "赛博青·柔光", "bg": "#071519", "panel": "#0d2228", "input": "#132f38", "line": "#24505d", "accent": "#67e8f9", "accent2": "#06b6d4", "text": "#e6fbff", "subtext": "#9ccbd4", "success_bg": "#0d2228", "success_text": "#67e8f9", "tab": "#132f38", "tab_active": "#06b6d4"},
    "indigo_4": {"name": "靛蓝星·柔光", "bg": "#0d1020", "panel": "#151a33", "input": "#1e2549", "line": "#354078", "accent": "#a5b4fc", "accent2": "#6366f1", "text": "#eef0ff", "subtext": "#adb5dd", "success_bg": "#151a33", "success_text": "#a5b4fc", "tab": "#1e2549", "tab_active": "#6366f1"},
    "rose_4": {"name": "玫瑰雾·柔光", "bg": "#1b1018", "panel": "#2a1925", "input": "#3a2333", "line": "#5f3852", "accent": "#f9a8d4", "accent2": "#ec4899", "text": "#fff0f8", "subtext": "#e2adc9", "success_bg": "#2a1925", "success_text": "#f9a8d4", "tab": "#3a2333", "tab_active": "#ec4899"},
    "slate_4": {"name": "石墨灰·柔光", "bg": "#0f1217", "panel": "#171b22", "input": "#202632", "line": "#343d4d", "accent": "#cbd5e1", "accent2": "#64748b", "text": "#eef2f7", "subtext": "#a8b3c2", "success_bg": "#171b22", "success_text": "#cbd5e1", "tab": "#202632", "tab_active": "#64748b"},
    "forest_4": {"name": "森林绿·柔光", "bg": "#0c150d", "panel": "#152318", "input": "#1f3423", "line": "#385a40", "accent": "#86efac", "accent2": "#22c55e", "text": "#f0fff4", "subtext": "#a9cbb2", "success_bg": "#152318", "success_text": "#86efac", "tab": "#1f3423", "tab_active": "#22c55e"},
    "ocean_4": {"name": "海洋蓝·柔光", "bg": "#07131f", "panel": "#0e1f33", "input": "#142d49", "line": "#27527c", "accent": "#7dd3fc", "accent2": "#0ea5e9", "text": "#eaf8ff", "subtext": "#a7c8dd", "success_bg": "#0e1f33", "success_text": "#7dd3fc", "tab": "#142d49", "tab_active": "#0ea5e9"},
    "gold_4": {"name": "王者金·柔光", "bg": "#181204", "panel": "#261d08", "input": "#33270c", "line": "#5b4514", "accent": "#facc15", "accent2": "#ca8a04", "text": "#fffbea", "subtext": "#d5bd73", "success_bg": "#261d08", "success_text": "#facc15", "tab": "#33270c", "tab_active": "#ca8a04"},
    "deep_blue_5": {"name": "深海蓝·霓虹", "bg": "#0d111a", "panel": "#151a25", "input": "#1a2033", "line": "#26324d", "accent": "#f2b84b", "accent2": "#3d7eff", "text": "#dce7ff", "subtext": "#8d9aba", "success_bg": "#151a25", "success_text": "#f2b84b", "tab": "#1a2033", "tab_active": "#3d7eff"},
    "emerald_5": {"name": "祖母绿·霓虹", "bg": "#0d1714", "panel": "#16211d", "input": "#1d2d27", "line": "#2f4f45", "accent": "#4fe39a", "accent2": "#12b981", "text": "#e8fff5", "subtext": "#98b9aa", "success_bg": "#16211d", "success_text": "#4fe39a", "tab": "#1d2d27", "tab_active": "#12b981"},
    "violet_5": {"name": "紫晶夜·霓虹", "bg": "#120f1d", "panel": "#1c1730", "input": "#272041", "line": "#403463", "accent": "#b990ff", "accent2": "#8b5cf6", "text": "#f0eaff", "subtext": "#b8acd8", "success_bg": "#1c1730", "success_text": "#b990ff", "tab": "#272041", "tab_active": "#8b5cf6"},
    "amber_5": {"name": "琥珀金·霓虹", "bg": "#17120b", "panel": "#241b11", "input": "#302316", "line": "#51402a", "accent": "#ffce6b", "accent2": "#f59e0b", "text": "#fff8e6", "subtext": "#d7c3a1", "success_bg": "#241b11", "success_text": "#ffce6b", "tab": "#302316", "tab_active": "#f59e0b"},
    "crimson_5": {"name": "赤焰红·霓虹", "bg": "#1b0e10", "panel": "#281619", "input": "#3a2025", "line": "#5c3038", "accent": "#ff6b7a", "accent2": "#ef4444", "text": "#fff1f3", "subtext": "#e3a9b0", "success_bg": "#281619", "success_text": "#ff6b7a", "tab": "#3a2025", "tab_active": "#ef4444"},
    "cyan_5": {"name": "赛博青·霓虹", "bg": "#071519", "panel": "#0d2228", "input": "#132f38", "line": "#24505d", "accent": "#67e8f9", "accent2": "#06b6d4", "text": "#e6fbff", "subtext": "#9ccbd4", "success_bg": "#0d2228", "success_text": "#67e8f9", "tab": "#132f38", "tab_active": "#06b6d4"},
    "indigo_5": {"name": "靛蓝星·霓虹", "bg": "#0d1020", "panel": "#151a33", "input": "#1e2549", "line": "#354078", "accent": "#a5b4fc", "accent2": "#6366f1", "text": "#eef0ff", "subtext": "#adb5dd", "success_bg": "#151a33", "success_text": "#a5b4fc", "tab": "#1e2549", "tab_active": "#6366f1"},
    "rose_5": {"name": "玫瑰雾·霓虹", "bg": "#1b1018", "panel": "#2a1925", "input": "#3a2333", "line": "#5f3852", "accent": "#f9a8d4", "accent2": "#ec4899", "text": "#fff0f8", "subtext": "#e2adc9", "success_bg": "#2a1925", "success_text": "#f9a8d4", "tab": "#3a2333", "tab_active": "#ec4899"},
    "slate_5": {"name": "石墨灰·霓虹", "bg": "#0f1217", "panel": "#171b22", "input": "#202632", "line": "#343d4d", "accent": "#cbd5e1", "accent2": "#64748b", "text": "#eef2f7", "subtext": "#a8b3c2", "success_bg": "#171b22", "success_text": "#cbd5e1", "tab": "#202632", "tab_active": "#64748b"},
    "forest_5": {"name": "森林绿·霓虹", "bg": "#0c150d", "panel": "#152318", "input": "#1f3423", "line": "#385a40", "accent": "#86efac", "accent2": "#22c55e", "text": "#f0fff4", "subtext": "#a9cbb2", "success_bg": "#152318", "success_text": "#86efac", "tab": "#1f3423", "tab_active": "#22c55e"},
    "ocean_5": {"name": "海洋蓝·霓虹", "bg": "#07131f", "panel": "#0e1f33", "input": "#142d49", "line": "#27527c", "accent": "#7dd3fc", "accent2": "#0ea5e9", "text": "#eaf8ff", "subtext": "#a7c8dd", "success_bg": "#0e1f33", "success_text": "#7dd3fc", "tab": "#142d49", "tab_active": "#0ea5e9"},
    "gold_5": {"name": "王者金·霓虹", "bg": "#181204", "panel": "#261d08", "input": "#33270c", "line": "#5b4514", "accent": "#facc15", "accent2": "#ca8a04", "text": "#fffbea", "subtext": "#d5bd73", "success_bg": "#261d08", "success_text": "#facc15", "tab": "#33270c", "tab_active": "#ca8a04"},
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小说翻译器 / Novel Translator")
        self.cfg = load_config()
        self.input_file: str | None = None
        self.worker: TranslateWorker | None = None
        self.last_output_dir: str = str(OUTPUT_DIR)
        self.current_theme = self.cfg.get("theme_name", "deep_blue")

        self._build_ui()
        self._load_config_to_ui()
        self._apply_theme(self.current_theme)
        self.update_strategy_description()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(20, 18, 20, 18)
        main.setSpacing(12)

        # Header
        title_row = QHBoxLayout()
        self.title_label = QLabel("📖 小说翻译器 / Novel Translator")
        self.title_label.setObjectName("Title")
        self.status_badge = QLabel("● 本地运行")
        self.status_badge.setObjectName("Badge")
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        title_row.addWidget(self.status_badge)
        main.addLayout(title_row)

        self.subtitle = QLabel("彩色选项卡 · 设置中心 · 主题切换 · 策略中心 · OPUS-MT 本地兜底")
        self.subtitle.setObjectName("Subtitle")
        main.addWidget(self.subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("Line")
        main.addWidget(line)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        main.addWidget(self.tabs, stretch=1)

        self._build_task_tab()
        self._build_strategy_tab()
        self._build_settings_tab()
        self._build_theme_tab()
        self._build_logs_tab()

    def _build_task_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # File
        file_group = QGroupBox("① 文件与任务")
        file_layout = QVBoxLayout(file_group)
        self.file_label = QLabel("尚未选择 TXT 文件")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setMinimumHeight(100)
        self.file_label.setObjectName("DropBox")
        file_btn_row = QHBoxLayout()
        self.choose_btn = QPushButton("📄 选择 TXT 文件")
        self.choose_btn.clicked.connect(self.choose_file)
        self.open_btn = QPushButton("📂 打开输出目录")
        self.open_btn.clicked.connect(self.open_output_dir)
        file_btn_row.addWidget(self.choose_btn)
        file_btn_row.addWidget(self.open_btn)
        file_btn_row.addStretch()
        file_layout.addWidget(self.file_label)
        file_layout.addLayout(file_btn_row)
        layout.addWidget(file_group)

        # Quick settings
        quick_group = QGroupBox("② 快速翻译设置")
        grid = QGridLayout(quick_group)
        self.source_combo = QComboBox()
        self.source_combo.addItem("中文 Chinese", "zh")
        self.source_combo.addItem("英文 English", "en")
        self.source_combo.addItem("日文 Japanese", "ja")
        self.source_combo.addItem("自动 auto", "auto")

        self.target_combo = QComboBox()
        self.target_combo.addItem("英文 English", "en")
        self.target_combo.addItem("中文 Chinese", "zh-CN")
        self.target_combo.addItem("日文 Japanese", "ja")

        self.chunk_spin = QSpinBox()
        self.chunk_spin.setRange(300, 4500)
        self.chunk_spin.setSingleStep(100)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 20.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setDecimals(1)
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)

        self.quick_strategy_label = QLabel("当前策略：未设置")
        self.quick_theme_label = QLabel("当前主题：未设置")
        self.quick_strategy_label.setObjectName("SmallInfo")
        self.quick_theme_label.setObjectName("SmallInfo")

        grid.addWidget(QLabel("源语言"), 0, 0)
        grid.addWidget(self.source_combo, 0, 1)
        grid.addWidget(QLabel("目标语言"), 0, 2)
        grid.addWidget(self.target_combo, 0, 3)
        grid.addWidget(QLabel("每段字符"), 1, 0)
        grid.addWidget(self.chunk_spin, 1, 1)
        grid.addWidget(QLabel("请求间隔/秒"), 1, 2)
        grid.addWidget(self.interval_spin, 1, 3)
        grid.addWidget(QLabel("失败重试"), 2, 0)
        grid.addWidget(self.retry_spin, 2, 1)
        grid.addWidget(self.quick_strategy_label, 2, 2, 1, 2)
        grid.addWidget(self.quick_theme_label, 3, 2, 1, 2)
        layout.addWidget(quick_group)

        # Control
        control_group = QGroupBox("③ 任务控制")
        control_layout = QVBoxLayout(control_group)
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶ 开始翻译")
        self.pause_btn = QPushButton("⏸ 暂停")
        self.resume_btn = QPushButton("▶ 继续")
        self.cancel_btn = QPushButton("⛔ 终止任务")
        self.reset_btn = QPushButton("🔄 重置界面")
        self.goto_strategy_btn = QPushButton("🧭 打开策略中心")
        self.goto_setting_btn = QPushButton("⚙ 打开设置中心")
        self.goto_theme_btn = QPushButton("🎨 打开主题中心")

        self.start_btn.clicked.connect(self.start_translate)
        self.pause_btn.clicked.connect(self.pause_task)
        self.resume_btn.clicked.connect(self.resume_task)
        self.cancel_btn.clicked.connect(self.cancel_task)
        self.reset_btn.clicked.connect(self.reset_ui)
        self.goto_strategy_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        self.goto_setting_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        self.goto_theme_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(3))

        for btn in [self.start_btn, self.pause_btn, self.resume_btn, self.cancel_btn, self.reset_btn]:
            btn_row.addWidget(btn)
        btn_row.addStretch()
        control_layout.addLayout(btn_row)

        nav_row = QHBoxLayout()
        nav_row.addWidget(self.goto_strategy_btn)
        nav_row.addWidget(self.goto_setting_btn)
        nav_row.addWidget(self.goto_theme_btn)
        nav_row.addStretch()
        control_layout.addLayout(nav_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("等待开始...")
        control_layout.addWidget(self.progress)

        self.eta_label = QLabel("当前进度：0 / 0    已用时间：00:00:00    预计剩余：--:--:--")
        self.eta_label.setObjectName("EtaLabel")
        control_layout.addWidget(self.eta_label)

        self.task_hint = QLabel("V5：译文会按段实时写入；暂停/终止后可通过 checkpoint.json 断点续译。日志较长时请切换到“日志中心”。")
        self.task_hint.setObjectName("SmallInfo")
        control_layout.addWidget(self.task_hint)
        layout.addWidget(control_group)

        layout.addStretch()
        self.tabs.addTab(tab, "🏠 任务主页")

    def _build_strategy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        preset_group = QGroupBox("策略预设 / 自动模式")
        preset_layout = QVBoxLayout(preset_group)
        row = QHBoxLayout()
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("稳定 API：腾讯云 → 百度 → Google → OPUS", "stable_api")
        self.strategy_combo.addItem("API 优先 + 离线兜底", "api_offline")
        self.strategy_combo.addItem("免费优先 + 离线兜底", "free_offline")
        self.strategy_combo.addItem("免费 + API + 离线兜底", "free_api_offline")
        self.strategy_combo.addItem("免费优先", "free_first")
        self.strategy_combo.addItem("离线优先", "offline_first")
        self.strategy_combo.addItem("腾讯优先", "tencent_first")
        self.strategy_combo.addItem("百度优先", "baidu_first")
        self.strategy_combo.addItem("自定义顺序", "custom")
        self.strategy_combo.currentIndexChanged.connect(self.update_strategy_description)
        self.apply_strategy_btn = QPushButton("应用当前策略")
        self.apply_strategy_btn.clicked.connect(self.apply_selected_strategy_to_manual_order)
        row.addWidget(QLabel("自动策略"))
        row.addWidget(self.strategy_combo, 1)
        row.addWidget(self.apply_strategy_btn)
        preset_layout.addLayout(row)
        self.strategy_desc_label = QLabel("")
        self.strategy_desc_label.setWordWrap(True)
        self.strategy_desc_label.setObjectName("HintLabel")
        preset_layout.addWidget(self.strategy_desc_label)

        preset_btn_row = QHBoxLayout()
        self.preset_api_offline_btn = QPushButton("API→离线")
        self.preset_free_offline_btn = QPushButton("免费→离线")
        self.preset_free_api_offline_btn = QPushButton("免费→API→离线")
        self.preset_custom_btn = QPushButton("切到自定义")
        self.preset_api_offline_btn.clicked.connect(lambda: self.select_strategy("api_offline", apply_order=True))
        self.preset_free_offline_btn.clicked.connect(lambda: self.select_strategy("free_offline", apply_order=True))
        self.preset_free_api_offline_btn.clicked.connect(lambda: self.select_strategy("free_api_offline", apply_order=True))
        self.preset_custom_btn.clicked.connect(lambda: self.select_strategy("custom", apply_order=False))
        for btn in [self.preset_api_offline_btn, self.preset_free_offline_btn, self.preset_free_api_offline_btn, self.preset_custom_btn]:
            preset_btn_row.addWidget(btn)
        preset_btn_row.addStretch()
        preset_layout.addLayout(preset_btn_row)
        layout.addWidget(preset_group)

        manual_group = QGroupBox("手动排序 / 引擎顺序")
        manual_layout = QHBoxLayout(manual_group)
        left = QVBoxLayout()
        self.engine_order_list = QListWidget()
        self.engine_order_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.engine_order_list.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.engine_order_list.setMinimumHeight(260)
        left.addWidget(QLabel("自定义顺序（custom 模式时生效）"))
        left.addWidget(self.engine_order_list)
        manual_layout.addLayout(left, 1)

        right = QVBoxLayout()
        self.move_up_btn = QPushButton("⬆ 上移")
        self.move_down_btn = QPushButton("⬇ 下移")
        self.move_top_btn = QPushButton("⏫ 置顶")
        self.move_bottom_btn = QPushButton("⏬ 置底")
        self.refresh_manual_btn = QPushButton("🔁 按启用项重建")
        self.save_strategy_btn = QPushButton("💾 保存策略顺序")
        self.move_up_btn.clicked.connect(lambda: self.move_engine_item(-1))
        self.move_down_btn.clicked.connect(lambda: self.move_engine_item(1))
        self.move_top_btn.clicked.connect(lambda: self.move_engine_item("top"))
        self.move_bottom_btn.clicked.connect(lambda: self.move_engine_item("bottom"))
        self.refresh_manual_btn.clicked.connect(self.rebuild_engine_order_list_from_enabled)
        self.save_strategy_btn.clicked.connect(self.save_config_from_ui)
        for btn in [self.move_up_btn, self.move_down_btn, self.move_top_btn, self.move_bottom_btn, self.refresh_manual_btn, self.save_strategy_btn]:
            right.addWidget(btn)
        right.addStretch()
        manual_layout.addLayout(right)
        layout.addWidget(manual_group)

        self.manual_hint = QLabel("提示：如果你选择“自定义顺序”，系统会严格按照上面列表的顺序：从上到下依次尝试。")
        self.manual_hint.setObjectName("HintLabel")
        layout.addWidget(self.manual_hint)
        layout.addStretch()
        self.tabs.addTab(tab, "🧭 策略中心")

    def _build_settings_tab(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(14)

        api_group = QGroupBox("在线翻译引擎 / API 设置")
        eng = QGridLayout(api_group)
        self.tencent_enabled = QCheckBox("启用腾讯云")
        self.tencent_id = QLineEdit()
        self.tencent_id.setPlaceholderText("Tencent SecretId")
        self.tencent_key = QLineEdit()
        self.tencent_key.setPlaceholderText("Tencent SecretKey")
        self.tencent_key.setEchoMode(QLineEdit.Password)
        self.tencent_region = QLineEdit()
        self.tencent_region.setPlaceholderText("ap-guangzhou")

        self.baidu_enabled = QCheckBox("启用百度翻译")
        self.baidu_id = QLineEdit()
        self.baidu_id.setPlaceholderText("Baidu APP ID")
        self.baidu_key = QLineEdit()
        self.baidu_key.setPlaceholderText("Baidu SecretKey")
        self.baidu_key.setEchoMode(QLineEdit.Password)

        self.google_enabled = QCheckBox("启用 Google 免费")
        self.mymemory_enabled = QCheckBox("启用 MyMemory 免费")

        eng.addWidget(self.tencent_enabled, 0, 0)
        eng.addWidget(self.tencent_id, 0, 1)
        eng.addWidget(self.tencent_key, 0, 2)
        eng.addWidget(self.tencent_region, 0, 3)
        eng.addWidget(self.baidu_enabled, 1, 0)
        eng.addWidget(self.baidu_id, 1, 1)
        eng.addWidget(self.baidu_key, 1, 2)
        eng.addWidget(self.google_enabled, 2, 0)
        eng.addWidget(self.mymemory_enabled, 2, 1)
        layout.addWidget(api_group)

        opus_group = QGroupBox("离线引擎 / OPUS-MT 设置")
        op = QGridLayout(opus_group)
        self.opus_enabled = QCheckBox("启用 OPUS-MT 本地兜底")
        self.opus_path = QLineEdit()
        self.opus_path.setPlaceholderText("OPUS-MT 模型路径，例如 G:/AI_Models/translation/opus-mt-zh-en")
        self.opus_browse_btn = QPushButton("选择模型目录")
        self.opus_browse_btn.clicked.connect(self.choose_opus_dir)
        self.opus_device = QComboBox()
        self.opus_device.addItem("自动 GPU/CPU", "auto")
        self.opus_device.addItem("强制 CPU", "cpu")
        self.opus_device.addItem("强制 CUDA", "cuda")
        op.addWidget(self.opus_enabled, 0, 0)
        op.addWidget(self.opus_path, 0, 1, 1, 2)
        op.addWidget(self.opus_browse_btn, 0, 3)
        op.addWidget(QLabel("OPUS 设备"), 1, 0)
        op.addWidget(self.opus_device, 1, 1)
        layout.addWidget(opus_group)

        general_group = QGroupBox("通用设置")
        g = QGridLayout(general_group)
        self.realtime_write_enabled = QCheckBox("实时写入译文文件")
        self.resume_enabled = QCheckBox("启用断点续译")
        self.save_cfg_btn = QPushButton("💾 保存全部设置")
        self.save_cfg_btn.clicked.connect(self.save_config_from_ui)
        self.open_logs_btn = QPushButton("📝 打开日志中心")
        self.open_logs_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(4))
        g.addWidget(QLabel("提示"), 0, 0)
        g.addWidget(QLabel("建议：在线 API 作为主力，OPUS-MT 作为离线兜底。"), 0, 1, 1, 3)
        g.addWidget(self.realtime_write_enabled, 1, 0)
        g.addWidget(self.resume_enabled, 1, 1)
        g.addWidget(self.save_cfg_btn, 2, 2)
        g.addWidget(self.open_logs_btn, 2, 3)
        layout.addWidget(general_group)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.tabs.addTab(tab, "⚙ 设置中心")

    def _build_theme_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        theme_group = QGroupBox("主题中心")
        theme_layout = QVBoxLayout(theme_group)
        row = QHBoxLayout()
        self.theme_combo = QComboBox()
        for k, v in THEMES.items():
            self.theme_combo.addItem(v["name"], k)
        self.theme_apply_btn = QPushButton("应用主题")
        self.theme_apply_btn.clicked.connect(self.apply_selected_theme)
        row.addWidget(QLabel("主题选择"))
        row.addWidget(self.theme_combo, 1)
        row.addWidget(self.theme_apply_btn)
        theme_layout.addLayout(row)

        self.theme_count_label = QLabel("已内置 60 套主题；使用下拉框选择后点击应用。")
        self.theme_count_label.setObjectName("HintLabel")
        theme_layout.addWidget(self.theme_count_label)

        self.theme_preview_label = QLabel("主题说明：不同主题只改变颜色与氛围，不影响功能。")
        self.theme_preview_label.setWordWrap(True)
        self.theme_preview_label.setObjectName("HintLabel")
        theme_layout.addWidget(self.theme_preview_label)
        layout.addWidget(theme_group)

        preview_group = QGroupBox("主题说明")
        pv = QVBoxLayout(preview_group)
        pv.addWidget(QLabel("V5 已内置 60 套主题：深色、青色、绿色、紫色、金色、灰色、玫瑰色等系列。"))
        pv.addWidget(QLabel("主题只影响界面视觉，不影响翻译策略、API 或输出文件。"))
        pv.addWidget(QLabel("当前主题会写入 config/translator_config.json，下次启动自动恢复。"))
        layout.addWidget(preview_group)
        layout.addStretch()
        self.tabs.addTab(tab, "🎨 主题中心")

    def _build_logs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        top = QHBoxLayout()
        self.clear_log_btn = QPushButton("🧹 清空日志")
        self.clear_log_btn.clicked.connect(lambda: self.log_box.clear())
        self.return_task_btn = QPushButton("↩ 返回任务主页")
        self.return_task_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        top.addWidget(self.clear_log_btn)
        top.addWidget(self.return_task_btn)
        top.addStretch()
        layout.addLayout(top)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(450)
        layout.addWidget(self.log_box, stretch=1)
        self.tabs.addTab(tab, "📝 日志中心")

    def _apply_theme(self, theme_name: str | None = None):
        if theme_name is not None:
            self.current_theme = theme_name if theme_name in THEMES else "deep_blue"
        theme = THEMES.get(self.current_theme, THEMES["deep_blue"])
        self.setStyleSheet(f"""
        QMainWindow, QWidget {{
            background: {theme['bg']};
            color: {theme['text']};
            font-family: "Microsoft YaHei", "Segoe UI";
            font-size: 14px;
        }}
        QLabel#Title {{
            color: {theme['accent']};
            font-size: 28px;
            font-weight: 800;
        }}
        QLabel#Subtitle, QLabel#SmallInfo {{
            color: {theme['subtext']};
        }}
        QLabel#HintLabel {{
            color: {theme['accent']};
            padding: 4px 2px;
        }}
        QLabel#Badge {{
            background: {theme['success_bg']};
            color: {theme['success_text']};
            border-radius: 14px;
            padding: 6px 14px;
            font-weight: 700;
        }}
        QLabel#EtaLabel {{
            color: {theme['accent']};
            font-weight: 700;
        }}
        QFrame#Line {{
            color: {theme['line']};
            background: {theme['line']};
        }}
        QTabWidget::pane {{
            border: 1px solid {theme['line']};
            border-radius: 12px;
            top: -1px;
            background: {theme['panel']};
        }}
        QTabBar::tab {{
            background: {theme['tab']};
            color: {theme['text']};
            border: 1px solid {theme['line']};
            padding: 10px 18px;
            margin-right: 6px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            min-width: 118px;
            font-weight: 700;
        }}
        QTabBar::tab:selected {{
            background: {theme['tab_active']};
            color: white;
        }}
        QTabBar::tab:hover {{
            background: {theme['accent2']};
            color: white;
        }}
        QGroupBox {{
            border: 1px solid {theme['line']};
            border-radius: 12px;
            margin-top: 12px;
            padding: 14px;
            background: {theme['panel']};
            color: {theme['subtext']};
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 8px;
        }}
        QLabel#DropBox {{
            border: 1px dashed {theme['line']};
            border-radius: 12px;
            background: {theme['bg']};
            color: {theme['subtext']};
            font-size: 15px;
        }}
        QPushButton {{
            background: {theme['input']};
            color: {theme['text']};
            border: 1px solid {theme['line']};
            border-radius: 10px;
            padding: 9px 15px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {theme['accent2']};
            color: white;
        }}
        QPushButton:disabled {{
            background: {theme['panel']};
            color: {theme['subtext']};
            border-color: {theme['line']};
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QListWidget {{
            background: {theme['input']};
            border: 1px solid {theme['line']};
            border-radius: 8px;
            padding: 7px;
            color: {theme['text']};
        }}
        QListWidget::item {{
            padding: 8px;
            margin: 3px;
            border-radius: 6px;
        }}
        QListWidget::item:selected {{
            background: {theme['accent2']};
            color: white;
        }}
        QTextEdit, QScrollArea {{
            background: {theme['bg']};
            border: 1px solid {theme['line']};
            border-radius: 10px;
            color: {theme['text']};
        }}
        QTextEdit {{
            padding: 10px;
            font-family: Consolas, "Microsoft YaHei";
            font-size: 13px;
        }}
        QProgressBar {{
            background: {theme['bg']};
            border: 1px solid {theme['line']};
            border-radius: 10px;
            height: 26px;
            color: white;
            text-align: center;
            font-weight: 800;
        }}
        QProgressBar::chunk {{
            background: {theme['accent']};
            border-radius: 10px;
        }}
        """)
        self.quick_theme_label.setText(f"当前主题：{theme['name']}")
        self.theme_preview_label.setText(f"已选择主题：{theme['name']}。你可以在这里即时切换整体 UI 颜色。")

    def _load_config_to_ui(self):
        cfg = self.cfg
        self.chunk_spin.setValue(int(cfg.get("max_chars_per_chunk", 1800)))
        self.interval_spin.setValue(float(cfg.get("request_interval", 0.8)))
        self.retry_spin.setValue(int(cfg.get("retry_times", 3)))

        # strategy
        strategy = cfg.get("strategy", "stable_api")
        for i in range(self.strategy_combo.count()):
            if self.strategy_combo.itemData(i) == strategy:
                self.strategy_combo.setCurrentIndex(i)
                break

        # theme
        theme_name = cfg.get("theme_name", "deep_blue")
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme_name:
                self.theme_combo.setCurrentIndex(i)
                break

        t = cfg.get("tencent", {})
        self.tencent_enabled.setChecked(bool(t.get("enabled", False)))
        self.tencent_id.setText(t.get("secret_id", ""))
        self.tencent_key.setText(t.get("secret_key", ""))
        self.tencent_region.setText(t.get("region", "ap-guangzhou"))

        b = cfg.get("baidu", {})
        self.baidu_enabled.setChecked(bool(b.get("enabled", False)))
        self.baidu_id.setText(b.get("app_id", ""))
        self.baidu_key.setText(b.get("secret_key", ""))

        self.google_enabled.setChecked(bool(cfg.get("google_free", {}).get("enabled", True)))
        self.mymemory_enabled.setChecked(bool(cfg.get("mymemory", {}).get("enabled", False)))

        o = cfg.get("opus_mt", {})
        self.opus_enabled.setChecked(bool(o.get("enabled", True)))
        self.opus_path.setText(o.get("model_path", "G:/AI_Models/translation/opus-mt-zh-en"))
        dev = o.get("device", "auto")
        for i in range(self.opus_device.count()):
            if self.opus_device.itemData(i) == dev:
                self.opus_device.setCurrentIndex(i)
                break

        self.realtime_write_enabled.setChecked(bool(cfg.get("realtime_write", True)))
        self.resume_enabled.setChecked(bool(cfg.get("resume_enabled", True)))

        self.rebuild_engine_order_list_from_config()
        self.update_strategy_description()

    def get_current_engine_order(self) -> list[str]:
        order = []
        for i in range(self.engine_order_list.count()):
            item = self.engine_order_list.item(i)
            order.append(item.data(Qt.UserRole))
        return order

    def rebuild_engine_order_list_from_config(self):
        order = list(self.cfg.get("engine_order", []))
        if not order:
            order = ["tencent", "baidu", "google_free", "opus_mt", "mymemory"]
        self.engine_order_list.clear()
        used = set()
        for key in order:
            if key in ENGINE_LABELS and key not in used:
                self.add_engine_list_item(key)
                used.add(key)
        for key in ENGINE_LABELS:
            if key not in used:
                self.add_engine_list_item(key)

    def rebuild_engine_order_list_from_enabled(self):
        enabled = []
        if self.tencent_enabled.isChecked():
            enabled.append("tencent")
        if self.baidu_enabled.isChecked():
            enabled.append("baidu")
        if self.google_enabled.isChecked():
            enabled.append("google_free")
        if self.opus_enabled.isChecked():
            enabled.append("opus_mt")
        if self.mymemory_enabled.isChecked():
            enabled.append("mymemory")
        if not enabled:
            enabled = ["google_free", "opus_mt"]

        self.engine_order_list.clear()
        for key in enabled:
            self.add_engine_list_item(key)
        self.add_log("已根据当前启用项重建手动排序列表", "success")

    def add_engine_list_item(self, key: str):
        item = QListWidgetItem(f"{ENGINE_LABELS.get(key, key)}  ({key})")
        item.setData(Qt.UserRole, key)
        self.engine_order_list.addItem(item)

    def move_engine_item(self, direction):
        row = self.engine_order_list.currentRow()
        if row < 0:
            return
        item = self.engine_order_list.takeItem(row)
        if direction == -1:
            new_row = max(0, row - 1)
        elif direction == 1:
            new_row = min(self.engine_order_list.count(), row + 1)
        elif direction == "top":
            new_row = 0
        else:
            new_row = self.engine_order_list.count()
        self.engine_order_list.insertItem(new_row, item)
        self.engine_order_list.setCurrentRow(new_row)

    def select_strategy(self, strategy_id: str, apply_order: bool = False):
        for i in range(self.strategy_combo.count()):
            if self.strategy_combo.itemData(i) == strategy_id:
                self.strategy_combo.setCurrentIndex(i)
                break
        if apply_order:
            self.apply_selected_strategy_to_manual_order()

    def apply_selected_strategy_to_manual_order(self):
        strategy_id = self.strategy_combo.currentData()
        preset_orders = {
            "stable_api": ["tencent", "baidu", "google_free", "opus_mt", "mymemory"],
            "api_offline": ["tencent", "baidu", "opus_mt", "google_free", "mymemory"],
            "free_first": ["google_free", "mymemory", "opus_mt", "tencent", "baidu"],
            "free_offline": ["google_free", "mymemory", "opus_mt", "tencent", "baidu"],
            "free_api_offline": ["google_free", "mymemory", "tencent", "baidu", "opus_mt"],
            "offline_first": ["opus_mt", "google_free", "mymemory", "tencent", "baidu"],
            "tencent_first": ["tencent", "baidu", "opus_mt", "google_free", "mymemory"],
            "baidu_first": ["baidu", "tencent", "opus_mt", "google_free", "mymemory"],
        }
        order = preset_orders.get(strategy_id)
        if order:
            self.engine_order_list.clear()
            for key in order:
                self.add_engine_list_item(key)
            self.add_log(f"已将手动排序列表应用为：{self.strategy_combo.currentText()}", "success")
        self.update_strategy_description()

    def update_strategy_description(self):
        strategy_id = self.strategy_combo.currentData()
        self.strategy_desc_label.setText(STRATEGY_DESCRIPTIONS.get(strategy_id, ""))
        self.quick_strategy_label.setText(f"当前策略：{self.strategy_combo.currentText()}")

    def apply_selected_theme(self):
        theme_key = self.theme_combo.currentData()
        self._apply_theme(theme_key)
        self.cfg["theme_name"] = theme_key
        save_config(self.cfg)
        self.add_log(f"主题已切换为：{THEMES[theme_key]['name']}", "success")

    def select_theme(self, theme_key: str):
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == theme_key:
                self.theme_combo.setCurrentIndex(i)
                break
        self.apply_selected_theme()

    def save_config_from_ui(self):
        self.cfg["max_chars_per_chunk"] = self.chunk_spin.value()
        self.cfg["request_interval"] = self.interval_spin.value()
        self.cfg["retry_times"] = self.retry_spin.value()
        self.cfg["strategy"] = self.strategy_combo.currentData()
        self.cfg["theme_name"] = self.theme_combo.currentData()
        self.cfg["realtime_write"] = self.realtime_write_enabled.isChecked()
        self.cfg["resume_enabled"] = self.resume_enabled.isChecked()

        self.cfg["tencent"] = {
            "enabled": self.tencent_enabled.isChecked(),
            "secret_id": self.tencent_id.text().strip(),
            "secret_key": self.tencent_key.text().strip(),
            "region": self.tencent_region.text().strip() or "ap-guangzhou",
        }
        self.cfg["baidu"] = {
            "enabled": self.baidu_enabled.isChecked(),
            "app_id": self.baidu_id.text().strip(),
            "secret_key": self.baidu_key.text().strip(),
        }
        self.cfg["google_free"]["enabled"] = self.google_enabled.isChecked()
        self.cfg["mymemory"]["enabled"] = self.mymemory_enabled.isChecked()
        self.cfg["opus_mt"] = {
            "enabled": self.opus_enabled.isChecked(),
            "model_path": self.opus_path.text().strip(),
            "device": self.opus_device.currentData(),
            "max_new_tokens": 900,
            "offline_only": False,
        }

        order = self.get_current_engine_order()
        self.cfg["engine_order"] = order or ["google_free", "opus_mt"]

        save_config(self.cfg)
        self._apply_theme(self.cfg["theme_name"])
        self.add_log("设置中心、策略中心、主题中心配置已保存", "success")

    def choose_opus_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择 OPUS-MT 模型目录", self.opus_path.text().strip() or "")
        if folder:
            self.opus_path.setText(folder)
            self.add_log(f"已选择 OPUS-MT 模型目录：{folder}", "success")

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择小说 TXT 文件",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.input_file = file_path
            p = Path(file_path)
            size_mb = p.stat().st_size / 1024 / 1024
            self.file_label.setText(f"📄 {p.name}\n{size_mb:.2f} MB")
            self.add_log(f"已选择文件：{file_path}", "success")

    def start_translate(self):
        if not self.input_file:
            QMessageBox.warning(self, "未选择文件", "请先选择 TXT 文件。")
            return

        self.save_config_from_ui()
        source = self.source_combo.currentData()
        target = self.target_combo.currentData()
        self.worker = TranslateWorker(self.input_file, self.cfg, source, target, self)
        self.worker.log_signal.connect(self.add_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.failed_signal.connect(self.on_failed)
        self.worker.start()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.add_log("翻译线程已启动，界面不会卡死", "start")

    def pause_task(self):
        if self.worker:
            self.worker.pause()

    def resume_task(self):
        if self.worker:
            self.worker.resume_task()

    def cancel_task(self):
        if self.worker:
            self.worker.cancel()

    def open_output_dir(self):
        try:
            open_dir(self.last_output_dir)
            self.add_log(f"已打开输出目录：{self.last_output_dir}", "success")
        except Exception as e:
            self.add_log(f"打开输出目录失败：{e}", "error")

    def reset_ui(self):
        self.progress.setValue(0)
        self.progress.setFormat("等待开始...")
        self.eta_label.setText("当前进度：0 / 0    已用时间：00:00:00    预计剩余：--:--:--")
        self.log_box.clear()
        self.add_log("界面已重置", "info")

    def add_log(self, msg: str, level: str = "info"):
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "start": "🚀",
            "pause": "⏸️",
            "resume": "▶️",
            "cancel": "⛔",
            "engine": "🌐",
            "switch": "🔁",
        }
        now = datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {icons.get(level, 'ℹ️')} {msg}"
        self.log_box.append(line)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def update_progress(self, done: int, total: int, percent: float, elapsed: float, eta: float):
        self.progress.setValue(int(percent))
        self.progress.setFormat(f"{done} / {total} 段    {percent:.1f}%")
        self.eta_label.setText(
            f"当前进度：{done} / {total}    已用时间：{fmt_time(elapsed)}    预计剩余：{fmt_time(eta)}"
        )

        theme = THEMES.get(self.current_theme, THEMES["deep_blue"])
        if percent < 30:
            color = "#ff5f56"
        elif percent < 70:
            color = theme["accent"]
        else:
            color = "#24df61"

        self.progress.setStyleSheet(f"""
        QProgressBar {{
            background: {theme['bg']};
            border: 1px solid {theme['line']};
            border-radius: 10px;
            height: 26px;
            color: white;
            text-align: center;
            font-weight: 800;
        }}
        QProgressBar::chunk {{
            background: {color};
            border-radius: 10px;
        }}
        """)

    def on_finished(self, output_dir: str, msg: str):
        self.last_output_dir = output_dir
        self.add_log(msg, "success")
        self.start_btn.setEnabled(True)

    def on_failed(self, error: str):
        self.add_log(f"任务失败：{error}", "error")
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "任务失败", error)

"""
AI 分析 + 66 主题 + 66 配色包
- 66 套主题骨架（Bento Grid 风格描述）
- 66 套配色方案
- PySide6 可直接调用的主题应用器
- AI 分析页面结构定义
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
        QTextEdit, QFrame, QScrollArea, QGridLayout, QSizePolicy
    )
    from PySide6.QtCore import Qt
    QT_OK = True
except Exception:
    QT_OK = False
    QWidget = object
    QVBoxLayout = QHBoxLayout = QLabel = QPushButton = QTabWidget = QTextEdit = QFrame = QScrollArea = QGridLayout = QSizePolicy = object
    class Qt:
        AlignCenter = 0

@dataclass
class PaletteSpec:
    name: str
    bg: str
    surface: str
    accent: str
    text: str
    muted: str = "#8A8A8A"
    border: str = "#3A3A3A"
    glass: str = "rgba(255,255,255,0.08)"

@dataclass
class ThemeSpec:
    name: str
    slug: str
    description: str
    archetype: str
    suggested_palette: str
    layout_mode: str = "bento"
    nav_style: str = "capsule"
    card_style: str = "glass"
    table_style: str = "soft"
    radius: int = 24
    blur: int = 18
    shadow_strength: int = 24
    wallpaper_enabled: bool = False
    notes: Dict[str, Any] = field(default_factory=dict)

PALETTES_66: Dict[str, PaletteSpec] = {
    "典雅圣堂": PaletteSpec("典雅圣堂", "#2A2420", "#D4B16A", "#E8E2D9", "#F5E7C5", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "浪漫星空": PaletteSpec("浪漫星空", "#0F172A", "#1E293B", "#64748B", "#C7D2FE", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "复古国风": PaletteSpec("复古国风", "#EAE2D6", "#121212", "#433D3B", "#8C7D74", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "二次元": PaletteSpec("二次元", "#F6F0F8", "#785F99", "#B186B1", "#D9C2D9", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "朋克": PaletteSpec("朋克", "#030712", "#111827", "#7E22CE", "#EC4899", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "金属质感": PaletteSpec("金属质感", "#1A1A1D", "#28282B", "#5C5C62", "#A1A1AA", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "音浪花海": PaletteSpec("音浪花海", "#F9FBFB", "#8FB9B5", "#D1E7E5", "#E6F3F2", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "空中花园": PaletteSpec("空中花园", "#E8EDE7", "#3D5944", "#8A9A7E", "#B8C4A7", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "天空之城": PaletteSpec("天空之城", "#F0F4FF", "#2A3D5F", "#7B92D6", "#BFD0FF", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "海底世界": PaletteSpec("海底世界", "#0F1C2D", "#1F3A5C", "#4A7296", "#D6E4F0", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "世纪城堡": PaletteSpec("世纪城堡", "#E9E2D9", "#3A2F2B", "#7D6958", "#B0A08F", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "雾境松间": PaletteSpec("雾境松间", "#F2F4F3", "#4A5F58", "#8A9A93", "#B2C1BC", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "琉璃月夜": PaletteSpec("琉璃月夜", "#0F172A", "#1E293B", "#64748B", "#A5B4FC", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "琥珀暮光": PaletteSpec("琥珀暮光", "#F6EADF", "#B86F48", "#D99B79", "#FFB98F", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "青釉瓷韵": PaletteSpec("青釉瓷韵", "#F4F6F5", "#3B656E", "#91B1B8", "#C5D8DD", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "银翼幻空": PaletteSpec("银翼幻空", "#F8FAFC", "#4A5568", "#94A3B8", "#CBD5E1", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "紫藤花境": PaletteSpec("紫藤花境", "#F3EEF7", "#6D4B8C", "#B196C7", "#D9C6E6", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "赤金战铠": PaletteSpec("赤金战铠", "#2D2721", "#A13C3C", "#D4AF37", "#E6C15C", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "星砂海岸": PaletteSpec("星砂海岸", "#F5F7FA", "#6B9AC4", "#E8D2B8", "#F0E2CF", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "黑晶奢石": PaletteSpec("黑晶奢石", "#1A1A1A", "#0D0D0D", "#404040", "#B3B3B3", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "绯梦绮想": PaletteSpec("绯梦绮想", "#F9F2F4", "#B55A6F", "#E1B3C0", "#F2D8DF", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "苍岭雪峰": PaletteSpec("苍岭雪峰", "#F4F7F9", "#35424A", "#8C9FAE", "#BCC9D4", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "鎏光暗域": PaletteSpec("鎏光暗域", "#121212", "#1A1A1D", "#C6A870", "#E5C98E", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "紫晶王座": PaletteSpec("紫晶王座", "#F0EAF5", "#4B2F5D", "#916EAF", "#C5B0D9", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "落日熔金": PaletteSpec("落日熔金", "#FFF4E6", "#E9724C", "#FFC166", "#FFDAA3", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "烟雨江南": PaletteSpec("烟雨江南", "#F0F2F3", "#6B7F87", "#B0BEC5", "#D0D9DF", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "古铜岁月": PaletteSpec("古铜岁月", "#E5E0D9", "#8C6A4D", "#4B3B2B", "#B99673", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "冰晶幻城": PaletteSpec("冰晶幻城", "#F4FAFF", "#6BACD1", "#B7D9ED", "#E0F0FF", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "绯墨山河": PaletteSpec("绯墨山河", "#EAE3DF", "#8B2626", "#2D2A2E", "#C05656", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "星辰王座": PaletteSpec("星辰王座", "#0F111F", "#1A1E36", "#6C63FF", "#E0E4FF", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "白金轻奢": PaletteSpec("白金轻奢", "#FFFFFF", "#F5F5F5", "#D4AF37", "#333333", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "黑银奢石": PaletteSpec("黑银奢石", "#121212", "#2A2A2A", "#A6A6A6", "#E0E0E0", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "雾灰雅棕": PaletteSpec("雾灰雅棕", "#F3EDE5", "#D3C7B8", "#A69080", "#5E4C3E", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "莫兰迪灰粉": PaletteSpec("莫兰迪灰粉", "#E8D8D2", "#D3B8AF", "#B48C84", "#7A5F5A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "静谧雾霾蓝": PaletteSpec("静谧雾霾蓝", "#F1F5F9", "#CBD5E1", "#94A3B8", "#475569", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "青瓷雅绿": PaletteSpec("青瓷雅绿", "#F0F7F4", "#C8E2D9", "#8FB9A8", "#4A6F62", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "烟紫柔调": PaletteSpec("烟紫柔调", "#F4F0F8", "#D7C8E2", "#B196C7", "#7A5C99", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "琥珀焦糖": PaletteSpec("琥珀焦糖", "#F7E9D7", "#E4C1A1", "#B87F54", "#6D4B38", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "暗夜鎏金": PaletteSpec("暗夜鎏金", "#1A1A1D", "#2D2A32", "#C6A870", "#F3E9D9", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "冰川冷白": PaletteSpec("冰川冷白", "#F9FBFC", "#E2E8F0", "#CBD5E1", "#94A3B8", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "奶咖温柔": PaletteSpec("奶咖温柔", "#FFF8F0", "#F2E5D7", "#D9C3B0", "#A68D7A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "墨黑极简": PaletteSpec("墨黑极简", "#0A0A0A", "#222222", "#555555", "#EEEEEE", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "雾紫灰调": PaletteSpec("雾紫灰调", "#F1EFF6", "#D4CDF0", "#A696C5", "#6B5B93", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "松石蓝绿": PaletteSpec("松石蓝绿", "#EDF7F8", "#B4D6D9", "#7AA7A6", "#3D696A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "赤陶复古": PaletteSpec("赤陶复古", "#F6E6DA", "#E2B89C", "#B86F54", "#7A3E2B", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "银灰科技": PaletteSpec("银灰科技", "#F7F8FA", "#D1D5DB", "#9CA3AF", "#4B5563", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "柔粉奶白": PaletteSpec("柔粉奶白", "#FFF5F7", "#FCE4EC", "#F2BED1", "#E094A7", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "森林深谧": PaletteSpec("森林深谧", "#EFF4EF", "#B1C7B2", "#708C72", "#3A4D3C", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "落日柔橙": PaletteSpec("落日柔橙", "#FFF0E0", "#FFD6A5", "#FDAB6F", "#E87451", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "深海静谧": PaletteSpec("深海静谧", "#F0F7FF", "#BFD7EA", "#7B92A8", "#2D3A4A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "灰粉豆沙": PaletteSpec("灰粉豆沙", "#F1E6E4", "#D9C3C2", "#B48D8F", "#7A575A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "雾蓝清冷": PaletteSpec("雾蓝清冷", "#F4F7FA", "#D4E0ED", "#94A7C0", "#506480", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "古铜做旧": PaletteSpec("古铜做旧", "#EAE2D9", "#B8A18C", "#8C6A4D", "#4B3B2B", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "奶绿清新": PaletteSpec("奶绿清新", "#F5F9F0", "#E0ECCF", "#BFD2AA", "#8DA372", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "紫晶贵族": PaletteSpec("紫晶贵族", "#EFEAF5", "#CFC0E2", "#916EAF", "#4B2F5D", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "炭黑质感": PaletteSpec("炭黑质感", "#1E1E1E", "#333333", "#666666", "#CCCCCC", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "雾棕大地": PaletteSpec("雾棕大地", "#F1EAE4", "#D9CEC1", "#A68F7D", "#6D5A4A", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "柔灰薄荷": PaletteSpec("柔灰薄荷", "#F0F7F5", "#D1E7E5", "#8FB9B5", "#5A8A87", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "暖灰极简": PaletteSpec("暖灰极简", "#F8F5F0", "#E5E0D9", "#B8B0A8", "#7A7269", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "月光银白": PaletteSpec("月光银白", "#F2F3F7", "#D1D5E0", "#9EA4B8", "#525A70", "#6B7280", "#CBD5E1", "rgba(255,255,255,0.55)"),
    "哲风玻璃": PaletteSpec("哲风玻璃", "#111217", "#252833", "#6C63FF", "#E7C98E", "#9FD3FF", "#4A5568", "rgba(255,255,255,0.06)"),
    "深空紫晶": PaletteSpec("深空紫晶", "#141222", "#2A2340", "#A188E6", "#E7E4FF", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "墨黑冰蓝": PaletteSpec("墨黑冰蓝", "#0F1419", "#1C2833", "#55C6FF", "#E8F4FF", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "炭灰雾棕": PaletteSpec("炭灰雾棕", "#1A1918", "#2D2724", "#C8A98E", "#F0EAE4", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "暗夜松石": PaletteSpec("暗夜松石", "#0F1716", "#1C2927", "#64B5B2", "#E4F3F0", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
    "黑银商务": PaletteSpec("黑银商务", "#121212", "#232323", "#D4D4D4", "#F5F5F5", "#A0A0A0", "#4B5563", "rgba(255,255,255,0.08)"),
}

THEMES_66: Dict[str, ThemeSpec] = {
    "极简主义风格": ThemeSpec("极简主义风格", "minimal_1", "大量留白、低干扰、中性灰阶和细边界。", "minimal", "典雅圣堂", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "大胆现代": ThemeSpec("大胆现代", "modern_2", "高对比色块、大胆标题和清晰卡片层次。", "modern", "浪漫星空", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "优雅复古风格": ThemeSpec("优雅复古风格", "vintage_3", "米色纸张、棕红旧印刷、复古衬线。", "vintage", "复古国风", "bento", "capsule", "paper", "soft", 22, 16, 18, False),
    "未来科技风格": ThemeSpec("未来科技风格", "future_4", "深色背景、霓虹高亮、科技 HUD 信息层。", "future", "二次元", "bento", "capsule", "glass", "soft", 22, 16, 30, False),
    "斯堪的纳维亚风格": ThemeSpec("斯堪的纳维亚风格", "scandi_5", "纯白、浅灰蓝、原木气质、克制留白。", "scandi", "朋克", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "艺术装饰风格": ThemeSpec("艺术装饰风格", "artdeco_6", "黑金对称、装饰字体、金属边框。", "artdeco", "金属质感", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "日式极简风格": ThemeSpec("日式极简风格", "wabi_7", "朴素不完美、淡墨、柔和留白。", "wabi", "音浪花海", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "后现代解构风格": ThemeSpec("后现代解构风格", "deconstruct_8", "不规则切分、倾斜文字、重叠层。", "deconstruct", "空中花园", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "朋克风格": ThemeSpec("朋克风格", "punk_9", "粗糙剪贴、胶带、强烈对比。", "punk", "天空之城", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "英伦摇滚风格": ThemeSpec("英伦摇滚风格", "britrock_10", "做旧英伦、复古棕红、摇滚感。", "britrock", "海底世界", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "黑金属风格": ThemeSpec("黑金属风格", "metal_11", "压抑黑灰、锋利细节、金属边缘。", "metal", "世纪城堡", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "孟菲斯风格": ThemeSpec("孟菲斯风格", "memphis_12", "亮粉青黄、几何碰撞、活泼节奏。", "memphis", "雾境松间", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "赛博朋克风格": ThemeSpec("赛博朋克风格", "cyber_13", "深夜都市、霓虹粉蓝、发光边界。", "cyber", "琉璃月夜", "bento", "capsule", "glass", "soft", 22, 16, 18, False),
    "波普艺术风格": ThemeSpec("波普艺术风格", "pop_14", "红黄蓝、黑色轮廓、漫画平面感。", "pop", "琥珀暮光", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "瑞士解构风格": ThemeSpec("瑞士解构风格", "swiss_15", "严谨网格基础上的故意破坏。", "swiss", "青釉瓷韵", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "蒸汽波美学": ThemeSpec("蒸汽波美学", "vapor_16", "粉紫蓝渐变、怀旧未来主义。", "vapor", "银翼幻空", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "新表现主义风格": ThemeSpec("新表现主义风格", "expression_17", "不协调高能色彩、情绪笔触。", "expression", "紫藤花境", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "极端极简主义": ThemeSpec("极端极简主义", "ultra_minimal_18", "极端留白、黑白灰、弱装饰。", "ultra_minimal", "赤金战铠", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "新未来主义": ThemeSpec("新未来主义", "neo_future_19", "流线曲面、有机几何、动态感。", "neo_future", "星砂海岸", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "超现实主义拼贴": ThemeSpec("超现实主义拼贴", "surreal_20", "拼贴反常组合、艺术幻想。", "surreal", "黑晶奢石", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "新巴洛克数字风格": ThemeSpec("新巴洛克数字风格", "baroque_21", "华丽数字卷饰、浮雕和层叠。", "baroque", "绯梦绮想", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "液态数字形态主义": ThemeSpec("液态数字形态主义", "liquid_22", "液态气泡、半透明渐变、流动感。", "liquid", "苍岭雪峰", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "超感官极简主义": ThemeSpec("超感官极简主义", "sensory_23", "表面极简、细腻纹理和触觉暗示。", "sensory", "鎏光暗域", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "表现主义数据可视化": ThemeSpec("表现主义数据可视化", "dataviz_24", "表达式数据块、图形和笔触结合。", "dataviz", "紫晶王座", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "维多利亚风格": ThemeSpec("维多利亚风格", "victorian_25", "维多利亚排版和纸张装饰。", "victorian", "落日熔金", "bento", "capsule", "paper", "soft", 22, 16, 18, False),
    "包豪斯风格": ThemeSpec("包豪斯风格", "bauhaus_26", "基础几何、原色功能主义。", "bauhaus", "烟雨江南", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "构成主义风格": ThemeSpec("构成主义风格", "construct_27", "对角线结构、革命性张力。", "construct", "古铜岁月", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "孟菲斯风格加强版": ThemeSpec("孟菲斯风格加强版", "memphis_28", "亮粉青黄、几何碰撞、活泼节奏。", "memphis", "冰晶幻城", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "德国表现主义": ThemeSpec("德国表现主义", "expression_dark_29", "深蓝黑戏剧氛围、浓烈情感。", "expression_dark", "绯墨山河", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "新拟物主义": ThemeSpec("新拟物主义", "neumorphism_30", "柔软浮雕、浅阴影、拟物轻感。", "neumorphism", "星辰王座", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "玻璃态设计": ThemeSpec("玻璃态设计", "glass_31", "背景模糊、半透毛玻璃、亮边。", "glass", "白金轻奢", "bento", "capsule", "glass", "soft", 22, 16, 30, False),
    "扁平化2.0": ThemeSpec("扁平化2.0", "flat_32", "简洁纯平、少阴影、轻渐变。", "flat", "黑银奢石", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "苹果设计语言": ThemeSpec("苹果设计语言", "apple_33", "精密对齐、高级留白、极简细节。", "apple", "雾灰雅棕", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "Material You": ThemeSpec("Material You", "material_34", "壁纸取色、圆润、动态明亮。", "material", "莫兰迪灰粉", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "Fluent设计": ThemeSpec("Fluent设计", "fluent_35", "微软式材质、光效与深度。", "fluent", "静谧雾霾蓝", "bento", "capsule", "glass", "soft", 22, 16, 18, False),
    "暗黑模式": ThemeSpec("暗黑模式", "dark_36", "暗黑背景、清爽浅字、护眼。", "dark", "青瓷雅绿", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "像素艺术": ThemeSpec("像素艺术", "pixel_37", "8-bit 像素块、有限调色板。", "pixel", "烟紫柔调", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "有机设计": ThemeSpec("有机设计", "organic_38", "自然曲线、环保色调、不规则形。", "organic", "琥珀焦糖", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "3D等距风格": ThemeSpec("3D等距风格", "isometric_39", "等距深度、3D 卡片和体块。", "isometric", "暗夜鎏金", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "霓虹灯效果": ThemeSpec("霓虹灯效果", "neon_40", "发光边缘、夜景气氛。", "neon", "冰川冷白", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "日出日落渐变": ThemeSpec("日出日落渐变", "sunset_41", "橙粉紫渐变、温暖明亮。", "sunset", "奶咖温柔", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "纸张质感": ThemeSpec("纸张质感", "paper_42", "纸张纹理、柔阴影、阅读友好。", "paper", "墨黑极简", "bento", "capsule", "paper", "soft", 22, 16, 18, False),
    "克莱因蓝": ThemeSpec("克莱因蓝", "klein_43", "高饱和深蓝、艺术冲击。", "klein", "雾紫灰调", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "日系插画风格": ThemeSpec("日系插画风格", "illustration_44", "日系插画、柔和配色、细线。", "illustration", "松石蓝绿", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "科幻界面": ThemeSpec("科幻界面", "sciui_45", "科幻仪表、网格线、全息感。", "sciui", "赤陶复古", "bento", "capsule", "glass", "soft", 22, 16, 18, False),
    "儿童风格": ThemeSpec("儿童风格", "kids_46", "高明度、圆润、轻松可爱。", "kids", "银灰科技", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "中国传统风格": ThemeSpec("中国传统风格", "chinese_47", "红金、水墨、书法、传统纹样。", "chinese", "柔粉奶白", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "水彩风格": ThemeSpec("水彩风格", "watercolor_48", "透明叠色、柔和边缘和纹理。", "watercolor", "森林深谧", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "印刷风格": ThemeSpec("印刷风格", "print_49", "重文字、字号层级、版式感。", "print", "落日柔橙", "bento", "editorial", "soft", "soft", 22, 16, 18, False),
    "手绘风格": ThemeSpec("手绘风格", "handdrawn_50", "手绘线条、轻微不完美。", "handdrawn", "深海静谧", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "电影海报风格": ThemeSpec("电影海报风格", "poster_51", "戏剧性色彩、海报式主视觉。", "poster", "灰粉豆沙", "bento", "editorial", "soft", "soft", 22, 16, 18, False),
    "杂志风格": ThemeSpec("杂志风格", "magazine_52", "杂志式栏目、多栏图文。", "magazine", "雾蓝清冷", "bento", "editorial", "soft", "soft", 22, 16, 18, False),
    "复古游戏": ThemeSpec("复古游戏", "retro_game_53", "像素、CRT 怀旧、游戏感。", "retro_game", "古铜做旧", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "社交媒体卡片": ThemeSpec("社交媒体卡片", "social_54", "社交卡片、头像、互动按钮。", "social", "奶绿清新", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "电子商务卡片": ThemeSpec("电子商务卡片", "commerce_55", "产品卡片、价格和转化按钮。", "commerce", "紫晶贵族", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "天气应用风格": ThemeSpec("天气应用风格", "weather_56", "天气渐变、状态图标、温度感。", "weather", "炭黑质感", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "音乐应用风格": ThemeSpec("音乐应用风格", "music_57", "深色专辑墙、播放条和控制器。", "music", "雾棕大地", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "美食博客风格": ThemeSpec("美食博客风格", "food_58", "温暖食欲色、精致图文。", "food", "柔灰薄荷", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "旅行应用风格": ThemeSpec("旅行应用风格", "travel_59", "地图元素、探索感和照片。", "travel", "暖灰极简", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "健康应用风格": ThemeSpec("健康应用风格", "health_60", "清新色、数据卡、健康进度。", "health", "月光银白", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "哲风壁纸风格版": ThemeSpec("哲风壁纸风格版", "zhefeng_61", "暗调壁纸、毛玻璃、大圆角、轻奢社区感。", "zhefeng", "哲风玻璃", "bento", "capsule", "glass", "soft", 28, 24, 30, True),
    "黑曜商务舱": ThemeSpec("黑曜商务舱", "business_62", "黑曜商务、稳重专业、细金属边。", "business", "黑银商务", "bento", "capsule", "glass", "soft", 22, 16, 30, False),
    "云端极昼": ThemeSpec("云端极昼", "light_63", "高亮留白、云端轻透、柔和卡片。", "light", "月光银白", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "国潮霓裳": ThemeSpec("国潮霓裳", "guochao_64", "国潮图纹、霓裳配色、现代中式。", "guochao", "绯墨山河", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "电影暗房": ThemeSpec("电影暗房", "cinema_65", "暗房灯光、电影胶片感、叙事卡片。", "cinema", "黑晶奢石", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
    "医疗洁境": ThemeSpec("医疗洁境", "medical_66", "洁净浅色、温和蓝绿、医疗信息卡。", "medical", "柔灰薄荷", "bento", "capsule", "soft", "soft", 22, 16, 18, False),
}


AI_ANALYSIS_SCHEMA: Dict[str, Dict[str, List[str]]] = {
    "单词分析": {
        "tabs": ["助记", "词根", "词源", "搭配", "同义词", "形近词", "替换", "单词新解", "派生词"],
        "fields": ["核心义", "常见搭配", "高频短语", "例句", "易混词", "备注"]
    },
    "句子分析": {
        "tabs": ["语法分析", "搭配积累", "难词解释", "升级表达", "改写", "跟读提示"],
        "fields": ["原句", "中文", "句子主干", "从句结构", "重点短语", "难词解释", "升级表达", "跟读要点"]
    },
    "长文分析": {
        "tabs": ["原文", "解析", "笔记", "单词训练", "跟读", "阅读模式"],
        "fields": ["标题", "原文", "摘要", "重点段落", "重点词", "重点搭配", "难句拆解", "笔记"]
    },
    "口语分析": {
        "tabs": ["自由对话", "热点话题", "系统录音", "跟读对比", "AI点评", "历史记录"],
        "fields": ["话题", "提示词", "建议表达", "发音提醒", "替换表达", "点评"]
    },
    "学习统计": {
        "tabs": ["今日学习", "复习计划", "打卡统计", "历史记录", "AI建议"],
        "fields": ["新词数量", "复习数量", "学习时长", "掌握单词", "薄弱项", "建议"]
    },
}



def list_palette_names() -> List[str]:
    return list(PALETTES_66.keys())


def list_theme_names() -> List[str]:
    return list(THEMES_66.keys())


def _hex_to_rgb(value: str):
    value = (value or '').strip().lstrip('#')
    if len(value) == 3:
        value = ''.join(ch * 2 for ch in value)
    if len(value) != 6:
        return 255, 255, 255
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def _is_light(hex_color: str) -> bool:
    r, g, b = _hex_to_rgb(hex_color)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return lum >= 160


def _mix(c1: str, c2: str, ratio: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 * (1 - ratio) + r2 * ratio)
    g = int(g1 * (1 - ratio) + g2 * ratio)
    b = int(b1 * (1 - ratio) + b2 * ratio)
    return f"#{r:02X}{g:02X}{b:02X}"


def build_qss(theme_name: str, palette_name: Optional[str] = None, background_image: str = "") -> str:
    theme = THEMES_66.get(theme_name, next(iter(THEMES_66.values())))
    palette = PALETTES_66.get(palette_name or theme.suggested_palette, PALETTES_66[theme.suggested_palette])
    dark_mode = not _is_light(palette.bg)
    border_alpha = 0.18 if dark_mode else 0.12
    panel_bg = palette.surface if theme.card_style != 'glass' else _rgba(_mix(palette.bg, '#FFFFFF' if dark_mode else '#000000', 0.08 if dark_mode else 0.02), 0.92 if dark_mode else 0.88)
    chip_bg = _rgba(palette.accent, 0.14 if dark_mode else 0.18)
    chip_border = _rgba(palette.accent, 0.42 if dark_mode else 0.32)
    header_bg = _rgba(_mix(palette.surface, palette.bg, 0.55), 0.98)
    input_bg = _rgba(_mix(palette.surface, '#FFFFFF' if dark_mode else '#000000', 0.06 if dark_mode else 0.02), 0.96)
    muted = palette.muted if palette.muted else (_mix(palette.text, palette.bg, 0.45 if dark_mode else 0.35))

    if theme.archetype == 'zhefeng':
        wall_rule = f"background-image:url('{background_image}'); background-position:center; background-repeat:no-repeat;" if background_image else ""
        return f"""
        QMainWindow, QWidget#centralFrame {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #141518, stop:0.5 #1d1f25, stop:1 #17181d);
            color: #E7D19A;
            {wall_rule}
        }}
        QWidget {{ color: #D8E7FF; }}
        QFrame#glassCard, QGroupBox#glassCard {{
            background: rgba(35, 38, 48, 0.72);
            border: 1px solid rgba(231, 201, 142, 0.22);
            border-radius: {theme.radius}px;
            padding: 10px;
        }}
        QFrame#softCard, QGroupBox#softCard, QGroupBox {{
            background: rgba(29, 31, 39, 0.88);
            border: 1px solid rgba(159, 211, 255, 0.18);
            border-radius: {max(14, theme.radius-6)}px;
            padding: 8px;
        }}
        QGroupBox::title {{
            color: #E7C98E;
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }}
        QLabel {{ color: #DCE8F6; }}
        QLabel#heroTitle, QLabel#cardTitle {{ color: #F2CF8F; font-weight: 800; }}
        QLabel#heroSub, QLabel#muted {{ color: #AFC8E8; }}
        QTabWidget::pane {{ border: none; background: transparent; }}
        QTabBar::tab {{
            background: rgba(36, 40, 50, 0.78);
            color: #CFE2FA;
            border: 1px solid rgba(159, 211, 255, 0.22);
            border-radius: 16px;
            padding: 10px 18px;
            margin-right: 8px;
        }}
        QTabBar::tab:selected {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #3b4051, stop:1 #2b3042);
            color: #F4D18E;
            border: 1px solid rgba(244, 209, 142, 0.45);
        }}
        QPushButton {{
            background: rgba(58, 64, 81, 0.82);
            color: #F2D39C;
            border: 1px solid rgba(244, 209, 142, 0.28);
            border-radius: 16px;
            padding: 8px 16px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: rgba(85, 93, 116, 0.88);
            color: #FFF1CE;
        }}
        QPushButton:pressed {{ background: rgba(44, 49, 63, 0.92); }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
            background: rgba(28, 32, 42, 0.94);
            color: #FFF0CC;
            border: 1px solid rgba(159, 211, 255, 0.20);
            border-radius: 14px;
            padding: 8px 10px;
            selection-background-color: rgba(108, 99, 255, 0.45);
        }}
        QComboBox QAbstractItemView {{
            background: rgba(27, 30, 38, 0.98);
            color: #EED2A0;
            border: 1px solid rgba(159, 211, 255, 0.22);
            selection-background-color: rgba(108, 99, 255, 0.35);
        }}
        QTableWidget {{
            background: rgba(24, 27, 35, 0.96);
            alternate-background-color: rgba(31, 35, 46, 0.96);
            color: #E8F0FB;
            border: 1px solid rgba(159, 211, 255, 0.18);
            gridline-color: rgba(159, 211, 255, 0.14);
            border-radius: 14px;
        }}
        QHeaderView::section {{
            background: rgba(37, 41, 51, 0.95);
            color: #F0CD8B;
            border: none;
            border-bottom: 1px solid rgba(244, 209, 142, 0.18);
            padding: 8px;
            font-weight: 700;
        }}
        QTableWidget::item:selected {{
            background: rgba(108, 99, 255, 0.28);
            color: #FFF0CC;
        }}
        QMenu {{
            background: rgba(28, 31, 40, 0.98);
            color: #EAD8AC;
            border: 1px solid rgba(159, 211, 255, 0.18);
        }}
        QMenu::item:selected {{ background: rgba(108, 99, 255, 0.28); }}
        """

    if theme.card_style == 'paper':
        panel_bg = _rgba('#FFFFFF', 0.96)
        chip_bg = _rgba(palette.accent, 0.10)
        header_bg = _rgba(_mix(palette.surface, '#FFFFFF', 0.6), 0.98)
        input_bg = _rgba('#FFFFFF', 0.98)
    elif theme.card_style == 'glass':
        panel_bg = _rgba(palette.surface, 0.66 if dark_mode else 0.78)
    elif theme.card_style == 'soft':
        panel_bg = _rgba(palette.surface, 0.94)

    if theme.nav_style == 'editorial':
        nav = f"""
        QTabBar::tab {{ background: transparent; color: {palette.text}; border: none; border-bottom: 2px solid transparent; padding: 10px 14px; margin-right: 12px; font-weight: 600; }}
        QTabBar::tab:selected {{ color: {palette.accent}; border-bottom: 3px solid {palette.accent}; }}
        """
    else:
        nav = f"""
        QTabBar::tab {{ background: {chip_bg}; color: {palette.text}; border: 1px solid {chip_border}; border-radius: {max(12, theme.radius-10)}px; padding: 10px 18px; margin-right: 8px; }}
        QTabBar::tab:selected {{ background: {palette.accent}; color: {'#111111' if _is_light(palette.accent) else '#F7FAFC'}; font-weight: 700; }}
        """

    if theme.table_style == 'grid':
        gridline = _rgba(palette.border, 0.4)
        header_weight = '800'
    elif theme.table_style == 'soft':
        gridline = _rgba(palette.border, 0.18)
        header_weight = '700'
    else:
        gridline = 'transparent'
        header_weight = '700'

    main_bg = f"""
    QMainWindow, QWidget#centralFrame {{ background: {palette.bg}; color: {palette.text}; }}
    QWidget {{ color: {palette.text}; }}
    """
    glass_card = f"""
    QFrame#glassCard, QGroupBox#glassCard {{ background: {panel_bg}; border: 1px solid {_rgba(palette.border, border_alpha)}; border-radius: {theme.radius}px; padding: 10px; }}
    """
    soft_card = f"""
    QFrame#softCard, QGroupBox#softCard, QGroupBox {{ background: {panel_bg if theme.card_style != 'paper' else _rgba('#FFFFFF',0.95)}; border: 1px solid {_rgba(palette.border, border_alpha)}; border-radius: {max(14, theme.radius-8)}px; padding: 8px; }}
    QGroupBox::title {{ color: {palette.accent}; subcontrol-origin: margin; left: 12px; padding: 0 8px; }}
    """
    buttons = f"""
    QPushButton {{ background: {palette.accent}; color: {'#111111' if _is_light(palette.accent) else '#F7FAFC'}; border: 1px solid {_rgba(palette.border, 0.25)}; border-radius: {max(12, theme.radius-12)}px; padding: 8px 16px; font-weight: 700; }}
    QPushButton:hover {{ background: {_mix(palette.accent, '#FFFFFF' if dark_mode else '#000000', 0.12)}; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{ background: {input_bg}; color: {palette.text}; border: 1px solid {_rgba(palette.border, border_alpha)}; border-radius: {max(12, theme.radius-12)}px; padding: 8px 10px; selection-background-color: {_rgba(palette.accent,0.35)}; }}
    QComboBox QAbstractItemView {{ background: {header_bg}; color: {palette.text}; border: 1px solid {_rgba(palette.border, border_alpha)}; selection-background-color: {_rgba(palette.accent,0.28)}; }}
    """
    tables = f"""
    QTableWidget {{ background: {panel_bg}; alternate-background-color: {_rgba(palette.bg,0.92)}; color: {palette.text}; border: 1px solid {_rgba(palette.border, border_alpha)}; gridline-color: {gridline}; border-radius: {max(12, theme.radius-12)}px; }}
    QHeaderView::section {{ background: {header_bg}; color: {palette.text}; border: none; border-bottom: 1px solid {_rgba(palette.border, border_alpha)}; padding: 8px; font-weight: {header_weight}; }}
    QTableWidget::item:selected {{ background: {_rgba(palette.accent, 0.25 if dark_mode else 0.18)}; color: {palette.text}; }}
    """
    labels = f"""
    QLabel#heroTitle {{ font-size: 30px; font-weight: 800; color: {palette.text}; }}
    QLabel#heroSub {{ color: {muted}; font-size: 14px; }}
    QLabel#cardTitle {{ font-size: 20px; font-weight: 800; color: {palette.text}; }}
    QLabel#muted {{ color: {muted}; }}
    """
    return "\n".join([main_bg, glass_card, soft_card, nav, buttons, tables, labels])


def apply_theme(widget, theme_name: str, palette_name: Optional[str] = None, background_image: str = ""):
    if not QT_OK:
        return
    widget.setStyleSheet(build_qss(theme_name, palette_name, background_image))

if QT_OK:
    class AIAnalysisWorkbench(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 18, 18, 18)
            root.setSpacing(16)

            title_wrap = QFrame()
            title_wrap.setObjectName("glassCard")
            title_l = QVBoxLayout(title_wrap)
            hero = QLabel("AI分析")
            hero.setObjectName("heroTitle")
            sub = QLabel("单词 / 句子 / 长文 / 口语 / 学习统计")
            sub.setObjectName("heroSub")
            title_l.addWidget(hero)
            title_l.addWidget(sub)
            root.addWidget(title_wrap)

            self.top_tabs = QTabWidget()
            for section, cfg in AI_ANALYSIS_SCHEMA.items():
                page = QWidget()
                page_l = QVBoxLayout(page)
                page_l.setContentsMargins(8, 8, 8, 8)
                page_l.setSpacing(12)

                chip_bar = QHBoxLayout()
                for tab_name in cfg["tabs"]:
                    btn = QPushButton(tab_name)
                    btn.setObjectName("chipBtn")
                    btn.setFlat(False)
                    chip_bar.addWidget(btn)
                chip_bar.addStretch()
                page_l.addLayout(chip_bar)

                editor = QTextEdit()
                editor.setPlaceholderText(f"在这里输入或粘贴要分析的内容：{{section}}")
                page_l.addWidget(editor)

                cards = QGridLayout()
                cards.setSpacing(12)
                for i, field_name in enumerate(cfg["fields"]):
                    card = QFrame()
                    card.setObjectName("glassCard")
                    cl = QVBoxLayout(card)
                    title = QLabel(field_name)
                    title.setObjectName("cardTitle")
                    value = QTextEdit()
                    value.setPlaceholderText(field_name)
                    value.setMinimumHeight(120)
                    cl.addWidget(title)
                    cl.addWidget(value)
                    cards.addWidget(card, i // 2, i % 2)
                page_l.addLayout(cards)
                self.top_tabs.addTab(page, section)
            root.addWidget(self.top_tabs, 1)

    class ThemePreviewGallery(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            root = QVBoxLayout(self)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(12)
            title = QLabel("66主题 / 66配色")
            title.setObjectName("heroTitle")
            root.addWidget(title)

            self.theme_tabs = QTabWidget()
            root.addWidget(self.theme_tabs, 1)

            for name, spec in THEMES_66.items():
                page = QWidget()
                p_l = QVBoxLayout(page)
                p_l.setContentsMargins(12, 12, 12, 12)
                hero = QFrame()
                hero.setObjectName("glassCard")
                hl = QVBoxLayout(hero)
                t = QLabel(name)
                t.setObjectName("cardTitle")
                d = QLabel(spec.description)
                d.setWordWrap(True)
                d.setObjectName("muted")
                hl.addWidget(t)
                hl.addWidget(d)

                grid = QGridLayout()
                for i in range(6):
                    card = QFrame()
                    card.setObjectName("glassCard" if spec.card_style == "glass" else "softCard")
                    cl = QVBoxLayout(card)
                    cl.addWidget(QLabel(f"模块 {{i+1}}"))
                    body = QLabel("Bento Grid 模块预览")
                    body.setWordWrap(True)
                    body.setObjectName("muted")
                    cl.addWidget(body)
                    grid.addWidget(card, i // 3, i % 3)

                p_l.addWidget(hero)
                p_l.addLayout(grid)
                self.theme_tabs.addTab(page, name)

else:
    class AIAnalysisWorkbench:
        pass
    class ThemePreviewGallery:
        pass

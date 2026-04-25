from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

DEFAULT_FONT_FAMILIES = [
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Segoe UI",
    "Arial",
    "Tahoma",
    "Verdana",
    "Calibri",
    "Georgia",
    "Times New Roman",
    "Consolas",
]


@dataclass
class FontStyleConfig:
    family: str = "Microsoft YaHei UI"
    size: int = 12
    bold: bool = False
    italic: bool = False
    color: str = "#EAECEF"

    def to_qfont(self) -> QFont:
        font = QFont(self.family, self.size)
        font.setBold(self.bold)
        font.setItalic(self.italic)
        return font


class FontRoleEditor(QWidget):
    def __init__(self, role_name: str, config: FontStyleConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.role_name = role_name
        self.config = FontStyleConfig(**asdict(config))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.family_combo = QComboBox()
        self.family_combo.addItems(DEFAULT_FONT_FAMILIES)
        if self.config.family not in DEFAULT_FONT_FAMILIES:
            self.family_combo.addItem(self.config.family)
        self.family_combo.setCurrentText(self.config.family)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 48)
        self.size_spin.setValue(self.config.size)

        self.bold_combo = QComboBox()
        self.bold_combo.addItems(["常规", "加粗"])
        self.bold_combo.setCurrentIndex(1 if self.config.bold else 0)

        self.italic_combo = QComboBox()
        self.italic_combo.addItems(["常规", "斜体"])
        self.italic_combo.setCurrentIndex(1 if self.config.italic else 0)

        self.color_btn = QPushButton("颜色")
        self._apply_btn_color(self.config.color)
        self.color_btn.clicked.connect(self.pick_color)

        layout.addWidget(QLabel(role_name))
        layout.addWidget(self.family_combo, 2)
        layout.addWidget(QLabel("字号"))
        layout.addWidget(self.size_spin)
        layout.addWidget(self.bold_combo)
        layout.addWidget(self.italic_combo)
        layout.addWidget(self.color_btn)

    def _apply_btn_color(self, color: str):
        self.color_btn.setStyleSheet(
            f"QPushButton {{ background:{color}; color:#111; border-radius:8px; padding:4px 10px; }}"
        )

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.config.color), self, f"选择颜色 - {self.role_name}")
        if c.isValid():
            self.config.color = c.name()
            self._apply_btn_color(self.config.color)

    def get_config(self) -> FontStyleConfig:
        return FontStyleConfig(
            family=self.family_combo.currentText(),
            size=self.size_spin.value(),
            bold=self.bold_combo.currentIndex() == 1,
            italic=self.italic_combo.currentIndex() == 1,
            color=self.config.color,
        )


class LocalFontSettingsDialog(QDialog):
    """
    用法：
        dlg = LocalFontSettingsDialog(current_font_settings, self)
        if dlg.exec():
            new_settings = dlg.get_all_settings()
    """
    def __init__(self, current_settings: Optional[Dict[str, Dict[str, Dict]]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("本地模式字体设置")
        self.resize(980, 720)

        self._settings = self._merge_defaults(current_settings or {})
        self._editors: Dict[str, Dict[str, FontRoleEditor]] = {}

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self._build_tab("search_options", "搜索选项", [
            ("section_title", "分区标题"),
            ("form_label", "标签文字"),
            ("input_text", "输入框 / 下拉框"),
            ("result_title", "结果标题"),
            ("result_body", "结果正文"),
            ("result_meta", "结果附加信息"),
            ("hint_text", "提示文字"),
        ])
        self._build_tab("playlist_options", "播放列表选项", [
            ("section_title", "分区标题"),
            ("toolbar_text", "工具栏按钮"),
            ("item_title", "条目标题"),
            ("item_body", "条目正文"),
            ("item_meta", "条目附加信息"),
            ("status_text", "状态文字"),
            ("hint_text", "提示文字"),
        ])
        self._build_tab("play_options", "播放选项", [
            ("section_title", "分区标题"),
            ("topbar_text", "顶部按钮区"),
            ("bottombar_text", "底部按钮区"),
            ("subtitle_en", "英文字幕"),
            ("subtitle_zh", "中文字幕"),
            ("study_panel", "底部学习区"),
            ("hint_text", "提示文字"),
        ])

        preview_box = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText(
            "搜索选项：关键词 / 结果列表 / 提示文字\n"
            "播放列表选项：列表条目 / 状态 / 工具栏\n"
            "播放选项：顶部按钮 / 底部按钮 / 字幕 / 学习区"
        )
        preview_layout.addWidget(self.preview_text)
        root.addWidget(preview_box)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        restore_btn = btns.button(QDialogButtonBox.RestoreDefaults)
        restore_btn.clicked.connect(self.restore_defaults)
        root.addWidget(btns)

    def _merge_defaults(self, given: Dict[str, Dict[str, Dict]]) -> Dict[str, Dict[str, FontStyleConfig]]:
        defaults = {
            "search_options": {
                "section_title": FontStyleConfig(size=14, bold=True, color="#F7F8FA"),
                "form_label": FontStyleConfig(size=12, color="#CDD6E0"),
                "input_text": FontStyleConfig(size=12, color="#EAECEF"),
                "result_title": FontStyleConfig(size=13, bold=True, color="#FFFFFF"),
                "result_body": FontStyleConfig(size=12, color="#EAECEF"),
                "result_meta": FontStyleConfig(size=11, color="#9FB0C4"),
                "hint_text": FontStyleConfig(size=11, italic=True, color="#8FA1B6"),
            },
            "playlist_options": {
                "section_title": FontStyleConfig(size=14, bold=True, color="#F7F8FA"),
                "toolbar_text": FontStyleConfig(size=12, color="#EAECEF"),
                "item_title": FontStyleConfig(size=13, bold=True, color="#FFFFFF"),
                "item_body": FontStyleConfig(size=12, color="#EAECEF"),
                "item_meta": FontStyleConfig(size=11, color="#9FB0C4"),
                "status_text": FontStyleConfig(size=11, color="#9DD0A8"),
                "hint_text": FontStyleConfig(size=11, italic=True, color="#8FA1B6"),
            },
            "play_options": {
                "section_title": FontStyleConfig(size=14, bold=True, color="#F7F8FA"),
                "topbar_text": FontStyleConfig(size=12, color="#EAECEF"),
                "bottombar_text": FontStyleConfig(size=12, color="#EAECEF"),
                "subtitle_en": FontStyleConfig(size=22, bold=True, color="#FFFFFF"),
                "subtitle_zh": FontStyleConfig(size=20, color="#8CF2FF"),
                "study_panel": FontStyleConfig(size=12, color="#EAECEF"),
                "hint_text": FontStyleConfig(size=11, italic=True, color="#8FA1B6"),
            },
        }
        merged: Dict[str, Dict[str, FontStyleConfig]] = {}
        for section, role_map in defaults.items():
            merged[section] = {}
            for role, default_cfg in role_map.items():
                src = given.get(section, {}).get(role, {})
                if isinstance(src, FontStyleConfig):
                    merged[section][role] = src
                else:
                    merged[section][role] = FontStyleConfig(**{**asdict(default_cfg), **src})
        return merged

    def _build_tab(self, section_key: str, title: str, roles: List[tuple]):
        page = QWidget()
        layout = QVBoxLayout(page)

        grp = QGroupBox(title)
        grid = QGridLayout(grp)
        self._editors[section_key] = {}
        for row, (role_key, role_label) in enumerate(roles):
            editor = FontRoleEditor(role_label, self._settings[section_key][role_key])
            self._editors[section_key][role_key] = editor
            grid.addWidget(editor, row, 0)
        layout.addWidget(grp)
        layout.addStretch(1)
        self.tabs.addTab(page, title)

    def restore_defaults(self):
        self._settings = self._merge_defaults({})
        self.close()
        fresh = LocalFontSettingsDialog({}, self.parent())
        fresh.exec()

    def get_all_settings(self) -> Dict[str, Dict[str, Dict]]:
        out: Dict[str, Dict[str, Dict]] = {}
        for section, editors in self._editors.items():
            out[section] = {}
            for role, editor in editors.items():
                out[section][role] = asdict(editor.get_config())
        return out


class LocalFontSettingsMixin:
    """
    集成方式：

    1) MainWindow.__init__ 里增加：
        self.local_font_settings = self.config.get("local_font_settings", {})

    2) 在三个菜单里分别增加入口：
        act = menu.addAction("字体设置")
        act.triggered.connect(lambda: self.open_local_font_settings("search_options"))

    3) 在需要的地方调用 apply_local_font_settings_to_widgets()
    """

    def ensure_local_font_settings(self):
        if not hasattr(self, "local_font_settings") or not self.local_font_settings:
            dlg = LocalFontSettingsDialog({})
            self.local_font_settings = dlg.get_all_settings()

    def open_local_font_settings(self, default_tab: str = "search_options"):
        self.ensure_local_font_settings()
        dlg = LocalFontSettingsDialog(self.local_font_settings, self)
        tab_map = {
            "search_options": 0,
            "playlist_options": 1,
            "play_options": 2,
        }
        dlg.tabs.setCurrentIndex(tab_map.get(default_tab, 0))
        if dlg.exec():
            self.local_font_settings = dlg.get_all_settings()
            if hasattr(self, "config") and isinstance(self.config, dict):
                self.config["local_font_settings"] = self.local_font_settings
                save = getattr(self, "save_config", None)
                if callable(save):
                    save()
            self.apply_local_font_settings_to_widgets()

    def _apply_cfg_to_widget(self, widget: QWidget, cfg: Dict):
        if widget is None:
            return
        font_cfg = FontStyleConfig(**cfg)
        widget.setFont(font_cfg.to_qfont())
        existing = widget.styleSheet() or ""
        color_css = f"color: {font_cfg.color};"
        widget.setStyleSheet(existing + ("\n" if existing else "") + color_css)

    def apply_local_font_settings_to_widgets(self):
        """
        按你现有对象名尽量匹配。
        如果某些控件名和你主程序不一样，就把这里的 getattr 名称改成你自己的。
        """
        self.ensure_local_font_settings()
        s = self.local_font_settings

        # ===== 搜索选项 =====
        search_targets = {
            "section_title": [getattr(self, "search_group", None), getattr(self, "local_search_group", None)],
            "form_label": [getattr(self, "search_path_label", None), getattr(self, "search_keyword_label", None), getattr(self, "result_count_label", None)],
            "input_text": [getattr(self, "search_edit", None), getattr(self, "search_limit_spin", None), getattr(self, "search_sort_combo", None)],
            "result_title": [getattr(self, "search_result_table", None), getattr(self, "search_result_list", None)],
            "result_body": [getattr(self, "search_result_table", None), getattr(self, "search_result_list", None)],
            "result_meta": [getattr(self, "search_status_label", None)],
            "hint_text": [getattr(self, "search_hint_label", None)],
        }
        for role, widgets in search_targets.items():
            for w in widgets:
                self._apply_cfg_to_widget(w, s["search_options"][role])

        # ===== 播放列表选项 =====
        playlist_targets = {
            "section_title": [getattr(self, "playlist_group", None)],
            "toolbar_text": [getattr(self, "playlist_options_btn", None), getattr(self, "playlist_play_btn", None)],
            "item_title": [getattr(self, "playlist_table", None), getattr(self, "playlist_list", None)],
            "item_body": [getattr(self, "playlist_table", None), getattr(self, "playlist_list", None)],
            "item_meta": [getattr(self, "playlist_status_label", None)],
            "status_text": [getattr(self, "playlist_mode_label", None)],
            "hint_text": [getattr(self, "playlist_hint_label", None)],
        }
        for role, widgets in playlist_targets.items():
            for w in widgets:
                self._apply_cfg_to_widget(w, s["playlist_options"][role])

        # ===== 播放选项 =====
        play_targets = {
            "section_title": [getattr(self, "player_group", None)],
            "topbar_text": [getattr(self, "play_options_btn", None), getattr(self, "top_toolbar", None)],
            "bottombar_text": [getattr(self, "bottom_toolbar", None), getattr(self, "play_pause_btn", None)],
            "subtitle_en": [getattr(self, "subtitle_en_label", None), getattr(self, "video_overlay_en", None)],
            "subtitle_zh": [getattr(self, "subtitle_zh_label", None), getattr(self, "video_overlay_zh", None)],
            "study_panel": [getattr(self, "study_panel", None), getattr(self, "learning_panel", None)],
            "hint_text": [getattr(self, "play_hint_label", None)],
        }
        for role, widgets in play_targets.items():
            for w in widgets:
                self._apply_cfg_to_widget(w, s["play_options"][role])


__all__ = [
    "FontStyleConfig",
    "LocalFontSettingsDialog",
    "LocalFontSettingsMixin",
]

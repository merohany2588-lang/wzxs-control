from __future__ import annotations
import sys
from pathlib import Path
from ai_analysis_theme_pack_66 import (
    QT_OK, ThemePreviewGallery, AIAnalysisWorkbench,
    apply_theme, list_palette_names, list_theme_names, THEMES_66
)

if not QT_OK:
    print("当前环境没有 PySide6，无法运行演示。")
    raise SystemExit(0)

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTabWidget

class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI分析 + 66主题 + 66配色 演示")
        self.resize(1680, 980)
        central = QWidget()
        central.setObjectName("centralFrame")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("主题"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list_theme_names())
        toolbar.addWidget(self.theme_combo)
        toolbar.addWidget(QLabel("配色"))
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(list_palette_names())
        toolbar.addWidget(self.palette_combo)
        toolbar.addStretch()
        root.addLayout(toolbar)

        self.tabs = QTabWidget()
        self.ai_panel = AIAnalysisWorkbench()
        self.theme_panel = ThemePreviewGallery()
        self.tabs.addTab(self.ai_panel, "AI分析")
        self.tabs.addTab(self.theme_panel, "主题预览")
        root.addWidget(self.tabs, 1)

        self.theme_combo.currentTextChanged.connect(self.refresh_theme)
        self.palette_combo.currentTextChanged.connect(self.refresh_theme)

        self.theme_combo.setCurrentText("哲风壁纸风格版")
        self.palette_combo.setCurrentText(THEMES_66["哲风壁纸风格版"].suggested_palette)
        self.refresh_theme()

    def refresh_theme(self):
        apply_theme(self, self.theme_combo.currentText(), self.palette_combo.currentText())

def main():
    app = QApplication(sys.argv)
    win = DemoWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

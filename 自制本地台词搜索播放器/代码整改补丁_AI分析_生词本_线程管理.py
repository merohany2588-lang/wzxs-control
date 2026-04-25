from __future__ import annotations

"""
代码整改补丁：AI分析 / 生词本重构 / 线程统一管理

用途：
1. 替换当前“AI互动”弱页面，升级为“AI分析”工作台
2. 生词本从“只能存单词”升级为“支持单词 / 短语 / 句子 + 分类 + CRUD + 搜索”
3. 消灭 QThread: Destroyed while thread is still running

说明：
- 这是可直接并入现有 PySide6 主工程的模块，不依赖 canmore / notebook。
- 你需要在主窗口中创建下面三个对象：
    * WorkerRegistry(self)
    * StudyItemStore(vocab_json_path)
    * AIAnalysisPanel(...)
- 如果你已有 AI 请求函数，只要把 provider_callback 传进去即可。
"""

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
import json
import threading
import time

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTextEdit, QPlainTextEdit, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QColorDialog, QFontDialog,
    QSplitter, QFormLayout, QDialog, QDialogButtonBox
)


# =========================
# 一、统一学习项数据结构
# =========================

ENTRY_TYPES = ("word", "phrase", "sentence")
DEFAULT_CATEGORIES = ["未分类", "口语", "写作", "听力", "阅读", "台词", "文章", "自定义"]


@dataclass
class StudyItem:
    id: str
    entry_type: str              # word / phrase / sentence
    content: str                 # 原文内容
    translation: str = ""
    note: str = ""
    category: str = "未分类"
    source: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    review_state: str = "new"   # new / reviewing / mastered
    tags: List[str] = field(default_factory=list)
    style: Dict[str, Any] = field(default_factory=lambda: {
        "fg": "#2d3748",
        "bg": "#ffffff",
        "font_family": "Microsoft YaHei UI",
        "font_size": 12,
        "bold": False,
        "italic": False,
    })

    def touch(self) -> None:
        self.updated_at = time.time()


class StudyItemStore:
    """本地 JSON 持久化，支持新增 / 删 / 改 / 搜索 / 分类。"""

    def __init__(self, json_path: str | Path):
        self.path = Path(json_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.items: List[StudyItem] = []
        self.load()

    def load(self) -> None:
        with self._lock:
            if not self.path.exists():
                self.items = []
                return
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self.items = [StudyItem(**x) for x in raw]
            except Exception:
                self.items = []

    def save(self) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps([asdict(x) for x in self.items], ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

    def all(self) -> List[StudyItem]:
        return list(self.items)

    def add(self, item: StudyItem) -> None:
        self.items.append(item)
        self.save()

    def upsert(self, item: StudyItem) -> None:
        for i, old in enumerate(self.items):
            if old.id == item.id:
                item.touch()
                self.items[i] = item
                self.save()
                return
        self.add(item)

    def remove(self, item_id: str) -> None:
        self.items = [x for x in self.items if x.id != item_id]
        self.save()

    def get(self, item_id: str) -> Optional[StudyItem]:
        for x in self.items:
            if x.id == item_id:
                return x
        return None

    def search(
        self,
        keyword: str = "",
        entry_type: str = "",
        category: str = "",
        review_state: str = "",
    ) -> List[StudyItem]:
        kw = (keyword or "").strip().lower()
        results = []
        for x in self.items:
            if entry_type and x.entry_type != entry_type:
                continue
            if category and x.category != category:
                continue
            if review_state and x.review_state != review_state:
                continue
            haystack = "\n".join([
                x.content or "",
                x.translation or "",
                x.note or "",
                x.source or "",
                " ".join(x.tags or []),
            ]).lower()
            if kw and kw not in haystack:
                continue
            results.append(x)
        results.sort(key=lambda z: z.updated_at, reverse=True)
        return results


# =========================
# 二、线程统一管理
# =========================

class WorkerRegistry(QObject):
    """统一托管 QThread，防止线程对象被销毁时仍在运行。"""

    worker_started = Signal(str)
    worker_finished = Signal(str)

    def __init__(self, owner: QObject):
        super().__init__(owner)
        self._owner = owner
        self._workers: Dict[int, QThread] = {}

    def track(self, worker: QThread, name: str = "worker") -> QThread:
        key = id(worker)
        self._workers[key] = worker
        self.worker_started.emit(name)

        def _cleanup() -> None:
            self._workers.pop(key, None)
            self.worker_finished.emit(name)
            try:
                worker.deleteLater()
            except Exception:
                pass

        worker.finished.connect(_cleanup)
        return worker

    def stop_all(self, timeout_ms: int = 4000) -> None:
        for worker in list(self._workers.values()):
            try:
                if hasattr(worker, "cancel"):
                    worker.cancel()  # type: ignore[attr-defined]
            except Exception:
                pass
            try:
                worker.quit()
            except Exception:
                pass
            try:
                worker.wait(timeout_ms)
            except Exception:
                pass
        self._workers.clear()


# =========================
# 三、AI 分析数据与工作台
# =========================

class AIAnalyzeWorker(QThread):
    success = Signal(dict)
    failed = Signal(str)

    def __init__(self, provider_callback: Callable[[str, Dict[str, Any]], Dict[str, Any]], mode: str, payload: Dict[str, Any]):
        super().__init__()
        self.provider_callback = provider_callback
        self.mode = mode
        self.payload = payload
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            if self._cancelled:
                return
            data = self.provider_callback(self.mode, self.payload)
            if self._cancelled:
                return
            self.success.emit(data)
        except Exception as e:
            self.failed.emit(str(e))


class StudyItemEditor(QDialog):
    def __init__(self, parent: QWidget | None = None, item: Optional[StudyItem] = None):
        super().__init__(parent)
        self.setWindowTitle("学习项编辑")
        self.resize(640, 480)
        self.item = item

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.type_combo = QComboBox(); self.type_combo.addItems(list(ENTRY_TYPES))
        self.category_combo = QComboBox(); self.category_combo.addItems(DEFAULT_CATEGORIES)
        self.content_edit = QTextEdit()
        self.translation_edit = QTextEdit()
        self.note_edit = QTextEdit()
        self.source_edit = QLineEdit()
        self.state_combo = QComboBox(); self.state_combo.addItems(["new", "reviewing", "mastered"])
        self.tags_edit = QLineEdit()
        form.addRow("类型", self.type_combo)
        form.addRow("分类", self.category_combo)
        form.addRow("内容", self.content_edit)
        form.addRow("翻译", self.translation_edit)
        form.addRow("备注", self.note_edit)
        form.addRow("来源", self.source_edit)
        form.addRow("复习状态", self.state_combo)
        form.addRow("标签(空格分隔)", self.tags_edit)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        if item:
            self.type_combo.setCurrentText(item.entry_type)
            self.category_combo.setCurrentText(item.category)
            self.content_edit.setPlainText(item.content)
            self.translation_edit.setPlainText(item.translation)
            self.note_edit.setPlainText(item.note)
            self.source_edit.setText(item.source)
            self.state_combo.setCurrentText(item.review_state)
            self.tags_edit.setText(" ".join(item.tags or []))

    def build_item(self) -> StudyItem:
        item = self.item or StudyItem(id=f"si_{int(time.time()*1000)}", entry_type="word", content="")
        item.entry_type = self.type_combo.currentText()
        item.category = self.category_combo.currentText()
        item.content = self.content_edit.toPlainText().strip()
        item.translation = self.translation_edit.toPlainText().strip()
        item.note = self.note_edit.toPlainText().strip()
        item.source = self.source_edit.text().strip()
        item.review_state = self.state_combo.currentText()
        item.tags = [x for x in self.tags_edit.text().split() if x.strip()]
        item.touch()
        return item


class StyleDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, style: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("样式面板")
        self.resize(420, 220)
        self.style = dict(style or {})

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.fg_btn = QPushButton(self.style.get("fg", "#2d3748"))
        self.bg_btn = QPushButton(self.style.get("bg", "#ffffff"))
        self.font_btn = QPushButton(self.style.get("font_family", "Microsoft YaHei UI"))
        self.font_size_combo = QComboBox()
        for x in range(10, 33):
            self.font_size_combo.addItem(str(x), x)
        idx = self.font_size_combo.findData(self.style.get("font_size", 12))
        if idx >= 0:
            self.font_size_combo.setCurrentIndex(idx)

        self.fg_btn.clicked.connect(self.pick_fg)
        self.bg_btn.clicked.connect(self.pick_bg)
        self.font_btn.clicked.connect(self.pick_font)

        form.addRow("文字颜色", self.fg_btn)
        form.addRow("背景颜色", self.bg_btn)
        form.addRow("字体", self.font_btn)
        form.addRow("字号", self.font_size_combo)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def pick_fg(self):
        color = QColorDialog.getColor(QColor(self.fg_btn.text()), self, "选择文字颜色")
        if color.isValid():
            self.fg_btn.setText(color.name())

    def pick_bg(self):
        color = QColorDialog.getColor(QColor(self.bg_btn.text()), self, "选择背景颜色")
        if color.isValid():
            self.bg_btn.setText(color.name())

    def pick_font(self):
        ok, font = QFontDialog.getFont(QFont(self.font_btn.text(), 12), self, "选择字体")
        if ok:
            self.font_btn.setText(font.family())

    def get_style(self) -> Dict[str, Any]:
        return {
            "fg": self.fg_btn.text(),
            "bg": self.bg_btn.text(),
            "font_family": self.font_btn.text(),
            "font_size": self.font_size_combo.currentData(),
        }


class AIAnalysisPanel(QWidget):
    request_started = Signal(str)
    request_finished = Signal(str)

    def __init__(
        self,
        provider_callback: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        worker_registry: WorkerRegistry,
        study_store: Optional[StudyItemStore] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.provider_callback = provider_callback
        self.worker_registry = worker_registry
        self.study_store = study_store
        self.current_payload: Dict[str, Any] = {}
        self.current_mode: str = "word"

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入单词 / 短语 / 句子 / 长文")
        self.analyze_word_btn = QPushButton("分析单词")
        self.analyze_sentence_btn = QPushButton("分析句子")
        self.analyze_article_btn = QPushButton("分析长文")
        self.add_to_vocab_btn = QPushButton("加入生词本")
        self.add_to_note_btn = QPushButton("加入笔记")
        for b in [self.analyze_word_btn, self.analyze_sentence_btn, self.analyze_article_btn, self.add_to_vocab_btn, self.add_to_note_btn]:
            top.addWidget(b)
        top.addStretch()
        root.addLayout(top)
        root.addWidget(self.input_edit, 1)

        self.tabs = QTabWidget()
        self.word_tab = self._make_text_tab(["核心义", "助记", "词根", "词源", "搭配", "同义词", "形近词", "替换", "单词新解", "派生词"])
        self.sent_tab = self._make_text_tab(["语法分析", "句子主干", "从句结构", "搭配积累", "难词解释", "升级表达", "同义改写", "跟读提示"])
        self.article_tab = self._make_text_tab(["摘要", "段落主旨", "重点词汇", "重点搭配", "难句拆解", "笔记"])
        self.tabs.addTab(self.word_tab["widget"], "单词分析")
        self.tabs.addTab(self.sent_tab["widget"], "句子分析")
        self.tabs.addTab(self.article_tab["widget"], "长文分析")
        root.addWidget(self.tabs, 2)

        self.analyze_word_btn.clicked.connect(self.analyze_word)
        self.analyze_sentence_btn.clicked.connect(self.analyze_sentence)
        self.analyze_article_btn.clicked.connect(self.analyze_article)
        self.add_to_vocab_btn.clicked.connect(self.add_current_to_store)
        self.add_to_note_btn.clicked.connect(lambda: self.add_current_to_store(force_type="sentence"))

    def _make_text_tab(self, sections: Iterable[str]) -> Dict[str, Any]:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        split = QSplitter(Qt.Vertical)
        layout.addWidget(split)
        boxes = {}
        for title in sections:
            area = QWidget()
            al = QVBoxLayout(area)
            lab = QLabel(title)
            lab.setStyleSheet("font-weight:700; font-size:16px;")
            edit = QTextEdit()
            edit.setReadOnly(True)
            al.addWidget(lab)
            al.addWidget(edit)
            split.addWidget(area)
            boxes[title] = edit
        split.setSizes([160] * len(boxes))
        return {"widget": widget, "boxes": boxes}

    def _run(self, mode: str, payload: Dict[str, Any]) -> None:
        worker = AIAnalyzeWorker(self.provider_callback, mode, payload)
        self.worker_registry.track(worker, f"ai_{mode}")
        worker.success.connect(lambda data, m=mode: self._apply_result(m, data))
        worker.failed.connect(lambda err, m=mode: QMessageBox.critical(self, f"AI分析失败[{m}]", err))
        self.request_started.emit(mode)
        worker.finished.connect(lambda m=mode: self.request_finished.emit(m))
        worker.start()

    def analyze_word(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.current_mode = "word"
        self.current_payload = {"text": text}
        self._run("word", self.current_payload)

    def analyze_sentence(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.current_mode = "sentence"
        self.current_payload = {"text": text}
        self._run("sentence", self.current_payload)

    def analyze_article(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.current_mode = "article"
        self.current_payload = {"text": text}
        self._run("article", self.current_payload)

    def _apply_result(self, mode: str, data: Dict[str, Any]) -> None:
        if mode == "word":
            for key, edit in self.word_tab["boxes"].items():
                edit.setPlainText(str(data.get(key, "")).strip())
            self.tabs.setCurrentWidget(self.word_tab["widget"])
        elif mode == "sentence":
            for key, edit in self.sent_tab["boxes"].items():
                edit.setPlainText(str(data.get(key, "")).strip())
            self.tabs.setCurrentWidget(self.sent_tab["widget"])
        elif mode == "article":
            for key, edit in self.article_tab["boxes"].items():
                edit.setPlainText(str(data.get(key, "")).strip())
            self.tabs.setCurrentWidget(self.article_tab["widget"])

    def add_current_to_store(self, force_type: Optional[str] = None) -> None:
        if not self.study_store:
            QMessageBox.warning(self, "提示", "未绑定学习项存储")
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        item_type = force_type or ("word" if self.current_mode == "word" else "sentence")
        item = StudyItem(
            id=f"si_{int(time.time()*1000)}",
            entry_type=item_type,
            content=text,
            translation="",
            note="",
            category="未分类",
            source="AI分析",
        )
        self.study_store.add(item)
        QMessageBox.information(self, "已保存", f"已加入{ '生词本' if item_type == 'word' else '学习笔记' }")


# =========================
# 四、主窗口里怎么接
# =========================

MAINWINDOW_PATCH_USAGE = r'''
# 1) 在 MainWindow.__init__ 里加入：
from pathlib import Path
from 代码整改补丁_AI分析_生词本_线程管理 import WorkerRegistry, StudyItemStore, AIAnalysisPanel, StudyItemEditor, StyleDialog

self.worker_registry = WorkerRegistry(self)
self.vocab_store = StudyItemStore(Path("data") / "vocab_items.json")
self.note_store = StudyItemStore(Path("data") / "note_items.json")

# 2) 重写 closeEvent：
def closeEvent(self, event):
    try:
        self.worker_registry.stop_all()
    finally:
        super().closeEvent(event)

# 3) 把“AI互动”页换成 AIAnalysisPanel：
def _build_ai_tab(self):
    layout = QVBoxLayout(self.ai_tab)
    self.ai_panel = AIAnalysisPanel(
        provider_callback=self.call_ai_analysis,
        worker_registry=self.worker_registry,
        study_store=self.vocab_store,
    )
    layout.addWidget(self.ai_panel)

# 4) 在 MainWindow 里实现 provider_callback：
def call_ai_analysis(self, mode: str, payload: dict) -> dict:
    text = (payload.get("text") or "").strip()
    # 这里替换成你已有的 AI 接口请求
    # 返回值必须是 dict，并且 key 要与 AIAnalysisPanel 里的栏目名对应。
    if mode == "word":
        return {
            "核心义": f"{text} 的中文核心义...",
            "助记": f"{text} 的助记...",
            "词根": "...",
            "词源": "...",
            "搭配": "...",
            "同义词": "...",
            "形近词": "...",
            "替换": "...",
            "单词新解": "...",
            "派生词": "...",
        }
    if mode == "sentence":
        return {
            "语法分析": "...",
            "句子主干": "...",
            "从句结构": "...",
            "搭配积累": "...",
            "难词解释": "...",
            "升级表达": "...",
            "同义改写": "...",
            "跟读提示": "...",
        }
    return {
        "摘要": "...",
        "段落主旨": "...",
        "重点词汇": "...",
        "重点搭配": "...",
        "难句拆解": "...",
        "笔记": "...",
    }

# 5) 生词本 / 笔记页不要再只允许“单词”
#    打开编辑器时，直接允许 type = word / phrase / sentence
'''


if __name__ == "__main__":
    print("这个文件是补丁模块，请在你的主工程中 import 使用。")
    print(MAINWINDOW_PATCH_USAGE)

import sys
import os
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, 
                             QFileDialog, QListWidget, QProgressBar, QTextEdit, QWidget, QHBoxLayout)
from PySide6.QtCore import QThread, Signal, Qt

# 核心：使用 faster_whisper
from faster_whisper import WhisperModel

class TranscribeThread(QThread):
    progress_update = Signal(int, str)  # 进度百分比, 当前状态文字
    task_finished = Signal(str)         # 完成的文件名
    all_done = Signal()

    def __init__(self, file_paths, model_size="base"):
        super().__init__()
        self.file_paths = file_paths
        self.model_size = model_size
        self._is_running = True

    def run(self):
        try:
            # 自动检测设备：有显卡用CUDA，没显卡用CPU
            # 注意：使用CUDA通常需要安装 cuDNN 和 NVIDIA 驱动
            device = "cuda" if os.environ.get("CUDA_PATH") else "cpu"
            self.progress_update.emit(0, f"正在加载模型 ({device})...")
            
            # 初始化模型
            model = WhisperModel(self.model_size, device=device, compute_type="int8")

            for file_path in self.file_paths:
                if not self._is_running:
                    break
                
                base_name = os.path.basename(file_path)
                self.progress_update.emit(0, f"正在处理: {base_name}")
                
                # 开始转录
                segments, info = model.transcribe(file_path, beam_size=5)
                
                duration = info.duration
                results = []
                
                for segment in segments:
                    if not self._is_running:
                        break
                    results.append(segment)
                    # 更新进度条
                    progress = int((segment.end / duration) * 100)
                    self.progress_update.emit(progress, f"进度: {progress}% - {base_name}")

                if self._is_running:
                    self.save_srt(file_path, results)
                    self.task_finished.emit(base_name)

            self.all_done.emit()
        except Exception as e:
            self.progress_update.emit(0, f"发生错误: {str(e)}")

    def save_srt(self, video_path, segments):
        srt_path = os.path.splitext(video_path)[0] + ".srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, s in enumerate(segments):
                f.write(f"{i+1}\n{self.format_time(s.start)} --> {self.format_time(s.end)}\n{s.text.strip()}\n\n")

    def format_time(self, seconds):
        td = time.gmtime(seconds)
        milis = int((seconds - int(seconds)) * 1000)
        return f"{time.strftime('%H:%M:%S', td)},{milis:03}"

    def stop(self):
        self._is_running = False

class WhisperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PotPlayer 助手：Whisper 批量字幕生成器")
        self.setMinimumSize(700, 500)
        
        # UI 布局
        layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setToolTip("拖入文件或点击添加")
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加视频/音频")
        self.btn_clear = QPushButton("清空列表")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_clear)
        
        self.progress_bar = QProgressBar()
        self.status_label = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setPlaceholderText("日志信息将在此显示...")
        
        ctrl_layout = QHBoxLayout()
        self.btn_start = QPushButton("🚀 开始批量生成")
        self.btn_stop = QPushButton("🛑 停止任务")
        self.btn_stop.setEnabled(False)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        
        layout.addWidget(self.file_list)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(ctrl_layout)
        layout.addWidget(self.status_label)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 逻辑绑定
        self.btn_add.clicked.connect(self.add_files)
        self.btn_clear.clicked.connect(lambda: (self.file_list.clear(), self.files.clear()))
        self.btn_start.clicked.connect(self.start_task)
        self.btn_stop.clicked.connect(self.stop_task)
        
        self.files = []

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "Media Files (*.mp4 *.mkv *.mp3 *.wav *.flac)")
        if files:
            for f in files:
                if f not in self.files:
                    self.files.append(f)
                    self.file_list.addItem(os.path.basename(f))

    def start_task(self):
        if not self.files:
            self.status_label.append("❌ 请先添加文件！")
            return
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.thread = TranscribeThread(self.files)
        self.thread.progress_update.connect(self.handle_progress)
        self.thread.task_finished.connect(lambda name: self.status_label.append(f"✅ 完成: {name}"))
        self.thread.all_done.connect(self.task_over)
        self.thread.start()

    def handle_progress(self, val, msg):
        self.progress_bar.setValue(val)
        if "正在处理" in msg:
            self.status_label.append(msg)

    def stop_task(self):
        if hasattr(self, 'thread'):
            self.thread.stop()
            self.status_label.append("⚠️ 正在尝试停止，请稍候...")

    def task_over(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.append("✨ 任务结束。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置样式
    app.setStyle("Fusion") 
    window = WhisperApp()
    window.show()
    sys.exit(app.exec())
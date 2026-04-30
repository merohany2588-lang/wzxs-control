
import sys, socket, threading, json, os
from pathlib import Path
try:
    from PySide6.QtCore import QObject, Signal, QUrl, Qt
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
except Exception as e:
    print("PY_SIDE6_IMPORT_FAILED", repr(e), flush=True)
    sys.exit(3)

class Bridge(QObject):
    play_signal = Signal(str)
    stop_signal = Signal()

class Win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PlayPhrase Studio Player · 左键重播 / 右键关闭 / Esc关闭')
        self.resize(920, 520)
        self.current_path = '' 
        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.video = QVideoWidget(); layout.addWidget(self.video, 1)
        self.label = QLabel('等待播放片段...'); layout.addWidget(self.label)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.85)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
    def play_path(self, p):
        p = str(Path(p).resolve())
        self.current_path = p
        self.label.setText(p + '    | 左键重播，右键/Esc 关闭')
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(p))
        self.player.play()
        self.show(); self.raise_(); self.activateWindow()
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.hide()
        elif event.button() == Qt.LeftButton and self.current_path:
            self.play_path(self.current_path)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
    def stop(self):
        self.player.stop()


def server_loop(port, bridge):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', port)); srv.listen(5)
    print('PLAYER_READY', port, flush=True)
    while True:
        conn, _ = srv.accept()
        with conn:
            data = conn.recv(65536).decode('utf-8', errors='ignore')
            if not data: continue
            try:
                msg = json.loads(data)
            except Exception:
                continue
            cmd = msg.get('cmd')
            if cmd == 'play':
                bridge.play_signal.emit(msg.get('path',''))
            elif cmd == 'stop':
                bridge.stop_signal.emit()
            elif cmd == 'quit':
                bridge.stop_signal.emit()
                os._exit(0)


def main():
    if len(sys.argv) < 2:
        print("qt_player_helper must be started by PlayPhrase Studio with a port argument.", flush=True)
        return
    try:
        port = int(sys.argv[1])
    except Exception:
        print("INVALID_PORT", sys.argv[1:] if len(sys.argv) > 1 else [], flush=True)
        return
    app = QApplication(sys.argv)
    win = Win()
    bridge = Bridge()
    bridge.play_signal.connect(win.play_path)
    bridge.stop_signal.connect(win.stop)
    threading.Thread(target=server_loop, args=(port, bridge), daemon=True).start()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

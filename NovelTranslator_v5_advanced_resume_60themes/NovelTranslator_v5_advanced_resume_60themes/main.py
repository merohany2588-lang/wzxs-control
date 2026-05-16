import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1180, 820)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

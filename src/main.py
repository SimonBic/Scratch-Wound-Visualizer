from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from userinterface import MainWindow
 
STYLESHEET = Path(__file__).resolve() / "style.qss"
 
 
def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Scratch Wound Visualizer")
 
    if STYLESHEET.is_file():
        app.setStyleSheet(STYLESHEET.read_text(encoding="utf-8"))
 
    window = MainWindow()
    window.show()
    return app.exec()
 
 
if __name__ == "__main__":
    raise SystemExit(main())
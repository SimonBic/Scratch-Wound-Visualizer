from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from userinterface import MainWindow
 
from theme import QSS
 
 
def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Scratch Wound Visualizer")
    app.setStyleSheet(QSS)
    
    window = MainWindow()
    window.show()
    return app.exec()
 
 
if __name__ == "__main__":
    raise SystemExit(main())
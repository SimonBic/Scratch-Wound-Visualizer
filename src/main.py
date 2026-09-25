from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from userinterface import MainWindow, LOGO
 
from theme import QSS
 
 
def main() -> int:
    if sys.platform == "win32":
        #Eigene App-ID, sonst zeigt die Taskleiste das Python-Icon statt dem Logo
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ukr.scratchwoundvisualizer")

    app = QApplication(sys.argv)
    app.setApplicationName("Scratch Wound Visualizer")
    app.setDesktopFileName("scratch-wound-visualizer") #Verknuepft das Fenster unter Linux mit dem .desktop-Eintrag
    app.setWindowIcon(QIcon(str(LOGO)))
    app.setStyleSheet(QSS)
    
    window = MainWindow()
    window.show()
    return app.exec()
 
 
if __name__ == "__main__":
    raise SystemExit(main())
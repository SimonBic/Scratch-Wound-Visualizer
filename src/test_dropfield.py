import sys
from PySide6.QtWidgets import QApplication
from dropfield import DropField

app = QApplication(sys.argv)
w = DropField(1)
w.setStyleSheet("""
QFrame#dropField { border: 2px dashed #b0b0b0; border-radius: 8px; }
QFrame#dropField QLabel { color: #909090; }
QFrame#dropField[state="hover"]  { border-color: #e0a800; }
QFrame#dropField[state="filled"] { border-style: solid; }
""")
w.fileDropped.connect(print)
w.resize(300, 200)
w.show()
sys.exit(app.exec())
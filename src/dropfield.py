from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PySide6.QtGui import QImageReader, QPixmap, QImage
from pathlib import Path

from scanner import SUFFIXE

class DropField(QFrame):
    fileDropped = Signal(str)   # gibt den Pfad nach oben weiter

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.path = None
        self._pixmap = None
        self.setAcceptDrops(True)          
        self.setObjectName("dropField")   

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setScaledContents(False)
        self.preview.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.label_dropfield = QLabel(f"Bild Nr.: {index} hier ablegen") 
        self.label_dropfield.setAlignment(Qt.AlignCenter)
        self.box_layout_dropfield = QVBoxLayout(self)

        self.box_layout_dropfield.addWidget(self.preview, 1)     
        self.box_layout_dropfield.addWidget(self.label_dropfield) # Dateiname darunter
        self.setMinimumSize(192, 108)

    def dragEnterEvent(self, event):
        if self._is_image(event.mimeData()):
            event.acceptProposedAction()
            self.setProperty("state", "hover")
            self._refresh_style()

    def _is_image(self, mime) -> bool:
        #Gleiche Dateitypen wie im Ordner-Modus (scanner.py)
        if not mime.hasUrls():
            return False
        return Path(mime.urls()[0].toLocalFile()).suffix.lower() in SUFFIXE

    def set_path(self, path: str):
        self.path = path
        self._pixmap = self._load_preview(path)

        if self._pixmap:
            self._update_preview()
            self.label_dropfield.setText(Path(path).name)
        else:
            self.preview.clear()
            self.label_dropfield.setText(f"{Path(path).name}\n(keine Vorschau)")

        self.setProperty("state", "filled")
        self._refresh_style()
        self.fileDropped.emit(path)

    def dragLeaveEvent(self, event):
        self.setProperty("state", "filled" if self.path else "")
        self._refresh_style()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        self.set_path(url.toLocalFile())
        event.acceptProposedAction()

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)

    def _load_preview(self, path: str):
        reader = QImageReader(path)
        reader.setAutoTransform(True)

        size = reader.size()
        if size.isValid():
            size.scale(400, 400, Qt.KeepAspectRatio)
            reader.setScaledSize(size)

        image = reader.read()
        if not image.isNull():
            return QPixmap.fromImage(image)

        # Qt kam mit der Datei nicht klar -> tifffile versuchen
        try:
            import numpy as np
            import tifffile
            arr = tifffile.imread(path)
            if arr.ndim > 2:
                arr = arr[0] if arr.shape[0] < arr.shape[-1] else arr[..., 0]
            arr = arr.astype(np.float32)
            lo, hi = arr.min(), arr.max()
            arr8 = (np.zeros_like(arr, dtype=np.uint8) if hi <= lo
                    else ((arr - lo) / (hi - lo) * 255).astype(np.uint8))
            arr8 = np.ascontiguousarray(arr8)
            h, w = arr8.shape
            img = QImage(arr8.data, w, h, w, QImage.Format_Grayscale8).copy()
            return QPixmap.fromImage(img)
        except Exception as exc:
            print("Vorschau fehlgeschlagen:", exc)
            return None

    def _update_preview(self):
        if not self._pixmap:
            return
        self.preview.setPixmap(self._pixmap.scaled(
            self.preview.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()

    def clear_field(self):
        self.path = None
        self._pixmap = None
        self.preview.clear()
        self.label_dropfield.setText(f"Bild Nr.: {self.index} hier ablegen")
        self.setProperty("state", "")
        self._refresh_style()


class FolderDropField(QFrame):
    folderDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.path = None
        self.setAcceptDrops(True)
        self.setObjectName("folderDrop")
        self.setMinimumHeight(220)

        self.label = QLabel("Ordner hier ablegen")
        self.label.setObjectName("folderDropLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)

        lay = QVBoxLayout(self)
        lay.addWidget(self.label)

    def _is_folder(self, mime) -> bool:
        if not mime.hasUrls():
            return False
        return Path(mime.urls()[0].toLocalFile()).is_dir()

    def dragEnterEvent(self, event):
        if self._is_folder(event.mimeData()):
            event.acceptProposedAction()
            self.setProperty("state", "hover")
            self._refresh_style()

    def dragLeaveEvent(self, event):
        self.setProperty("state", "filled" if self.path else "")
        self._refresh_style()

    def dropEvent(self, event):
        pfad = event.mimeData().urls()[0].toLocalFile()
        self.set_path(pfad)
        event.acceptProposedAction()

    def set_path(self, path: str):
        self.path = path
        self.label.setText(Path(path).name)
        self.setProperty("state", "filled")
        self._refresh_style()
        self.folderDropped.emit(path)

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
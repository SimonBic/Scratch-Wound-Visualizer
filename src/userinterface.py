from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator #Für die EIngabefelder, zb dass man keine Buchstaben eingeben kann
from PySide6.QtSvgWidgets import QSvgWidget #Für das Logo
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QButtonGroup,
    QPushButton
)


ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS / "logo.svg"



# Kopfzeile


class HeaderBar(QWidget):
    #Logo links, Titel rehcts daneben

    LOGO_SIZE = 40

    def __init__(self, parent: QWidget | None = None): #Erbt von dem dem "Hauptwidget"
        #Titelzeile und Logo
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)   #Abstände definieren zu den Rändern des Headerobjekts
        layout.setSpacing(12)                       #Abstände zwischen den Elementen

        #Logo und Titel hinzufügen
        layout.addWidget(self._make_logo())

        title = QLabel("Scratch Wound Visualizer")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        layout.addStretch(1)

    def _make_logo(self) -> QWidget:
        if LOGO.is_file():
            svg = QSvgWidget(str(LOGO))
            svg.setFixedSize(self.LOGO_SIZE, self.LOGO_SIZE)
            return svg

        placeholder = QLabel("Logo")
        placeholder.setObjectName("logoPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setFixedSize(self.LOGO_SIZE, self.LOGO_SIZE)
        placeholder.setToolTip(f"Logo erwartet unter: {LOGO}")
        return placeholder


class ParameterPanel(QWidget):
    #Seitenspalte (1/5 der Breite)

    parameters_changed = Signal(dict)

    #Höhe des Bedienblocks
    CONTROLS_START = 1 / 3
    #Minimaler Abstand der Oberkante des Bedienblocks zum oberen Rand der Seitenspalte
    TOP_MARGIN = 16

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, self.TOP_MARGIN, 16, 16)
        layout.setSpacing(0)

        self._top_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addSpacerItem(self._top_spacer)

        layout.addWidget(self._build_threshold())
        layout.addSpacing(24)
        layout.addWidget(self._build_variance_radius())
        layout.addSpacing(16)
        layout.addWidget(self._build_saturated())

        layout.addStretch(1)

    def resizeEvent(self, event):
        #Hält die Oberkante des Bedienblocks auf der 1/3-Linie
        super().resizeEvent(event)
        offset = int(self.height() * self.CONTROLS_START) - self.TOP_MARGIN
        self._top_spacer.changeSize(
            0, max(offset, 0), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self.layout().invalidate()


    def _build_threshold(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        header = QHBoxLayout()
        label = QLabel("Threshold")
        label.setObjectName("paramLabel")
        self.threshold_value = QLabel("50")
        self.threshold_value.setObjectName("paramValue")
        header.addWidget(label)
        header.addStretch(1)
        header.addWidget(self.threshold_value)
        v.addLayout(header)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(50)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.setToolTip(
            "Schwellwert für die Binarisierung.\n"
            "Höher = mehr wird als Wunde gewertet."
        )
        self.threshold_slider.valueChanged.connect(self._on_threshold)
        v.addWidget(self.threshold_slider)

        return box

    def _build_variance_radius(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        label = QLabel("Variance window radius")
        label.setObjectName("paramLabel")
        v.addWidget(label)

        self.variance_edit = QLineEdit("20")
        self.variance_edit.setValidator(QIntValidator(1, 500, self))
        self.variance_edit.setPlaceholderText("z. B. 20")
        self.variance_edit.setToolTip(
            "Radius des Varianzfilters in Pixeln.\n"
            "Zu klein: Spalt wird nicht erkannt.\n"
            "Zu groß: Fläche wird unterschätzt."
        )
        self.variance_edit.textChanged.connect(self._emit)
        v.addWidget(self.variance_edit)

        return box

    def _build_saturated(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        label = QLabel("Percentage of saturated pixels")
        label.setObjectName("paramLabel")
        label.setWordWrap(True)
        v.addWidget(label)

        validator = QDoubleValidator(0.0, 100.0, 4, self)
        validator.setNotation(QDoubleValidator.StandardNotation)

        self.saturated_edit = QLineEdit("0.01")
        self.saturated_edit.setValidator(validator)
        self.saturated_edit.setPlaceholderText("z. B. 0.01")
        self.saturated_edit.setToolTip(
            "Anteil gesättigter Pixel bei der Kontrastverstärkung.\n"
            "Höher = kleinere erkannte Fläche."
        )
        self.saturated_edit.textChanged.connect(self._emit)
        v.addWidget(self.saturated_edit)

        return box

    def _on_threshold(self, value: int):
        self.threshold_value.setText(str(value))
        self._emit()

    def values(self) -> dict:
        def as_int(text: str, default: int) -> int:
            try:
                return int(text)
            except ValueError:
                return default

        def as_float(text: str, default: float) -> float:
            try:
                return float(text.replace(",", "."))
            except ValueError:
                return default

        return {
            "threshold": self.threshold_slider.value(),
            "variance_radius": as_int(self.variance_edit.text(), 20),
            "saturated": as_float(self.saturated_edit.text(), 0.01),
        }

    def _emit(self):
        self.parameters_changed.emit(self.values())



class ModeCard(QPushButton):
    def __init__(self, title, subtitle, hint, parent=None):
        super().__init__(parent)
        self.setObjectName("modeCard")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(280, 190)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("modeCardTitle")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setObjectName("modeCardSubtitle")
        lbl_sub.setWordWrap(True)

        lbl_hint = QLabel(hint)
        lbl_hint.setObjectName("modeCardHint")
        lbl_hint.setWordWrap(True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addStretch(1)
        layout.addWidget(lbl_hint)


        #Label, also Text, würde die klicks nicht durch lassen, deswegen wird hier festegelegt, dass 
        #Die Labels keine Klicks verschlucken.
        for lbl in (lbl_title, lbl_sub, lbl_hint):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

class ImageArea(QFrame):
    #4/5 der Breite
    mode_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("imageArea")
        
        self.card_single = ModeCard(
            "Einzelner Versuch",
            "Ein Versuchsaufbau mit Bidlern wie 24h, 48h usw.",
            "",
        )
        self.card_batch = ModeCard(
            "Mehrere Versuche",
            "Ein Ordner mit mehreren Versuchen, je Versuch ein Unterordner.",
            "",
        )

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.addButton(self.card_single)
        self.group.addButton(self.card_batch)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)

        outer.addStretch(1)

        heading = QLabel("Was möchten Sie auswerten?")
        heading.setObjectName("areaHeading")
        heading.setAlignment(Qt.AlignCenter)
        outer.addWidget(heading)

        outer.addSpacing(28)

        cards = QHBoxLayout()
        cards.setSpacing(24)
        cards.addStretch(1)
        cards.addWidget(self.card_single)
        cards.addWidget(self.card_batch)
        cards.addStretch(1)
        outer.addLayout(cards)

        outer.addStretch(2)

        self.card_single.clicked.connect(lambda: self._select("single"))
        self.card_batch.clicked.connect(lambda: self._select("batch"))

        self._mode = None

    def _select(self, mode: str):
        self._mode = mode
        print(f"Debug: select: {self._mode}")
        self.mode_changed.emit(mode)

    def mode(self) -> str | None:
        print(f"Debug: mode: {self._mode}")
        return self._mode

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scratch Wound Visualizer")
        self.resize(1920, 1080)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = HeaderBar()
        root.addWidget(self.header)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("headerRule")
        root.addWidget(separator)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.panel = ParameterPanel()
        self.image_area = ImageArea()

        # Verhaeltnis 1:4 -- die Seitenspalte belegt ein Fuenftel der Breite
        body.addWidget(self.panel, 1)
        body.addWidget(self.image_area, 4)

        root.addLayout(body, 1)
        self.setCentralWidget(central)

        self.panel.parameters_changed.connect(self._on_parameters_changed)
        self.statusBar().showMessage("Bereit")

    def _on_parameters_changed(self, params: dict):
        self.statusBar().showMessage(
            f"Threshold {params['threshold']}  |  "
            f"Radius {params['variance_radius']}  |  "
            f"Saturated {params['saturated']}"
        )
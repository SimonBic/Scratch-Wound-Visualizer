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
    QPushButton,
    QGridLayout,
    QStackedWidget,
    QSpinBox,
    QApplication,
    QMessageBox,
)

from dropfield import DropField, FolderDropField
from scanner import scanne_versuche
from skimage import io as skio
from detect_scratch import detect_scratch_main
from overlay import save_marked, save_combined, save_heatmap, HeatmapAverage, color_for, output_dir_for
from measure import measure_rows, measure_width
from excel_export import save_excel, save_batch_excel

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
    field_count_changed = Signal(int)
    analysis_requested = Signal()
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

        layout.addWidget(self._build_field_count())
        layout.addSpacing(24)
        layout.addWidget(self._build_threshold())
        layout.addSpacing(24)
        layout.addWidget(self._build_variance_radius())
        layout.addSpacing(16)
        layout.addWidget(self._build_saturated())

        self.btn_start = QPushButton("Auswertung starten")
        self.btn_start.setObjectName("startButton")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setMinimumHeight(40)
        self.btn_start.clicked.connect(self.analysis_requested.emit)

        layout.addSpacing(24)
        layout.addWidget(self.btn_start)

        layout.addStretch(1)

    def resizeEvent(self, event):
        #Hält die Oberkante des Bedienblocks auf der 1/3-Linie
        super().resizeEvent(event)
        offset = int(self.height() * self.CONTROLS_START) - self.TOP_MARGIN
        self._top_spacer.changeSize(
            0, max(offset, 0), QSizePolicy.Minimum, QSizePolicy.Fixed
        )
        self.layout().invalidate()

    def _build_field_count(self) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        label = QLabel("Anzahl Bilder")
        label.setObjectName("paramLabel")
        v.addWidget(label)

        self.spin_count = QSpinBox()
        self.spin_count.setRange(2, 24)
        self.spin_count.setValue(4)
        self.spin_count.setToolTip(
            "Wie viele Zeitpunkte hat der Versuch?\n"
            "Legt fest, wie viele Ablagefelder erscheinen."
        )
        self.spin_count.valueChanged.connect(self.field_count_changed.emit)
        v.addWidget(self.spin_count)

        return box

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


class SingleRunPage(QWidget):
    #Vier Ablagefelder für die Zeitreihe eines Versuchs.

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 32, 40, 32)
        outer.setSpacing(20)

        kopf = QHBoxLayout()
        btn_back = QPushButton("← Zurück")
        btn_back.setObjectName("backButton")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self.back_requested.emit)

        titel = QLabel("Bilder des Versuchs ablegen")
        titel.setObjectName("areaHeading")

        kopf.addWidget(btn_back)
        kopf.addSpacing(16)
        kopf.addWidget(titel)
        kopf.addStretch(1)
        outer.addLayout(kopf)

        self.raster = QGridLayout()
        self.raster.setSpacing(20)
        outer.addLayout(self.raster, 1)

        self.fields = []
        self.set_field_count(4)

    def set_field_count(self, n: int):
        #Baut das Raster auf n Felder um. Bereits abgelegte Bilder bleiben
        #erhalten; beim Verkleinern fallen die hinteren Felder weg
        # Felder aus dem Raster lösen, ohne sie zu zerstören
        while self.raster.count():
            self.raster.takeAt(0)

        while len(self.fields) < n:
            self.fields.append(DropField(len(self.fields) + 1))

        while len(self.fields) > n:
            feld = self.fields.pop()
            feld.setParent(None)
            feld.deleteLater()

        spalten = 2 if n <= 4 else 3 if n <= 9 else 4
        for i, feld in enumerate(self.fields):
            self.raster.addWidget(feld, i // spalten, i % spalten)

    def paths(self) -> list[str]:
        """Belegte Felder in Reihenfolge. Leere werden übersprungen."""
        return [f.path for f in self.fields if f.path]

    def reset(self):
        for f in self.fields:
            f.clear_field()

class BatchPage(QWidget):
    """Ein Ordner mit mehreren Versuchen."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.versuche = []
        self.wurzel = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 32, 40, 32)
        outer.setSpacing(20)

        kopf = QHBoxLayout()
        btn_back = QPushButton("← Zurück")
        btn_back.setObjectName("backButton")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self.back_requested.emit)

        titel = QLabel("Ordner mit mehreren Versuchen")
        titel.setObjectName("areaHeading")

        kopf.addWidget(btn_back)
        kopf.addSpacing(16)
        kopf.addWidget(titel)
        kopf.addStretch(1)
        outer.addLayout(kopf)

        erklaerung = QLabel(
            "Erwartete Struktur: ein Ordner, darin je Versuch ein "
            "Unterordner mit den Bildern:\n\n"
            "    Hauptordner/\n"
            "       Versuch_01/\n"
            "           1.tif   2.tif   3.tif\n"
            "       Versuch_02/\n"
            "           A.tif   B.tif   C.tif\n\n"
            "Die Bilder werden je Versuch nach Namen sortiert (2 vor 10) und in "
            "dieser Reihenfolge als Zeitpunkte gewertet. Ordner, die auf _marked "
            "enden (Ergebnisse einer früheren Auswertung), werden übersprungen."
        )
        erklaerung.setObjectName("structureHint")
        outer.addWidget(erklaerung)

        self.drop = FolderDropField()
        self.drop.folderDropped.connect(self._ordner_eingelesen)
        outer.addWidget(self.drop, 1)

        self.zusammenfassung = QLabel("")
        self.zusammenfassung.setObjectName("scanSummary")
        self.zusammenfassung.setWordWrap(True)
        outer.addWidget(self.zusammenfassung)

    def _ordner_eingelesen(self, pfad: str):
        self.wurzel = Path(pfad)
        self.versuche = scanne_versuche(pfad)

        if not self.versuche:
            self.zusammenfassung.setText(
                "Keine Unterordner gefunden. Liegen die Bilder direkt im "
                "gewählten Ordner? Erwartet wird je Versuch ein Unterordner."
            )
            return

        zeilen = [f"{len(self.versuche)} Versuche gefunden:"]
        for name, bilder in self.versuche[:6]:
            zeilen.append(f"  {name}: {len(bilder)} Bilder")
        if len(self.versuche) > 6:
            zeilen.append(f"  … und {len(self.versuche) - 6} weitere")

        leer = [n for n, b in self.versuche if not b]
        if leer:
            zeilen.append(f"Ohne Bilder: {', '.join(leer)}")

        self.zusammenfassung.setText("\n".join(zeilen))


class ImageArea(QFrame):
    # 4/5 der Breite
    mode_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("imageArea")

        self.stack = QStackedWidget()

        # --- Seite 0: Auswahl ---
        auswahl = QWidget()
        outer = QVBoxLayout(auswahl)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.addStretch(1)

        heading = QLabel("Was möchten Sie auswerten?")
        heading.setObjectName("areaHeading")
        heading.setAlignment(Qt.AlignCenter)
        outer.addWidget(heading)

        outer.addSpacing(28)

        self.card_single = ModeCard(
            "Einzelner Versuch",
            "Ein Versuchsaufbau mit Bildern wie 24 h, 48 h usw.",
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

        cards = QHBoxLayout()
        cards.setSpacing(24)
        cards.addStretch(1)
        cards.addWidget(self.card_single)
        cards.addWidget(self.card_batch)
        cards.addStretch(1)
        outer.addLayout(cards)

        outer.addStretch(2)

        #Seite 1: Einzelner Versuch
        self.single_page = SingleRunPage()
        self.single_page.back_requested.connect(self.show_selection)

        #Seite 2, mehrere Versuche in einem Ordner
        self.batch_page = BatchPage()
        self.batch_page.back_requested.connect(self.show_selection)

        #Seiten registrieren 
        self.stack.addWidget(auswahl)           # Index 0
        self.stack.addWidget(self.single_page)  # Index 1
        self.stack.addWidget(self.batch_page)   # Index 2

        #der Stack ist der einzige Inhalt der ImageArea
        rahmen = QVBoxLayout(self)
        rahmen.setContentsMargins(0, 0, 0, 0)
        rahmen.addWidget(self.stack)

        self.card_single.clicked.connect(lambda: self._select("single"))
        self.card_batch.clicked.connect(lambda: self._select("batch"))

        self._mode = None

    def _select(self, mode: str):
        self._mode = mode
        if mode == "single":
            self.stack.setCurrentIndex(1)
        elif mode == "batch":
            self.stack.setCurrentIndex(2)
        self.mode_changed.emit(mode)

    def show_selection(self):
        self.stack.setCurrentIndex(0)
        self.group.setExclusive(False)
        self.card_single.setChecked(False)
        self.card_batch.setChecked(False)
        self.group.setExclusive(True)
        self._mode = None

    def set_field_count(self, n: int):
        self.single_page.set_field_count(n)

    def mode(self) -> str | None:
        return self._mode

    def collect_runs(self) -> list:
        if self._mode == "single":
            paths = self.single_page.paths()
            if not paths:
                return []
            return [(Path(paths[0]).parent.name, [Path(p) for p in paths])]

        if self._mode == "batch":
            return [(name, bilder) for name, bilder in self.batch_page.versuche]

        return []

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
        self.panel.field_count_changed.connect(self.image_area.set_field_count)
        self.panel.analysis_requested.connect(self.run_analysis)
        self.statusBar().showMessage("Bereit")

    def _on_parameters_changed(self, params: dict):
        self.statusBar().showMessage(
            f"Threshold {params['threshold']}  |  "
            f"Radius {params['variance_radius']}  |  "
            f"Saturated {params['saturated']}"
        )

    def run_analysis(self):
        # Versuche ohne Bilder (leere Unterordner) ueberspringen
        runs = [(name, paths) for name, paths in self.image_area.collect_runs() if paths]
        if not runs:
            self.statusBar().showMessage("Keine Bilder ausgewählt.")
            return

        params = self.panel.values()
        self.panel.btn_start.setEnabled(False)

        # Ohne try/finally bliebe der Button nach einem Fehler fuer immer grau,
        # und unter Windows (pythonw) saehe man den Fehler gar nicht
        try:
            written = self._analyse(runs, params)
        except PermissionError as exc:
            self._show_error(
                "Eine Datei konnte nicht geschrieben werden:\n"
                f"{exc.filename}\n\n"
                "Ist sie vielleicht noch in Excel oder einem Bildprogramm geöffnet? "
                "Bitte schließen und die Auswertung nochmal starten."
            )
        except Exception as exc:
            self._show_error(f"Die Auswertung ist abgebrochen:\n\n{type(exc).__name__}: {exc}")
        else:
            self.statusBar().showMessage(f"Fertig: {len(runs)} Versuche, {written} Dateien geschrieben")
        finally:
            self.panel.btn_start.setEnabled(True)

    def _show_error(self, text: str):
        self.statusBar().showMessage("Fehler bei der Auswertung")
        QMessageBox.critical(self, "Fehler", text)

    def _analyse(self, runs: list, params: dict) -> int:
        batch = self.image_area.mode() == "batch"
        results = []
        heatmap_average = HeatmapAverage()

        written = 0
        for run_name, paths in runs:
            # Zielordner aus dem Ordner der Bilder ableiten
            target_dir = output_dir_for(paths[0].parent)

            masks = []
            measurements = []
            for p in paths:
                self.statusBar().showMessage(f"{run_name}: {p.name}")
                QApplication.processEvents()

                image = skio.imread(str(p))
                mask = detect_scratch_main(
                    image,
                    radius=params["variance_radius"],
                    threshold=params["threshold"],
                    saturated=params["saturated"],
                )
                if masks and mask.shape != masks[0].shape:
                    raise ValueError(
                        f"{p.name} hat eine andere Bildgröße als das erste Bild von {run_name} "
                        f"({mask.shape[1]}x{mask.shape[0]} statt {masks[0].shape[1]}x{masks[0].shape[0]})."
                    )
                masks.append(mask)
                if len(masks) == 1:
                    # Messbereich einmal aus dem ersten Bild festlegen
                    rows = measure_rows(mask, params["variance_radius"])
                measurement = measure_width(mask, rows)
                measurements.append(measurement)
                written += len(save_marked(p, mask, measurement, target_dir, color_for(len(masks) - 1, len(paths))))

            written += len(save_combined(paths[-1], masks, target_dir))
            save_heatmap(paths[-1], masks, rows, target_dir)
            written += 1
            results.append((run_name, paths, measurements, rows))

            if batch:
                heatmap_average.add(masks, rows)
            else:
                # Ganzer Ordner: alles in eine gemeinsame Excel (siehe unten)
                save_excel(run_name, paths, measurements, rows, target_dir)
                written += 1

        if batch:
            wurzel = self.image_area.batch_page.wurzel
            save_batch_excel(results, wurzel / f"{wurzel.name}_auswertung.xlsx")
            heatmap_average.save(wurzel / f"{wurzel.name}_gesamt_heatmap.png")
            written += 2

        return written

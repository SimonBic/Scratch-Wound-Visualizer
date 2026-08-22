QSS = """
/* ---------------------------------------------------------------
   Scratch Wound Visualizer -- Erscheinungsbild
   Akzent: Blau #4A90D9 / #3A73AD -- das Logo bleibt gelb und setzt
   damit bewusst den einzigen warmen Punkt in der Oberflaeche.
   --------------------------------------------------------------- */

QMainWindow, QWidget {
    background-color: #F5F7FA;
    color: #1F2937;
    font-size: 14px;
    font-family: "Latin Modern Roman", "CMU Serif", serif;
}

/* -- Kopfzeile -- */

QLabel#appTitle {
    font-size: 22px;
    font-weight: 600;
    color: #1F2937;
    background: transparent;
}

QLabel#logoPlaceholder {
    border: 1px dashed #C7CDD4;
    border-radius: 8px;
    color: #A0A6AE;
    font-size: 12px;
    background: transparent;
}

QFrame#headerRule {
    color: #D8DEE6;
    max-height: 1px;
}

/* -- Seitenspalte -- */

QWidget#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #D8DEE6;
}

QLabel#paramLabel {
    color: #5B6472;
    font-size: 12px;
    letter-spacing: 0.5px;
    background: transparent;
}

QLabel#paramValue {
    color: #3A73AD;
    font-size: 15px;
    font-weight: 600;
    background: transparent;
}

/* -- Bildbereich -- */

QFrame#imageArea {
    background-color: #F5F7FA;
}

QLabel#areaHeading {
    font-size: 20px;
    font-weight: 600;
    color: #1F2937;
    background: transparent;
}

QLabel#structureHint {
    color: #5B6472;
    font-family: monospace;
    font-size: 12px;
    background: transparent;
}

QLabel#scanSummary {
    color: #5B6472;
    font-size: 13px;
    background: transparent;
}

/* -- Knöpfe -- */

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FFFFFF, stop:1 #EDF2F8);
    color: #1F2937;
    border: 2px solid #4A90D9;
    border-radius: 10px;
    padding: 8px;
    font-weight: 500;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #9CBFE2, stop:1 #7FA5C9);
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #4A90D9;
    color: #FFFFFF;
    border-color: #3A73AD;
}

QPushButton:disabled {
    background-color: #EDEFF2;
    color: #A0A6AE;
    border-color: #C7CDD4;
}

QPushButton#startButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #5FA0E0, stop:1 #4A90D9);
    color: #FFFFFF;
    border: 2px solid #3A73AD;
    font-size: 15px;
    font-weight: 600;
    padding: 10px;
}

QPushButton#startButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #B4D0EA, stop:1 #6E97BD);
}

QPushButton#startButton:disabled {
    background: #EDEFF2;
    color: #A0A6AE;
    border-color: #C7CDD4;
}

QPushButton#backButton {
    background: transparent;
    border: 1px solid #C7CDD4;
    border-radius: 6px;
    padding: 6px 14px;
    color: #5B6472;
    font-weight: 400;
}

QPushButton#backButton:hover {
    background: #EDF2F8;
    border-color: #3A73AD;
    color: #1F2937;
}

/* -- Auswahlkacheln -- */

QPushButton#modeCard {
    background-color: #FFFFFF;
    border: 2px solid #D8DEE6;
    border-radius: 12px;
    padding: 0px;
}

QPushButton#modeCard:hover {
    border-color: #4A90D9;
    background-color: #F4F8FC;
}

QPushButton#modeCard:checked {
    border-color: #3A73AD;
    background-color: #EAF2FA;
}

QLabel#modeCardTitle {
    font-size: 17px;
    font-weight: 600;
    color: #1F2937;
    background: transparent;
}

QLabel#modeCardSubtitle {
    font-size: 13px;
    color: #5B6472;
    background: transparent;
}

QLabel#modeCardHint {
    font-size: 12px;
    color: #8A9099;
    background: transparent;
}

/* -- Ablagefelder -- */

QFrame#dropField {
    background-color: #FFFFFF;
    border: 2px dashed #C7CDD4;
    border-radius: 8px;
}

QFrame#dropField QLabel {
    color: #8A9099;
    font-size: 13px;
    background: transparent;
}

QFrame#dropField[state="hover"] {
    border-color: #4A90D9;
    background-color: #F4F8FC;
}

QFrame#dropField[state="filled"] {
    border-style: solid;
    border-color: #3A73AD;
}

QFrame#dropField[state="filled"] QLabel {
    color: #1F2937;
}

QFrame#folderDrop {
    background-color: #FFFFFF;
    border: 2px dashed #C7CDD4;
    border-radius: 12px;
}

QLabel#folderDropLabel {
    color: #8A9099;
    font-size: 16px;
    background: transparent;
}

QFrame#folderDrop[state="hover"] {
    border-color: #4A90D9;
    background-color: #F4F8FC;
}

QFrame#folderDrop[state="filled"] {
    border-style: solid;
    border-color: #3A73AD;
}

QFrame#folderDrop[state="filled"] QLabel#folderDropLabel {
    color: #1F2937;
}

/* -- Eingabefelder -- */

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #C7CDD4;
    border-radius: 6px;
    padding: 6px 8px;
    color: #1F2937;
    selection-background-color: #4A90D9;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #3A73AD;
}

/* -- Schieberegler -- */

QSlider::groove:horizontal {
    height: 5px;
    background: #D8DEE6;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #4A90D9;
    border: 1px solid #3A73AD;
    width: 16px;
    height: 16px;
    margin: -7px 0px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #7FA5C9;
}

QSlider::sub-page:horizontal {
    background: #3A73AD;
    border-radius: 2px;
}

/* -- Bildlaufleisten -- */

QScrollArea#fieldScroll {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: transparent;
    width: 14px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #4A90D9;
    border-radius: 2px;
    min-height: 20px;
    margin: 0px 4px 0px 4px;
}
QScrollBar::handle:vertical:hover {
    background: #3A73AD;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 14px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #4A90D9;
    border-radius: 2px;
    min-width: 20px;
    margin: 4px 0px 4px 0px;
}
QScrollBar::handle:horizontal:hover {
    background: #3A73AD;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* -- Statuszeile -- */

QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #D8DEE6;
    color: #5B6472;
}
"""
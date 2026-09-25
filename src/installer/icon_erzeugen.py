
# Rendert das logo.svg in die Icon-Formate, die Windows (.ico) und
# macOS (.iconset -> .icns) brauchen. Laeuft ueber die VENV-Python,
# weil dort PySide6 installiert ist - Qt kann SVGs selbst rendern,
# dadurch braucht es kein separates logo.png und kein Pillow.

# Aufruf (macht install.py automatisch):
#     python icon_erzeugen.py ico     <logo.svg> <ziel.ico>
#     python icon_erzeugen.py iconset <logo.svg> <ziel.iconset>

import os
import struct
import sys
from pathlib import Path

# Kein Fenster/Display noetig, auch nicht auf einem Server ohne GUI
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def png_rendern(renderer: QSvgRenderer, groesse: int) -> bytes:
    # Jede Groesse direkt aus dem SVG rendern (schaerfer als runterskalieren)
    bild = QImage(groesse, groesse, QImage.Format_ARGB32)
    bild.fill(Qt.transparent)

    painter = QPainter(bild)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()

    daten = QByteArray()
    puffer = QBuffer(daten)
    puffer.open(QIODevice.WriteOnly)
    bild.save(puffer, "PNG")
    return bytes(daten)


def ico_schreiben(renderer: QSvgRenderer, ziel: Path) -> None:
    # ICO-Datei mit eingebetteten PNGs (von Windows seit Vista unterstuetzt):
    # 6 Byte Kopf, dann je Groesse 16 Byte Verzeichniseintrag, dann die PNG-Daten
    groessen = (16, 24, 32, 48, 64, 128, 256)
    pngs = [png_rendern(renderer, g) for g in groessen]

    kopf = struct.pack("<HHH", 0, 1, len(groessen))
    offset = len(kopf) + 16 * len(groessen)

    eintraege = b""
    for groesse, png in zip(groessen, pngs):
        breite = 0 if groesse >= 256 else groesse  # 0 steht im ICO-Format fuer 256
        eintraege += struct.pack("<BBBBHHII", breite, breite, 0, 0, 1, 32, len(png), offset)
        offset += len(png)

    ziel.write_bytes(kopf + eintraege + b"".join(pngs))


def iconset_schreiben(renderer: QSvgRenderer, ziel: Path) -> None:
    # Ordnerstruktur, die macOS' iconutil fuer .icns erwartet
    ziel.mkdir(parents=True, exist_ok=True)
    for groesse in (16, 32, 128, 256, 512):
        (ziel / f"icon_{groesse}x{groesse}.png").write_bytes(png_rendern(renderer, groesse))
        (ziel / f"icon_{groesse}x{groesse}@2x.png").write_bytes(png_rendern(renderer, groesse * 2))


if __name__ == "__main__":
    modus, svg_pfad, ziel_pfad = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])

    app = QGuiApplication(sys.argv[:1])
    renderer = QSvgRenderer(str(svg_pfad))
    if not renderer.isValid():
        sys.exit(f"FEHLER: SVG konnte nicht gelesen werden: {svg_pfad}")

    if modus == "ico":
        ico_schreiben(renderer, ziel_pfad)
    elif modus == "iconset":
        iconset_schreiben(renderer, ziel_pfad)
    else:
        sys.exit(f"FEHLER: Unbekannter Modus '{modus}' (erlaubt: ico, iconset)")

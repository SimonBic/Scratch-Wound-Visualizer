import re
from pathlib import Path

SUFFIXE = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}


def natuerlicher_schluessel(p: Path):
    #Wichtig, da sonst zb 10 vor 2 wäre lexikographisch
    #Nach Namen ohne Endung, sonst kaeme "0001 (1).tif" vor "0001.tif"
    #(Leerzeichen < Punkt). Bei Ordnern gehoert ein Punkt zum Namen.
    endung = p.suffix.lower() if p.suffix.lower() in SUFFIXE else ""
    name = p.name[:len(p.name) - len(endung)]
    teile = re.split(r"(\d+)", name)
    return [int(t) if t.isdecimal() else t.lower() for t in teile], endung


def scanne_versuche(wurzel: str) -> list[tuple[str, list[Path]]]:
    #Liest die Ordnerstruktur ein.

    ##Erwartet: wurzel/<versuch>/<bilder>
    ##Gibt je Versuch den Namen und die sortierten Bildpfade zurück.
    basis = Path(wurzel)
    ergebnis = []

    for unterordner in sorted(basis.iterdir(), key=natuerlicher_schluessel):
        if not unterordner.is_dir():
            continue
        # Ausgabeordner einer frueheren Auswertung nicht nochmal auswerten
        if unterordner.name.endswith("_marked"):
            continue
        bilder = [f for f in unterordner.iterdir()
                  if f.is_file() and f.suffix.lower() in SUFFIXE]
        bilder.sort(key=natuerlicher_schluessel)
        ergebnis.append((unterordner.name, bilder))

    return ergebnis
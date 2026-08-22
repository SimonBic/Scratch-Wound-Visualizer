import re
from pathlib import Path

SUFFIXE = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}


def natuerlicher_schluessel(p: Path):
    #Wichtig, da sonst zb 10 vor 2 wäre lexikographisch
    teile = re.split(r"(\d+)", p.name)
    return [int(t) if t.isdigit() else t.lower() for t in teile]


def scanne_versuche(wurzel: str) -> list[tuple[str, list[Path]]]:
    #Liest die Ordnerstruktur ein.

    ##Erwartet: wurzel/<versuch>/<bilder>
    ##Gibt je Versuch den Namen und die sortierten Bildpfade zurück.
    basis = Path(wurzel)
    ergebnis = []

    for unterordner in sorted(basis.iterdir(), key=natuerlicher_schluessel):
        if not unterordner.is_dir():
            continue
        bilder = [f for f in unterordner.iterdir()
                  if f.is_file() and f.suffix.lower() in SUFFIXE]
        bilder.sort(key=natuerlicher_schluessel)
        ergebnis.append((unterordner.name, bilder))

    return ergebnis
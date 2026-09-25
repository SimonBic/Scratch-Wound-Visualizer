
# Vermisst den Spalt Zeile fuer Zeile. Der Spalt verlaeuft senkrecht
# (siehe fill_holes in detect_scratch.py), deshalb ist der Abstand der
# beiden Grenzlinien in jeder Bildzeile die waagrechte Breite der Maske.
# Alle Werte in Pixeln.

import numpy as np
from scipy import ndimage


def row_edges(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    #Linker und rechter Rand der Wunde je Zeile, plus Breite.
    #Zeilen ohne Wunde (Spalt dort schon zugewachsen) haben Breite 0.
    has_wound = mask.any(axis=1)
    left = np.argmax(mask, axis=1)
    right = mask.shape[1] - 1 - np.argmax(mask[:, ::-1], axis=1)
    width = np.where(has_wound, right - left + 1, 0)
    return left, right, width


def measure_rows(first_mask: np.ndarray, margin: int) -> np.ndarray:
    #Welche Bildzeilen gemessen werden (True/False je Zeile) - bestimmt aus
    #dem ersten Bild. Direkt nach dem Kratzen ist der Spalt ueberall offen,
    #Zeilen ohne Wunde sind dort also immer Stoerungen: dunkler Kamerastreifen
    #am Rand, eine Linie/ein Haar quer durch den Spalt usw.
    #Zusaetzlich fliegt um jede solche Stelle ein Sicherheitsabstand von
    #margin (= Filterradius) raus, weil der Varianzfilter die Stoerung dort
    #schon "sieht" und die Wunde spitz zulaeuft.
    has_wound = first_mask.any(axis=1)
    if not has_wound.any():
        return np.ones(first_mask.shape[0], dtype=bool)

    rows = ndimage.binary_erosion(has_wound, iterations=margin, border_value=0) if margin > 0 else has_wound
    return rows if rows.any() else has_wound


def measure_width(mask: np.ndarray, rows: np.ndarray) -> dict:
    #Mittelwert ueber alle Zeilen im Messbereich, zugewachsene Zeilen
    #zaehlen als 0. Damit ist der Mittelwert = Flaeche / Anzahl Messzeilen.
    left, right, width = row_edges(mask)
    row_index = np.flatnonzero(rows)
    width = width[rows]

    row_min = int(row_index[np.argmin(width)])
    row_max = int(row_index[np.argmax(width)])

    def line(row: int):
        #In zugewachsenen Zeilen gibt es keine Linie zum Einzeichnen
        if not mask[row].any():
            return None
        return (row, int(left[row]), int(right[row]))

    return {
        "mean": float(width.mean()),
        "min": int(width.min()),
        "max": int(width.max()),
        "area": int(mask[rows].sum()),
        "row_min": row_min,
        "row_max": row_max,
        # Wo die Linien fuer Min/Max eingezeichnet werden: (Zeile, links, rechts) oder None
        "min_line": line(row_min),
        "max_line": line(row_max),
    }

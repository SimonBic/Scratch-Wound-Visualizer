from pathlib import Path

import numpy as np
from scipy import ndimage
from skimage import io as skio

from detect_scratch import to_grayscale

# Reihenfolge der Zeitpunkte: rot, orange, gelb, grün, blau
TIMEPOINT_COLORS = [
    (220, 50, 47),
    (230, 130, 30),
    (225, 200, 40),
    (70, 180, 80),
    (60, 120, 220),
]

# Heatmap: Zellrasen zu Zeitpunkt 1 rot, was zu Zeitpunkt 2 dazuwaechst
# gelb, dann gruen, blau, lila
HEATMAP_COLORS = [
    (220, 40, 40),  #rot 
    (240, 220, 40), #gelb
    (60, 190, 70),  #gruen
    (50, 110, 230), # blau
    (150, 70, 200), # lila
]
HEATMAP_OPACITY = 0.4

# Strichstaerken der Grenzlinie
THIN = 3
THICK = 9

# Eingezeichnete Min/Max-Abstaende: weisse Linie, Beschriftung klein darueber
DISTANCE_LINE_COLOR = (255, 255, 255)

def output_dir_for(source_dir: Path) -> Path:
    source_dir = Path(source_dir)
    target = source_dir.with_name(f"{source_dir.name}_marked")
    target.mkdir(parents=True, exist_ok=True)
    return target

def palette(colors: list, n: int) -> list:
    #n Farben aus der Liste. Reicht die Liste nicht, wird sie zu einem
    #Verlauf gestreckt - sonst faenge sie wieder vorne an und z.B.
    #Zeitpunkt 1 und 6 haetten dieselbe Farbe.
    if n <= len(colors):
        return list(colors[:n])
    stops = np.array(colors, dtype=np.float32)
    positions = np.linspace(0, len(colors) - 1, n)
    result = []
    for pos in positions:
        i = min(int(pos), len(colors) - 2)
        f = pos - i
        result.append(tuple(int(round(c)) for c in (1 - f) * stops[i] + f * stops[i + 1]))
    return result


def color_for(index: int, n: int) -> tuple:
    #Farbe der Grenzlinie fuer Zeitpunkt index von n
    return palette(TIMEPOINT_COLORS, n)[index]


def boundary_of(mask: np.ndarray, thickness: int = 3) -> np.ndarray:
    #border_value=1: Wo die Wunde am Bildrand angeschnitten ist, ist das keine Grenze
    eroded = ndimage.binary_erosion(mask, iterations=max(thickness, 1), border_value=1)
    return mask & ~eroded


def to_rgb(image: np.ndarray) -> np.ndarray:
    gray = to_grayscale(image)
    gray8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    return np.dstack([gray8, gray8, gray8])


def draw_boundary(rgb: np.ndarray, mask: np.ndarray, color: tuple, thickness: int = 3) -> np.ndarray:
    result = rgb.copy()
    result[boundary_of(mask, thickness)] = color
    return result


def draw_distance_line(rgb: np.ndarray, line: tuple | None, color: tuple, thickness: int = 3) -> np.ndarray:
    #Waagrechte Linie von der linken zur rechten Grenze in der gegebenen Zeile
    if line is None:
        return rgb  # Spalt dort zu, nichts einzuzeichnen

    row, left, right = line

    result = rgb.copy()
    top = max(row - thickness // 2, 0)
    bottom = min(row + thickness // 2 + 1, rgb.shape[0])
    result[top:bottom, left:right + 1] = color
    return result


def draw_distance_labels(rgb: np.ndarray, labels: list, thickness: int) -> np.ndarray:
    #Beschriftung mittig ueber die jeweilige Linie, weiss mit dunklem Rand,
    #damit sie auf hellem und dunklem Untergrund lesbar ist. Liegt die Linie
    #ganz oben im Bild, kommt der Text darunter.
    from PIL import Image, ImageDraw, ImageFont

    bild = Image.fromarray(rgb)
    draw = ImageDraw.Draw(bild)
    font = ImageFont.load_default(size=max(12, rgb.shape[0] // 60))
    gap = thickness // 2 + 4

    for text, line in labels:
        if line is None:
            continue
        row, left, right = line
        x = (left + right) / 2
        if row - gap - font.size >= 0:
            y, anchor = row - gap, "md"
        else:
            y, anchor = row + gap, "ma"
        draw.text((x, y), text, fill="white", font=font, anchor=anchor,
                  stroke_width=max(1, font.size // 12), stroke_fill="black")

    return np.asarray(bild)


def save_marked(image_path: Path, mask: np.ndarray, measurement: dict, target_dir: Path, color: tuple) -> list[Path]:
    #Je Zeitpunkt eine duenne und eine dicke Version, beide mit Min/Max-Linie
    image_path = Path(image_path)
    base = to_rgb(skio.imread(str(image_path)))

    outputs = []
    for suffix, thickness in (("duenn", THIN), ("dick", THICK)):
        rgb = draw_boundary(base, mask, color, thickness)
        rgb = draw_distance_line(rgb, measurement["max_line"], DISTANCE_LINE_COLOR, thickness)
        rgb = draw_distance_line(rgb, measurement["min_line"], DISTANCE_LINE_COLOR, thickness)
        rgb = draw_distance_labels(rgb, [
            ("Max. distance", measurement["max_line"]),
            ("Min. distance", measurement["min_line"]),
        ], thickness)

        out = Path(target_dir) / f"{image_path.stem}_{suffix}.tif"
        skio.imsave(str(out), rgb)
        outputs.append(out)
    return outputs


def save_combined(last_image_path: Path, masks: list, target_dir: Path, name: str = "_alle_zeitpunkte") -> list[Path]:
    base = to_rgb(skio.imread(str(last_image_path)))

    outputs = []
    for suffix, thickness in (("duenn", THIN), ("dick", THICK)):
        rgb = base
        for i, mask in enumerate(masks):
            rgb = draw_boundary(rgb, mask, color_for(i, len(masks)), thickness)

        out = Path(target_dir) / f"{name}_{suffix}.tif"
        skio.imsave(str(out), rgb)
        outputs.append(out)
    return outputs


def save_heatmap(last_image_path: Path, masks: list, rows: np.ndarray, target_dir: Path, name: str = "_heatmap") -> Path:
    #Zeitpunkt 1: der ganze Zellrasen (alles ausser der Wunde) rot.
    #Jeder weitere Zeitpunkt: nur die Flaeche, die seit dem vorherigen
    #Bild neu zugewachsen ist, in der naechsten Farbe. Was am Ende noch
    #offen ist, bleibt ungefaerbt. Das Ganze mit 40 % Deckkraft uebers
    #letzte Bild. Eingefaerbt wird nur in den Messzeilen (rows), damit z.B.
    #der dunkle Kamerastreifen nicht als Zellrasen erscheint.
    base = to_rgb(skio.imread(str(last_image_path)))

    colors = np.zeros_like(base)
    covered = np.zeros(base.shape[:2], dtype=bool)
    previous_wound = np.ones(base.shape[:2], dtype=bool)
    for i, (mask, color) in enumerate(zip(masks, palette(HEATMAP_COLORS, len(masks)))):
        new_cells = previous_wound & ~mask
        colors[new_cells] = color
        covered |= new_cells
        previous_wound = previous_wound & mask

    covered[~rows] = False

    rgb = base.astype(np.float32)
    rgb[covered] = (1 - HEATMAP_OPACITY) * rgb[covered] + HEATMAP_OPACITY * colors[covered]

    out = Path(target_dir) / f"{name}.tif"
    skio.imsave(str(out), rgb.round().astype(np.uint8))
    return out


# Gesamt-Heatmap: Farbe fuer "am Ende noch offen"
OPEN_COLOR = (200, 200, 200)


def timepoint_map(masks: list) -> np.ndarray:
    #Je Pixel: ab welchem Zeitpunkt dort Zellen sind.
    #0 = Zellrasen zu Zeitpunkt 1, 1 = bis Zeitpunkt 2 zugewachsen, ...,
    #len(masks) = am Ende noch offen
    result = np.zeros(masks[0].shape, dtype=np.uint8)
    still_open = np.ones(masks[0].shape, dtype=bool)
    for i, mask in enumerate(masks):
        result[still_open & ~mask] = i
        still_open &= mask
    result[still_open] = len(masks)
    return result


def align_to_center(values: np.ndarray, first_mask: np.ndarray, rows: np.ndarray) -> np.ndarray:
    #Jede Bildzeile so verschieben, dass die Spaltmitte in der Bildmitte
    #liegt, damit liegen die Spalte aller Versuche genau uebereinander,
    #auch wenn der Kratzer schief oder woanders ist.
    #Die Spaltmitte ist eine gerade Linie durch die Mitten aller Zeilen im
    #ersten Bild (ein Kratzer ist gerade). Direkt die Mitte jeder Zeile zu
    #nehmen wuerde bei jeder Beule am Rand eine Treppe erzeugen.
    #Nicht gemessene Zeilen und rausgeschobene Raender sind NaN.
    height, width = values.shape
    aligned = np.full((height, width), np.nan, dtype=np.float32)

    measured = np.flatnonzero(rows & first_mask.any(axis=1))
    if measured.size < 2:
        return aligned

    left = np.argmax(first_mask[measured], axis=1)
    right = width - 1 - np.argmax(first_mask[measured, ::-1], axis=1)
    slope, offset = np.polyfit(measured, (left + right) / 2, 1)

    for r in np.flatnonzero(rows):
        shift = width // 2 - int(round(slope * r + offset))
        src = values[r, max(0, -shift):width - max(0, shift)]
        aligned[r, max(0, shift):max(0, shift) + src.size] = src

    return aligned


class HeatmapAverage:
    #Sammelt die Versuche eines Ordners und mittelt sie am Ende zu einer
    #Gesamt-Heatmap. Summe + Anzahl je Pixel, damit nicht alle Masken im
    #Speicher bleiben muessen.

    def __init__(self):
        self.total = None
        self.count = None
        self.runs = 0
        self.max_timepoints = 0
        self.timepoint_counts = set()

    def add(self, masks: list, rows: np.ndarray) -> None:
        # Als Anteil 0..1 speichern (0 = Zellrasen Zp. 1, 1 = noch offen), damit
        # Versuche mit unterschiedlich vielen Zeitpunkten zusammenpassen - sonst
        # waere "noch offen" bei 3 Zeitpunkten dasselbe wie "zu bei Zp. 4" bei 7
        aligned = align_to_center(timepoint_map(masks) / len(masks), masks[0], rows)

        if self.total is None:
            self.total = np.zeros(aligned.shape, dtype=np.float64)
            self.count = np.zeros(aligned.shape, dtype=np.int32)

        # Falls ein Versuch andere Bildgroesse hat: auf die erste zuschneiden/auffuellen
        h, w = self.total.shape
        fitted = np.full((h, w), np.nan, dtype=np.float32)
        fitted[:min(h, aligned.shape[0]), :min(w, aligned.shape[1])] = aligned[:h, :w]

        valid = ~np.isnan(fitted)
        self.total[valid] += fitted[valid]
        self.count[valid] += 1
        self.runs += 1
        self.max_timepoints = max(self.max_timepoints, len(masks))
        self.timepoint_counts.add(len(masks))

    def colorize(self) -> np.ndarray:
        #Mittelwert je Pixel -> Farbverlauf zwischen den Zeitpunkt-Farben
        n = self.max_timepoints
        stops = np.array(palette(HEATMAP_COLORS, n) + [OPEN_COLOR], dtype=np.float32)

        mean = np.divide(self.total, self.count, out=np.full(self.total.shape, np.nan), where=self.count > 0)
        v = np.clip(np.nan_to_num(mean, nan=0.0) * n, 0, n)
        lower = np.minimum(np.floor(v).astype(int), n - 1)
        frac = (v - lower)[..., None]
        rgb = (1 - frac) * stops[lower] + frac * stops[lower + 1]

        rgb[self.count == 0] = 255  # keine Daten: weiss
        return rgb.round().astype(np.uint8)

    def save(self, out_path: Path) -> Path | None:
        if self.total is None:
            return None
        from PIL import Image, ImageDraw, ImageFont

        bild = Image.fromarray(self.colorize())
        font = ImageFont.load_default(size=max(20, bild.width // 90))
        pad = bild.width // 60
        bar_h = bild.height // 25
        legend_h = pad * 3 + bar_h + font.size * 5

        canvas = Image.new("RGB", (bild.width, bild.height + legend_h), "white")
        canvas.paste(bild, (0, 0))
        draw = ImageDraw.Draw(canvas)

        # Farbskala: gleicher Verlauf wie im Bild
        n = self.max_timepoints
        x0, x1 = pad, bild.width - pad
        y0 = bild.height + pad
        stops = palette(HEATMAP_COLORS, n) + [OPEN_COLOR]
        for x in range(x0, x1):
            v = (x - x0) / (x1 - x0) * n
            i = min(int(v), n - 1)
            f = v - i
            color = tuple(round((1 - f) * a + f * b) for a, b in zip(stops[i], stops[i + 1]))
            draw.line((x, y0, x, y0 + bar_h), fill=color)
        draw.rectangle((x0, y0, x1, y0 + bar_h), outline="black")

        for i in range(n + 1):
            x = x0 + round(i / n * (x1 - x0))
            label = "Zellrasen Zp. 1" if i == 0 else ("noch offen" if i == n else f"zu bei Zp. {i + 1}")
            anchor = "la" if i == 0 else ("ra" if i == n else "ma")
            draw.line((x, y0 + bar_h, x, y0 + bar_h + pad // 2), fill="black")
            draw.text((x, y0 + bar_h + pad // 2 + 4), label, fill="black", font=font, anchor=anchor)

        draw.text(
            (pad, y0 + bar_h + pad + font.size * 2),
            # ohne Umlaute - die eingebaute Pillow-Schrift kann keine
            f"Durchschnitt aus {self.runs} Versuchen, jeweils an der Spaltmitte (aus dem ersten Bild) "
            "ausgerichtet. Ohne Farbe = keine Daten.",
            fill="black", font=font,
        )
        if len(self.timepoint_counts) > 1:
            draw.text(
                (pad, y0 + bar_h + pad + font.size * 3 + 4),
                "Achtung: Die Versuche haben unterschiedlich viele Zeitpunkte "
                f"({', '.join(map(str, sorted(self.timepoint_counts)))}), sie wurden anteilig umgerechnet.",
                fill="black", font=font,
            )

        canvas.save(out_path)
        return Path(out_path)

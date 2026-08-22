# How the Algorithm works:
# 0. turn pixture into grayscale 
# 1. highten contrast
# 2. add "variancefilter" https://de.wikipedia.org/wiki/Varianzfilter
# 3. measure by given threshold
# 4. fill holes
# 5. find biggest area
# -> count pixels, mesure size etc.

import skimage
import numpy as np
from skimage.color import rgb2gray, rgba2rgb
from skimage.util import img_as_float32
from skimage import exposure
from scipy.signal import fftconvolve
from skimage import morphology
from scipy import ndimage

#0:
def to_grayscale(bild: np.ndarray) -> np.ndarray:
    bild = np.asarray(bild)

    # Mehrseitiges TIFF: erste Ebene nehmen
    if bild.ndim == 3 and bild.shape[-1] not in (3, 4):
        bild = bild[0]
    elif bild.ndim == 4:
        bild = bild[0]

    if bild.ndim == 3 and bild.shape[-1] == 4:
        bild = rgba2rgb(bild)

    if bild.ndim == 3 and bild.shape[-1] == 3:
        bild = rgb2gray(bild)

    grau = img_as_float32(bild)
    return np.clip(grau, 0.0, 1.0)


#1:
def enhance_contrast(grau: np.ndarray, saturated: float = 0.01) -> np.ndarray:
    # saturated ist der Prozentsatz der Pixel, der insgesamt abgeschnitten
    # wird -- je zur Hälfte am unteren und oberen Ende. Richtwert 0.001-0.4.
    # Höherer Wert = stärkerer Kontrast = am Ende kleinere erkannte Fläche.'

    if saturated <= 0:
        return grau

    haelfte = saturated / 2.0
    lo, hi = np.percentile(grau, (haelfte, 100.0 - haelfte))

    if hi <= lo:
        # Bild ist praktisch einfarbig -- Streckung wäre eine Division durch 0
        return grau

    return exposure.rescale_intensity(grau, in_range=(lo, hi), out_range=(0.0, 1.0))

#2.
def variance_filter(bild: np.ndarray, radius: int = 20) -> np.ndarray:
    # Lokale Varianz über eine kreisförmige Nachbarschaft
    
    radius = max(int(radius), 1)

    scheibe = morphology.disk(radius).astype(np.float32)
    scheibe /= scheibe.sum()

    def falten(x):
        # fftconvolve füllt implizit mit Nullen auf,würde die Ränder
        # verfälschen => spiegeln und danach zurückschneiden.
        gepolstert = np.pad(x, radius, mode="reflect")
        return fftconvolve(gepolstert, scheibe, mode="same")[radius:-radius, radius:-radius]

    mittel = falten(bild)
    mittel_quadrat = falten(bild * bild)

    varianz = np.maximum(mittel_quadrat - mittel * mittel, 0.0)

    # Auf 0-255 bringen, damit die Schwellwerte aus dem Paper (50-150)
    # übertragbar bleiben. ImageJ rechnet intern auf 8-bit.
    return varianz * (255.0 * 255.0)

#3.
def find_by_threshold(varianz: np.ndarray, schwelle: float = 100.0) -> np.ndarray:
    #Gibt eine Bool-Maske zurück: True = Wunde, False = Zellrasen.
    return varianz < float(schwelle)

#4.
def fill_holes(maske: np.ndarray) -> np.ndarray:
    #Darauf ausgelegt, dass der Spalt senkrecht verläuft, oben und unten n Padding
    erweitert = np.pad(maske, ((1, 1), (0, 0)), constant_values=True)
    gefuellt = ndimage.binary_fill_holes(erweitert)
    return gefuellt[1:-1, :]

def remove_small_objects(mask: np.ndarray, min_area: int = 100) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        return mask

    sizes = ndimage.sum(mask, labels, index=np.arange(1, count + 1))
    too_small = np.flatnonzero(sizes < min_area) + 1

    result = mask.copy()
    result[np.isin(labels, too_small)] = False
    return result

#5.

def largest_region(mask: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        return np.zeros_like(mask, dtype=bool)

    ids = np.arange(1, count + 1)
    sizes = ndimage.sum(mask, labels, index=ids)

    top = set(np.unique(labels[0, :])) - {0}
    bottom = set(np.unique(labels[-1, :])) - {0}
    spanning = top & bottom

    if spanning:
        candidates = np.array(sorted(spanning))
        chosen = candidates[np.argmax(sizes[candidates - 1])]
    else:
        chosen = ids[np.argmax(sizes)]

    return labels == chosen

#Main:
def detect_scratch_main(
        image: np.ndarray, 
        radius: int = 35, 
        threshold: float = 100.0,
        saturated: float = 0.01, 
        min_area: int = 100) -> np.ndarray:

    gray = to_grayscale(image)
    enhanced = enhance_contrast(gray, saturated)
    variance = variance_filter(enhanced, radius)

    mask = find_by_threshold(variance, threshold)
    mask = fill_holes(mask)
    mask = remove_small_objects(mask, min_area)
    return largest_region(mask)

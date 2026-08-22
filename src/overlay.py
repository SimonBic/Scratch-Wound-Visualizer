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

def output_dir_for(source_dir: Path) -> Path:
    source_dir = Path(source_dir)
    target = source_dir.with_name(f"{source_dir.name}_marked")
    target.mkdir(parents=True, exist_ok=True)
    return target

def color_for(index: int) -> tuple:
    return TIMEPOINT_COLORS[index % len(TIMEPOINT_COLORS)]


def boundary_of(mask: np.ndarray, thickness: int = 3) -> np.ndarray:
    eroded = ndimage.binary_erosion(mask, iterations=max(thickness, 1))
    return mask & ~eroded


def to_rgb(image: np.ndarray) -> np.ndarray:
    gray = to_grayscale(image)
    gray8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    return np.dstack([gray8, gray8, gray8])


def draw_boundary(rgb: np.ndarray, mask: np.ndarray, color: tuple, thickness: int = 3) -> np.ndarray:
    result = rgb.copy()
    result[boundary_of(mask, thickness)] = color
    return result


def save_marked(image_path: Path, mask: np.ndarray, target_dir: Path, color: tuple = (220, 50, 47), thickness: int = 3) -> Path:
    image_path = Path(image_path)
    rgb = draw_boundary(to_rgb(skio.imread(str(image_path))), mask, color, thickness)

    out = Path(target_dir) / f"{image_path.stem}.tif"
    skio.imsave(str(out), rgb)
    return out


def save_combined(last_image_path: Path, masks: list, target_dir: Path, name: str = "_all_timepoints", thickness: int = 3) -> Path:
    rgb = to_rgb(skio.imread(str(last_image_path)))

    for i, mask in enumerate(masks):
        rgb = draw_boundary(rgb, mask, color_for(i), thickness)

    out = Path(target_dir) / f"{name}.tif"
    skio.imsave(str(out), rgb)
    return out
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_image(path: str | Path):
    """Read an image from paths that may contain non-ASCII characters on Windows."""
    path = Path(path)
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def write_image(path: str | Path, image) -> bool:
    """Write an image to paths that may contain non-ASCII characters on Windows."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix or ".jpg"
    ok, buffer = cv2.imencode(ext, image)
    if not ok:
        return False
    buffer.tofile(str(path))
    return True

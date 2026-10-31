"""Generate a multi-size assets/app.ico from the programmatic app icon.

Run once (or whenever the icon design changes):
    python scripts/generate_icons.py

Writes ICO entries as PNG streams (supported by Windows Vista+) so no extra
third-party dependency is needed.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice  # noqa: E402
from PyQt6.QtGui import QGuiApplication, QPixmap  # noqa: E402

from src.core.state import ASSETS_DIR  # noqa: E402
from src.ui.icons import build_app_icon  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)


def _png_bytes(pixmap: QPixmap) -> bytes:
    buffer = QByteArray()
    device = QBuffer(buffer)
    device.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(device, "PNG")
    device.close()
    return bytes(buffer)


def write_ico(path: Path, pixmaps: list[QPixmap]) -> None:
    header = struct.pack("<HHH", 0, 1, len(pixmaps))
    entries = []
    images = []
    offset = 6 + 16 * len(pixmaps)
    for pixmap in pixmaps:
        data = _png_bytes(pixmap)
        width = pixmap.width() if pixmap.width() < 256 else 0
        height = pixmap.height() if pixmap.height() < 256 else 0
        entries.append(
            struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(data), offset)
        )
        images.append(data)
        offset += len(data)
    path.write_bytes(header + b"".join(entries) + b"".join(images))


def main() -> None:
    app = QGuiApplication(sys.argv)  # noqa: F841 - needed for QPixmap
    icon = build_app_icon()
    pixmaps = [icon.pixmap(size, size) for size in SIZES]
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    output = ASSETS_DIR / "app.ico"
    write_ico(output, pixmaps)
    print(f"Wrote {output} ({output.stat().st_size} bytes, sizes {', '.join(map(str, SIZES))})")


if __name__ == "__main__":
    main()

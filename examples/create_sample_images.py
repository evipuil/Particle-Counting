"""Create three synthetic TIFF images for the example workflow."""

from pathlib import Path

import cv2
import numpy as np


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / "Images" / "EXAMPLE-1-1"
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(1, 4):
        image = np.full((1740, 2320), 20, dtype=np.uint8)
        for x, y, radius in [(400, 400, 20), (1000, 700, 40), (1700, 1100, 80)]:
            cv2.circle(image, (x + 10 * index, y), radius, 220, thickness=-1)
        destination = folder / f"sample_{index:02d}.tif"
        if destination.exists():
            raise FileExistsError(f"Image already exists: {destination}")
        if not cv2.imwrite(str(destination), image):
            raise OSError(f"Could not write {destination}")
    print(f"Created three synthetic images in {folder}")


if __name__ == "__main__":
    main()

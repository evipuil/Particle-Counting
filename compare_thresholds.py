"""Compare particle segmentation thresholds with annotated images."""

from settings import (
    rolling_ball_size, detect_dark_particles,
    image_width_mm, image_height_mm, camera_width_pixels, camera_height_pixels,
    diameter_multiplier,
)

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import glob
from skimage import restoration

folder_path = os.path.join("Images", "EXAMPLE-1-1")
threshold_values = [20, 40, 60]
max_images = 3

pixel_size_x_mm = image_width_mm / camera_width_pixels
pixel_size_y_mm = image_height_mm / camera_height_pixels
pixel_size_mm = (pixel_size_x_mm + pixel_size_y_mm) / 2
scale = pixel_size_mm * 1000

print(f"Calculated Scale (Average): {scale:.4f} microns/pixel")

image_paths = sorted(glob.glob(os.path.join(folder_path, "*.tif")))[:max_images]
if not image_paths:
    raise FileNotFoundError("No images found in the specified folder.")

fig, axes = plt.subplots(len(threshold_values), len(image_paths),
                         figsize=(5 * len(image_paths), 4 * len(threshold_values)), squeeze=False)

for row_idx, thresh_val in enumerate(threshold_values):
    for col_idx, image_path in enumerate(image_paths):

        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        scale_factor = 0.10
        small = cv2.resize(image, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)
        background_small = restoration.rolling_ball(small, radius=rolling_ball_size)
        background = cv2.resize(background_small, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR)

        subtracted = image.astype(np.int16) - background.astype(np.int16)
        subtracted[subtracted < 0] = 0
        image_sub = subtracted.astype(np.uint8)

        image_enhanced = cv2.convertScaleAbs(image_sub, alpha=1, beta=0.5)

        if detect_dark_particles:
            _, binary = cv2.threshold(image_enhanced, thresh_val, 255, cv2.THRESH_BINARY_INV)
        else:
            _, binary = cv2.threshold(image_enhanced, thresh_val, 255, cv2.THRESH_BINARY)

        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        image_with_contours = cv2.cvtColor(image_sub, cv2.COLOR_GRAY2BGR)
        filtered_contours = []
        particle_sizes = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area == 0:
                continue
            diameter = np.sqrt(4 * area / np.pi)
            size_in_microns = diameter_multiplier * diameter * scale
            if size_in_microns >= 10:
                filtered_contours.append(contour)
                particle_sizes.append(size_in_microns)

                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    cv2.putText(image_with_contours,
                                f"{size_in_microns:.1f} microns",
                                (cX, cY),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,
                                (0, 0, 255),
                                2)

        cv2.drawContours(image_with_contours, filtered_contours, -1, (0, 255, 0), 1)

        image_rgb = cv2.cvtColor(image_with_contours, cv2.COLOR_BGR2RGB)

        ax = axes[row_idx, col_idx]
        ax.imshow(image_rgb)
        if row_idx == 0:
            ax.set_title(os.path.basename(image_path), fontsize=9)
        if col_idx == 0:
            ax.set_ylabel(f"T={thresh_val}", fontsize=9)
        ax.axis("off")

plt.tight_layout()
os.makedirs("output", exist_ok=True)
plt.savefig(os.path.join("output", "threshold_comparison.png"), dpi=150)
plt.show()

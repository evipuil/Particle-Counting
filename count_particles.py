"""Count particles in a single sample and export a summary."""

from settings import (
    threshold_value, rolling_ball_size, detect_dark_particles,
    image_width_mm, image_height_mm, camera_width_pixels, camera_height_pixels,
    diameter_multiplier,
)

import os
import cv2
import numpy as np
import glob
import csv
from skimage import restoration

beakerWeight1 = float(input("Enter beaker weight 1: "))
beakerWeight2 = float(input("Enter beaker weight 2: "))
effluentVolume = float(input("Enter effluent volume (ml): "))
lotNumber = input("Enter lot number: ")
sampleNumber = input("Enter sample number: ")
filterNumber = input("Enter filter number: ")
folderPath = os.path.join("Images", lotNumber + "-" + sampleNumber + "-" + filterNumber)
containerVolume = beakerWeight2 - beakerWeight1

pixel_size_x_mm = image_width_mm / camera_width_pixels
pixel_size_y_mm = image_height_mm / camera_height_pixels
pixel_size_mm = (pixel_size_x_mm + pixel_size_y_mm) / 2
scale = pixel_size_mm * 1000

image_paths = sorted(glob.glob(os.path.join(folderPath, "*.tif")))
if not image_paths:
    raise FileNotFoundError("No images found in the specified folder.")

counts_per_image = []

for run_number, image_path in enumerate(image_paths, start=1):

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
        _, binary = cv2.threshold(image_enhanced, threshold_value, 255, cv2.THRESH_BINARY_INV)
    else:
        _, binary = cv2.threshold(image_enhanced, threshold_value, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    count_10 = 0
    count_25 = 0
    count_50 = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area == 0:
            continue
        diameter = np.sqrt(4 * area / np.pi)
        size_in_microns = diameter_multiplier * diameter * scale

        if size_in_microns >= 10:
            count_10 += 1
        if size_in_microns >= 25:
            count_25 += 1
        if size_in_microns >= 50:
            count_50 += 1

    per_ml = [c / effluentVolume for c in [count_10, count_25, count_50]]
    per_device = [c * containerVolume / effluentVolume for c in [count_10, count_25, count_50]]

    counts_per_image.append({
        "Lot Number": lotNumber,
        "Sample Number": sampleNumber,
        "Filter Number": filterNumber,
        "Beaker Wt. 1": beakerWeight1,
        "Beaker Wt. 2": beakerWeight2,
        "Effluent Volume": effluentVolume,
        ">=10 um": count_10,
        ">=25 um": count_25,
        ">=50 um": count_50,
        ">=10 um/ml": per_ml[0],
        ">=25 um/ml": per_ml[1],
        ">=50 um/ml": per_ml[2],
        ">=10 um/device": per_device[0],
        ">=25 um/device": per_device[1],
        ">=50 um/device": per_device[2]
    })

total_10 = sum(row[">=10 um"] for row in counts_per_image)
total_25 = sum(row[">=25 um"] for row in counts_per_image)
total_50 = sum(row[">=50 um"] for row in counts_per_image)

total_per_ml = [c / effluentVolume for c in [total_10, total_25, total_50]]
total_per_device = [c * containerVolume / effluentVolume for c in [total_10, total_25, total_50]]

summary_row = {
    "Lot Number": lotNumber,
    "Sample Number": sampleNumber,
    "Filter Number": filterNumber,
    "Beaker Wt. 1": beakerWeight1,
    "Beaker Wt. 2": beakerWeight2,
    "Effluent Volume": effluentVolume,
    ">=10 um": total_10,
    ">=25 um": total_25,
    ">=50 um": total_50,
    ">=10 um/ml": total_per_ml[0],
    ">=25 um/ml": total_per_ml[1],
    ">=50 um/ml": total_per_ml[2],
    ">=10 um/device": total_per_device[0],
    ">=25 um/device": total_per_device[1],
    ">=50 um/device": total_per_device[2]
}

csv_file = os.path.join(os.getcwd(), "datasheet.csv")
file_exists = os.path.isfile(csv_file)

with open(csv_file, mode="a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary_row.keys()))
    if not file_exists:
        writer.writeheader()
    writer.writerow(summary_row)

print(f"Summary counts appended to {csv_file}")

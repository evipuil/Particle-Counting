"""Process multiple samples and export consolidated particle counts."""

from settings import (
    threshold_value, rolling_ball_size, detect_dark_particles,
    image_width_mm, image_height_mm, camera_width_pixels, camera_height_pixels,
    diameter_multiplier, sampling_multiplier,
)

import os
import cv2
import numpy as np
import glob
import csv
from skimage import restoration

pixel_size_x_mm = image_width_mm / camera_width_pixels
pixel_size_y_mm = image_height_mm / camera_height_pixels
pixel_size_mm = (pixel_size_x_mm + pixel_size_y_mm) / 2
scale = pixel_size_mm * 1000

runs_info = []
study = input("Enter the study: ")
cohort = input("Enter the cohort: ")

while True:
    stop_check = input("\nType 'stop' to finish input or press Enter to add a new run: ").strip().lower()
    if stop_check == "stop":
        break

    beakerWeight1 = float(input("Enter beaker weight 1: "))
    beakerWeight2 = float(input("Enter beaker weight 2: "))
    effluentVolume = float(input("Enter effluent volume (ml): "))
    lotNumber = input("Enter lot number: ")
    sampleNumber = input("Enter sample number: ")
    filterNumber = input("Enter filter number: ")
    folderPath = os.path.join("Images", study, cohort, lotNumber + "-" + sampleNumber + "-" + filterNumber)

    runs_info.append({
        "lotNumber": lotNumber,
        "sampleNumber": sampleNumber,
        "filterNumber": filterNumber,
        "beakerWeight1": beakerWeight1,
        "beakerWeight2": beakerWeight2,
        "effluentVolume": effluentVolume,
        "folderPath": folderPath
    })

print(f"\nCollected {len(runs_info)} runs. Processing all now...\n")

all_summaries = []

for run in runs_info:
    lotNumber = run["lotNumber"]
    sampleNumber = run["sampleNumber"]
    filterNumber = run["filterNumber"]
    beakerWeight1 = run["beakerWeight1"]
    beakerWeight2 = run["beakerWeight2"]
    effluentVolume = run["effluentVolume"]
    folderPath = run["folderPath"]
    containerVolume = beakerWeight2 - beakerWeight1

    image_paths = sorted(glob.glob(os.path.join(folderPath, "*.tif")))
    if not image_paths:
        print(f"No images found for {lotNumber}-{sampleNumber}-{filterNumber}. Skipping...")
        continue

    counts_per_image = []

    for image_path in image_paths:
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

        counts_per_image.append({
            ">=10 um": count_10,
            ">=25 um": count_25,
            ">=50 um": count_50
        })

    total_10 = sum(row[">=10 um"] for row in counts_per_image) * sampling_multiplier
    total_25 = sum(row[">=25 um"] for row in counts_per_image) * sampling_multiplier
    total_50 = sum(row[">=50 um"] for row in counts_per_image) * sampling_multiplier

    total_per_ml = [total_10 / effluentVolume, total_25 / effluentVolume, total_50 / effluentVolume]
    total_per_device = [total_10 * containerVolume / effluentVolume,
                        total_25 * containerVolume / effluentVolume,
                        total_50 * containerVolume / effluentVolume]

    summary_row = {
        "Study": study,
        "Cohort": cohort,
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

    all_summaries.append(summary_row)
    print(f"Processed run: {lotNumber}-{sampleNumber}-{filterNumber}")

if all_summaries:
    csv_file = os.path.join(os.getcwd(), "batch_results.csv")
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_summaries[0].keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerows(all_summaries)

    print(f"\nAll {len(all_summaries)} runs appended to {csv_file}")
else:
    print("No valid runs to save.")

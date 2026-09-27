# Particle Counting

Python image analysis for counting and measuring particles in microscopy images. The workflow combines background correction, threshold segmentation, contour measurement, and CSV reporting for individual samples or batches.

Originally developed in August 2025, this project has been modified for public availability. Company-identifying information, internal sample identifiers, original images, and production records have been removed. The included example uses synthetic images and generic sample labels.

## Features

- Rolling-ball background subtraction and morphological image cleanup.
- Configurable image calibration, threshold, and particle polarity.
- Cumulative particle counts at 10, 25, and 50 micrometers.
- Volume-normalized summaries for individual samples and batches.
- Annotated threshold comparisons for reviewing segmentation.
- Sample-folder creation from a CSV manifest.

## Development Timeline

| Period | Milestone |
| --- | --- |
| August 7, 2025 | Image enhancement, contour detection, and particle-sizing exploration. |
| August 12–13, 2025 | Refinement of image processing, size classification, and threshold selection. |
| August 14, 2025 | Consolidation of local processing scripts and annotated threshold comparisons. |
| August 15, 2025 | Single-sample reporting, batch processing, and sample-folder organization. |
| September 2026 | Preparation for public availability, including removal of company-identifying material, generic examples, and updated documentation. |

The original milestones are based on the saved project files and their modification dates.

## Installation

Use Python 3.12.

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install the packages:

```bash
python -m pip install -r requirements.txt
```

## Example

Run commands from the project directory.

```bash
python examples/create_sample_images.py
python compare_thresholds.py
python count_particles.py
```

The example creates three synthetic TIFF images containing three bright circular particles each. The threshold comparison displays annotated images and saves a figure to `output/threshold_comparison.png`.

Enter these values for the single-sample example:

| Input | Value |
| --- | --- |
| Beaker weight 1 | `10` |
| Beaker weight 2 | `20` |
| Effluent volume (ml) | `1` |
| Lot number | `EXAMPLE` |
| Sample number | `1` |
| Filter number | `1` |

The summary is appended to `datasheet.csv`. With the included settings, the synthetic example produces cumulative counts of 9, 6, and 3 at the three size thresholds.

## Sample Organization

Single-sample processing reads TIFF images from:

```text
Images/
  EXAMPLE-1-1/
    sample_01.tif
    sample_02.tif
    sample_03.tif
```

Create additional sample folders from a manifest:

```bash
python make_folders.py examples/sample_manifest.csv
```

For batch processing, place folders under a study and cohort:

```text
Images/
  STUDY-A/
    GROUP-1/
      EXAMPLE-1-1/
        sample_01.tif
```

```bash
python make_folders.py examples/sample_manifest.csv --root Images/STUDY-A/GROUP-1
python batch_count.py
```

Enter the study and cohort, then the measurements and identifiers for each sample. Type `stop` when all samples have been entered. Results are appended to `batch_results.csv`.

## Analysis Settings

Edit `settings.py` to set image calibration and processing parameters. The public example is configured for bright particles. Set `detect_dark_particles` to `True` to select inverse thresholding.

The image dimensions and field of view determine the average micrometers per pixel. Contour area is converted to an equivalent circular diameter, then multiplied by `diameter_multiplier`. The supplied value of `2.0` preserves the original sizing calculation. Batch totals also apply `sampling_multiplier`, supplied as `10.0`; single-sample totals are unscaled.

Counts are cumulative: a particle at least 50 micrometers contributes to all three size categories. Counts per milliliter divide totals by the entered effluent volume. Counts per device multiply that result by the volume represented by the difference between the two beaker weights, using a density of 1 gram per milliliter.

In `compare_thresholds.py`, set `folder_path`, `threshold_values`, and `max_images` to choose the comparison. Source images, generated reports, and local environments are excluded from version control.

## Project Files

| File | Purpose |
| --- | --- |
| `count_particles.py` | Single-sample analysis and CSV summary. |
| `batch_count.py` | Multiple-sample analysis and consolidated reporting. |
| `compare_thresholds.py` | Annotated segmentation comparison. |
| `settings.py` | Shared calibration and processing parameters. |
| `make_folders.py` | Sample-folder creation from a manifest. |
| `examples/create_sample_images.py` | Synthetic demonstration images. |

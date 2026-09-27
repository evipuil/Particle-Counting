"""Create sample folders from a generic sample manifest."""

import argparse
import csv
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path("Images"))
    parser.add_argument("--filters", type=int, default=3)
    args = parser.parse_args()
    if args.filters < 1:
        parser.error("--filters must be positive")
    with args.manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lot = row["lotnumber"].strip()
            if not lot or any(char in lot for char in '/\\:') or lot in {'.', '..'}:
                parser.error("Lot identifiers must be plain folder names")
            samples = int(row["num_samples"])
            if samples < 1:
                parser.error("num_samples must be positive")
            for sample in range(1, samples + 1):
                for filter_number in range(1, args.filters + 1):
                    (args.root / f"{lot}-{sample}-{filter_number}").mkdir(parents=True, exist_ok=True)
    print(f"Sample folders created under {args.root}")


if __name__ == "__main__":
    main()

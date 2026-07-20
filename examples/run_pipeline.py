#!/usr/bin/env python3
"""
Minimal example: Run the MSI Isotope Detection Pipeline
========================================================

Before running, update the configuration constants in pipeline.py:
  - MSI_INPUT_FOLDER: path to your .h5ad files
  - MSI_SAMPLE_FILES: list of .h5ad filenames
  - MSI_SAMPLE_IDS: short identifiers for each sample

Usage:
    python examples/run_pipeline.py
"""

import sys
import os

# Add src to path if running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from msi_isotope_pipeline.pipeline import main


if __name__ == "__main__":
    print("=" * 60)
    print("MSI Isotope Detection Pipeline v2.0.0")
    print("=" * 60)

    # Run the full pipeline
    weights, matcher, matching_results, isotope_results, hierarchy = main()

    # Print calibrated weights
    print("\n--- Calibrated Metric Weights ---")
    for metric, weight in weights.items():
        print(f"  {metric:35s} {weight:.4f}")

    # Print summary
    if isotope_results is not None:
        print(f"\n--- Results ---")
        print(f"  Confirmed isotope/adduct pairs: {len(isotope_results)}")
    if hierarchy is not None:
        print(f"  Parent-children families:        {len(hierarchy)}")

    print("\nDone. Check the output directory for CSV files.")

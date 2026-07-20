"""
MSI Isotope & Adduct Detection Pipeline
===============================

A spatial-statistics-driven pipeline for identifying isotope and adduct
relationships in Mass Spectrometry Imaging (MSI) data using machine-learned
similarity weights.

Main classes:
    - CrossValidatedCalibrator: Learns optimal metric weights from control pairs
    - MzIsotopeMatcher: Scores candidate m/z pairs across samples

Main functions:
    - identify_isotopes: Filters for reproducible isotope relationships
    - build_strict_hierarchy: Organizes isotopes into parent-children families
    - main: Runs the complete pipeline end-to-end
"""

__version__ = "2.0.0"

from .pipeline import (
    CrossValidatedCalibrator,
    MzIsotopeMatcher,
    identify_isotopes,
    build_strict_hierarchy,
    main,
)

__all__ = [
    "CrossValidatedCalibrator",
    "MzIsotopeMatcher",
    "identify_isotopes",
    "build_strict_hierarchy",
    "main",
]

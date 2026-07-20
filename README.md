# MSI Isotope & adduct Detection Pipeline

> **Combined Pipeline: ML Calibration → m/z Isotope Detection & Hierarchy**
>
> A spatial-statistics-driven pipeline for identifying isotope and adduct relationships in Mass Spectrometry Imaging (MSI) data using machine-learned similarity weights.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [Pipeline Architecture](#pipeline-architecture)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Pipeline Stages in Detail](#pipeline-stages-in-detail)
  - [Calibration Phase](#calibration-phase)
  - [Stage 1 — Spatial Pattern Matching](#stage-1--spatial-pattern-matching)
  - [Stage 2 — Isotope Identification](#stage-2--isotope-identification)
  - [Stage 3 — Parent–Children Hierarchy](#stage-3--parentchildren-hierarchy)
- [Output Files](#output-files)
- [Spatial Similarity Metrics](#spatial-similarity-metrics)
- [Mass Differences Reference](#mass-differences-reference)
- [Contributing](#contributing)
- [License](#license)
- [Citation](#citation)

---

## Overview

This pipeline automatically discovers **isotope** and **adduct** relationships between m/z features in spatially resolved mass spectrometry imaging (MSI) datasets stored in [AnnData (`.h5ad`)](https://anndata.readthedocs.io/) format.

**Key idea:** Two m/z features whose mass difference matches a known isotope/adduct pattern *and* whose spatial intensity distributions are highly similar across multiple biological replicates are likely to represent the same underlying molecule.

The pipeline:

1. **Learns optimal similarity weights** from expert-curated positive/negative control pairs via cross-validated logistic regression.
2. **Scores every candidate m/z pair** (those within tolerance of a known mass difference) using 9 calibrated spatial similarity metrics.
3. **Filters candidates** that are consistent across a minimum number of biological replicates.
4. **Organizes** confirmed isotope/adduct relationships into parent–children hierarchies.

---

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   CALIBRATION PHASE                      │
│  Positive/Negative control pairs → Logistic Regression   │
│  → ReLU-rectified, normalized weights (9 metrics)        │
└────────────────────────┬─────────────────────────────────┘
                         │ calibrated_weights
                         ▼
┌──────────────────────────────────────────────────────────┐
│              STAGE 1: SPATIAL PATTERN MATCHING            │
│  For each sample:                                        │
│    • Find candidate m/z pairs (mass diff ± tolerance)    │
│    • Extract spatial signatures (importance, histogram,  │
│      radial profile, Moran's I)                          │
│    • Score pairs with calibrated weights                 │
│  Output: mz_to_mz_isotope_candidates.csv                │
└────────────────────────┬─────────────────────────────────┘
                         │ scored pairs
                         ▼
┌──────────────────────────────────────────────────────────┐
│            STAGE 2: ISOTOPE IDENTIFICATION               │
│  Filter pairs: score > threshold AND present in ≥ N      │
│  animals. Aggregate statistics across replicates.        │
│  Output: identified_isotopes.csv                         │
└────────────────────────┬─────────────────────────────────┘
                         │ confirmed isotopes
                         ▼
┌──────────────────────────────────────────────────────────┐
│         STAGE 3: PARENT–CHILDREN HIERARCHY               │
│  Group confirmed isotopes into families:                 │
│  Parent → [M+1], [M+2], [NH4], [Na], [K]                │
│  Output: parent_children_hierarchy.csv                   │
└──────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
msi-isotope-pipeline/
│
├── README.md                        # This file
├── LICENSE                          # MIT License
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package installation script
├── .gitignore                       # Git ignore rules
│
├── src/
│   └── msi_isotope_pipeline/
│       ├── __init__.py              # Package init
│       └── pipeline.py              # Main pipeline script
│
├── docs/
│   ├── configuration.md            # Detailed configuration reference
│   ├── metrics.md                  # Spatial similarity metrics explained
│   ├── pipeline_details.md         # In-depth pipeline documentation
│   └── output_schema.md           # Output CSV column definitions
│
├── examples/
│   └── run_pipeline.py             # Minimal usage example
│
├── tests/
│   └── __init__.py                 # Test package placeholder
│
└── output/                         # Default output directory (git-ignored)
    └── .gitkeep
```

---

## Installation

### Prerequisites

- Python ≥ 3.9
- MSI data in `.h5ad` (AnnData) format with `x_um` and `y_um` columns in `.obs`

### Steps

```bash
# Clone the repository
git clone https://github.com/<your-username>/msi-isotope-pipeline.git
cd msi-isotope-pipeline

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install as an editable package
pip install -e .
```

---

## Configuration

All configurable parameters are defined as module-level constants at the top of `pipeline.py`. Update these before running:

| Parameter | Default | Description |
|---|---|---|
| `MSI_PIXEL_SIZE` | `60` | Pixel size in μm |
| `MSI_INPUT_FOLDER` | *(path)* | Directory containing `.h5ad` sample files |
| `MSI_SAMPLE_FILES` | *(list)* | Filenames of the `.h5ad` sample files |
| `MSI_SAMPLE_IDS` | *(list)* | Short identifiers for each sample |
| `MASS_DIFFS` | *(dict)* | Expected mass differences for isotope/adduct types |
| `MASS_DIFF_TOLERANCE` | `0.01` Da | Tolerance window for mass difference matching |
| `MIN_ANIMALS` | `12` | Minimum biological replicates for confirmation |
| `MIN_SCORE` | `60` | Minimum score percentage threshold |
| `N_FOLDS` | `10` | Number of cross-validation folds for calibration |
| `HIERARCHY_PRECISION` | `4` | Decimal precision for m/z rounding in hierarchy |
| `HIERARCHY_TOLERANCE` | `0.01` Da | Tolerance for hierarchy child matching |
| `OUTPUT_DIR` | `./mz_isotope_results` | Directory for all output files |

> See [`docs/configuration.md`](docs/configuration.md) for a full reference including the positive/negative control pairs.

---

## Usage

### Run the full pipeline

```bash
cd src/msi_isotope_pipeline
python pipeline.py
```

### Programmatic usage

```python
from msi_isotope_pipeline.pipeline import main

calibrated_weights, matcher, matching_results, isotope_results, hierarchy_results = main()
```

### Run individual stages

```python
from msi_isotope_pipeline.pipeline import (
    CrossValidatedCalibrator,
    MzIsotopeMatcher,
    identify_isotopes,
    build_strict_hierarchy
)

# Phase 0: Calibrate weights
calibrator = CrossValidatedCalibrator()
weights = calibrator.run()

# Stage 1: Match m/z pairs
matcher = MzIsotopeMatcher(calibrated_weights=weights, output_dir='./results')
matcher.load_all_data()
results = matcher.run_analysis()

# Stage 2: Identify isotopes
isotopes, filtered = identify_isotopes(results, min_animals=12, min_score=60)

# Stage 3: Build hierarchy
hierarchy = build_strict_hierarchy('./results/identified_isotopes.csv')
```

---

## Pipeline Stages in Detail

### Calibration Phase

**Goal:** Learn optimal weights for combining 9 spatial similarity metrics.

- **Input:** Expert-curated positive control pairs (20 known isotope/adduct relationships) and negative control pairs (18 known non-relationships).
- **Method:** L2-regularized logistic regression (no intercept) trained via 10-fold cross-validation across biological samples.
- **Post-processing:** Coefficients are ReLU-rectified (`max(0, coef)`) and normalized to sum to 1.0. Negative coefficients are zeroed because all metrics are designed such that higher values indicate greater spatial co-localization.
- **Output:** A dictionary of 9 metric weights (summing to 1.0) and per-fold AUC.

### Stage 1 — Spatial Pattern Matching

**Goal:** Score every candidate m/z pair in every sample.

1. For each sample, identify all m/z pairs whose mass difference falls within ±0.01 Da of a known isotope/adduct mass shift.
2. Extract a **spatial signature** for each involved m/z feature:
   - **Biological importance map** — blends normalized local variance (50%) and normalized value magnitude (50%)
   - **2D spatial histogram** — 10×10 grid of average intensities
   - **Radial intensity profile** — 10-ring profile from centroid outward
   - **Moran's I** — spatial autocorrelation index (k=8 neighbors)
3. Compute 9 similarity metrics between each candidate pair and combine them using the calibrated weights.
4. Normalize each pair's score as a percentage of the maximum self-similarity score.
5. Parallelized via `joblib` for both signature extraction and pair scoring.

### Stage 2 — Isotope Identification

**Goal:** Filter for biologically reproducible isotope relationships.

- m/z values are rounded to 4 decimal places for cross-sample matching.
- A candidate pair is confirmed if:
  - Its **score percentage > `MIN_SCORE`** (default 60%)
  - It appears in **≥ `MIN_ANIMALS`** biological replicates (default 12 out of 16)
- Aggregated statistics (mean, median, min, max, std of score) are reported.

### Stage 3 — Parent–Children Hierarchy

**Goal:** Organize confirmed isotopes into parent-centered families.

- For each unique m/z (sorted ascending), check whether other confirmed m/z values exist at the expected mass offsets (M+1, M+2, NH₄, Na, K).
- Assign children greedily (closest match within tolerance), preventing a child from being assigned to multiple parents.
- Output: A table with one row per parent and columns `Child_1` through `Child_5` corresponding to each mass difference type.

---

## Output Files

All outputs are saved to `OUTPUT_DIR` (default: `./mz_isotope_results/`).

| File | Stage | Description |
|---|---|---|
| `mz_to_mz_isotope_candidates.csv` | 1 | All scored candidate pairs across all samples |
| `mz_matching_summary.csv` | 1 | Per-sample summary statistics |
| `identified_isotopes.csv` | 2 | Confirmed isotope/adduct pairs passing filters |
| `identified_isotopes_detailed.csv` | 2 | Per-sample detail for confirmed pairs |
| `parent_children_hierarchy.csv` | 3 | Parent–children family groupings |

### Column Definitions — `mz_to_mz_isotope_candidates.csv`

| Column | Description |
|---|---|
| `mz_1`, `mz_2` | The two m/z feature identifiers |
| `mz_difference` | Absolute mass difference (Da) |
| `sample_id` | Biological sample identifier |
| `mass_diff_type` | Matched isotope/adduct type |
| `combined_score` | Weighted similarity score |
| `score_percentage` | Score as % of the maximum self-score |
| `mz_1_self_score`, `mz_2_self_score` | Self-similarity scores for each m/z |
| `mz_1_morans_i`, `mz_2_morans_i` | Moran's I values for each m/z |
| `intensity_ratio_consistency` | Consistency of pixel-wise intensity ratios |
| `value_correlation` | Pearson correlation of nonzero values |
| `peak_colocalization` | IoU of top-20% intensity pixels |
| `importance_iou` | IoU of biological importance maps |
| `importance_correlation` | Pearson correlation of importance maps |
| `spatial_hist_corr` | Correlation of 2D spatial histograms |
| `value_iou` | Value-weighted IoU |
| `morans_similarity` | Similarity of Moran's I values |
| `radial_profile_corr` | Correlation of radial intensity profiles |

---

## Spatial Similarity Metrics

The pipeline computes **9 complementary spatial similarity metrics**, divided into two groups:

### Coordinate-Based Metrics (6)

| # | Metric | Range | What it measures |
|---|---|---|---|
| 1 | Intensity Ratio Consistency | [0, 1] | Stability of pixel-wise intensity ratios above the 10th percentile |
| 2 | Value Correlation | [0, 1] | Pearson correlation of nonzero pixel intensities |
| 3 | Peak Colocalization | [0, 1] | IoU overlap of top-20% intensity pixels |
| 4 | Importance IoU | [0, 1] | IoU of biological importance maps (local variance + magnitude) |
| 5 | Importance Correlation | [0, 1] | Pearson correlation of importance maps |
| 6 | Value IoU | [0, 1] | Soft IoU using min/max of raw intensity values |

### Descriptor-Based Metrics (3)

| # | Metric | Range | What it measures |
|---|---|---|---|
| 7 | Spatial Histogram Correlation | [0, 1] | Correlation of 10×10 spatial bin averages |
| 8 | Moran's I Similarity | [0, 1] | Closeness of spatial autocorrelation indices (1 − |I₁ − I₂|) |
| 9 | Radial Profile Correlation | [0, 1] | Correlation of centroid-to-periphery intensity profiles |

All metrics are bounded to [0, 1] by clamping negative correlations to 0.

---

## Mass Differences Reference

| Relationship | Mass Difference (Da) |
|---|---|
| Isotope (M+1) | 1.0033 |
| Isotope (M+2) | 2.0067 |
| Adduct (NH₄⁺) | 17.0265 |
| Adduct (Na⁺) | 21.982 |
| Adduct (K⁺) | 37.9555 |

Default tolerance: ±0.01 Da

---

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE) for details.

---

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{msi_isotope_pipeline,
  title  = {MSI Isotope Detection Pipeline},
  author = {Jarrahi, Alex(Amin)},
  year   = {2026},
  url    = {https://github.com/Amin-Jarrahi/msi-isotope-pipeline}
}
```

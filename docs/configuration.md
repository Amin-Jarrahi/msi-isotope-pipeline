# Configuration Reference

All configuration is defined as module-level constants at the top of `pipeline.py`. This document provides a complete reference.

---

## Data Input

### `MSI_PIXEL_SIZE`
- **Type:** `int`
- **Default:** `60`
- **Description:** The pixel size of the MSI acquisition in micrometers (μm). Used to interpret spatial coordinates from the `.h5ad` files.

### `MSI_INPUT_FOLDER`
- **Type:** `str`
- **Default:** *(dataset-specific path)*
- **Description:** Absolute or relative path to the directory containing all `.h5ad` sample files.

### `MSI_SAMPLE_FILES`
- **Type:** `list[str]`
- **Default:** *(16 filenames)*
- **Description:** List of `.h5ad` filenames within `MSI_INPUT_FOLDER`. Each file represents one biological replicate.

### `MSI_SAMPLE_IDS`
- **Type:** `list[str]`
- **Default:** *(16 short IDs)*
- **Description:** Short identifiers for each sample, used in output CSVs and logging. Must be in the same order as `MSI_SAMPLE_FILES`.

---

## Mass Difference Parameters

### `MASS_DIFFS`
- **Type:** `dict[str, float]`
- **Default:**
  ```python
  {
      'M+1': 1.0033,
      'M+2': 2.0067,
      'NH4': 17.0265,
      'Na':  21.982,
      'K':   37.9555,
  }
  ```
- **Description:** Dictionary mapping isotope/adduct relationship names to their expected mass differences in Daltons.

### `MASS_DIFF_TOLERANCE`
- **Type:** `float`
- **Default:** `0.01`
- **Description:** Tolerance (in Da) for matching observed mass differences to expected values. A pair with mass difference `d` matches type `t` if `|d - MASS_DIFFS[t]| ≤ MASS_DIFF_TOLERANCE`.

---

## Calibration Parameters

### `N_FOLDS`
- **Type:** `int`
- **Default:** `10`
- **Description:** Number of cross-validation folds used in the logistic regression calibration. Each fold holds out samples to test generalization.

### `POSITIVE_CONTROL_PAIRS`
- **Type:** `list[tuple[float, float]]`
- **Default:** *(20 m/z pairs)*
- **Description:** Expert-curated m/z pairs known to be true isotope/adduct relationships. Used as positive training examples.

### `NEGATIVE_CONTROL_PAIRS`
- **Type:** `list[tuple[float, float]]`
- **Default:** *(18 m/z pairs)*
- **Description:** Expert-curated m/z pairs known NOT to be isotope/adduct relationships despite having matching mass differences. Used as negative training examples.

---

## Filtering Parameters

### `MIN_ANIMALS`
- **Type:** `int`
- **Default:** `12`
- **Description:** Minimum number of biological replicates (samples) in which a candidate pair must appear with a passing score to be confirmed as an isotope relationship. Out of 16 total samples, this requires 75% consistency.

### `MIN_SCORE`
- **Type:** `float`
- **Default:** `60`
- **Description:** Minimum score percentage threshold. Candidate pairs scoring below this in any sample are excluded from that sample's count.

---

## Hierarchy Parameters

### `HIERARCHY_PRECISION`
- **Type:** `int`
- **Default:** `4`
- **Description:** Number of decimal places for rounding m/z values when building the parent–children hierarchy. Controls matching granularity.

### `HIERARCHY_TOLERANCE`
- **Type:** `float`
- **Default:** `0.01`
- **Description:** Tolerance (in Da) for matching child m/z values to expected offsets from parent m/z in the hierarchy building stage.

---

## Output

### `OUTPUT_DIR`
- **Type:** `str`
- **Default:** `'./mz_isotope_results'`
- **Description:** Directory where all output CSV files are saved. Created automatically if it does not exist.

---

## Spatial Signature Parameters (Hardcoded)

These values are embedded in the pipeline functions and are not currently exposed as top-level constants:

| Parameter | Value | Location | Description |
|---|---|---|---|
| Importance blend | 50% variance, 50% magnitude | `compute_importance_map()` | Weight balance for biological importance maps |
| Histogram bins | 10 × 10 | `compute_spatial_signature()` | Grid resolution for spatial histogram |
| Radial bins | 10 | `compute_spatial_signature()` | Number of rings for radial intensity profile |
| KNN neighbors | 8 | `compute_spatial_signature()` | Neighbors for Moran's I computation |
| Intensity threshold | Top 20% | `peak_colocalization()` | Percentile cutoff for peak pixel selection |
| Ratio threshold | 10th percentile | `intensity_ratio_consistency()` | Minimum intensity for ratio computation |
| Parallel jobs | -1 (all cores) | `MzIsotopeMatcher` | Number of parallel workers |

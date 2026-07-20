# Pipeline Details

This document provides an in-depth technical walkthrough of each pipeline stage.

---

## Overview

The pipeline runs four sequential stages:

| Stage | Class/Function | Purpose |
|---|---|---|
| 0 — Calibration | `CrossValidatedCalibrator` | Learn metric weights from control pairs |
| 1 — Matching | `MzIsotopeMatcher` | Score all candidate m/z pairs per sample |
| 2 — Identification | `identify_isotopes()` | Filter for reproducible relationships |
| 3 — Hierarchy | `build_strict_hierarchy()` | Group into parent–children families |

---

## Stage 0: Calibration (`CrossValidatedCalibrator`)

### Purpose

Determine how much weight each of the 9 spatial similarity metrics should receive in the combined score. Different metrics may be more or less informative depending on the data characteristics.

### Algorithm

1. **Data Collection:** For each of the 16 biological samples, compute the 9 similarity metrics for every positive control pair (label = 1) and every negative control pair (label = 0).

2. **Feature Matrix Construction:** Build a matrix `X` of shape `(n_pairs × n_samples, 9)` and a label vector `y`.

3. **Cross-Validation:** Perform 10-fold cross-validation using `StratifiedKFold`:
   - Train L2-regularized logistic regression (`C=1.0`, `fit_intercept=False`) on the training fold.
   - Predict probabilities on the test fold.
   - Compute ROC AUC for the fold.
   - Store the model coefficients.

4. **Weight Aggregation:**
   - Average coefficients across all folds.
   - Apply ReLU: `w = max(0, coef)` — negative weights make no physical sense since all metrics are positively oriented.
   - Normalize: `w = w / sum(w)` so weights sum to 1.0.

5. **Output:** Dictionary mapping metric names to weights, plus per-fold AUC scores.

### Why No Intercept?

The logistic regression is fit without an intercept because we want the decision to be based purely on the relative metric values. An intercept would introduce a bias toward positive or negative classification independent of spatial similarity.

### Control Pair Selection

- **Positive pairs** (20 pairs): Known isotope/adduct relationships confirmed by domain experts (e.g., verified M+1 isotopes).
- **Negative pairs** (18 pairs): m/z pairs whose mass difference matches an isotope/adduct pattern but are known to be unrelated molecules with coincidental mass spacing.

---

## Stage 1: Spatial Pattern Matching (`MzIsotopeMatcher`)

### Data Loading

For each `.h5ad` file:
1. Read with `scanpy.read_h5ad()`.
2. Extract spatial coordinates from `adata.obs[['x_um', 'y_um']]`.
3. Convert to grid positions by dividing by `MSI_PIXEL_SIZE` and rounding.
4. Extract intensity matrix `adata.X` (dense) and feature names from `adata.var_names`.
5. Parse m/z values from feature names (format: `"mz_<value>"`).

### Candidate Pair Discovery

For each sample:
1. Sort all m/z values.
2. For each pair `(mz_i, mz_j)` where `i < j`:
   - Compute `diff = mz_j - mz_i`.
   - Check if `diff` falls within `±MASS_DIFF_TOLERANCE` of any entry in `MASS_DIFFS`.
   - If yes, record the pair and its matched mass difference type.

This step uses an optimized approach: for each m/z, binary search for potential partners at each expected offset.

### Spatial Signature Extraction

For each unique m/z in the candidate list, compute a spatial signature containing:

- **`importance_map`:** Per-pixel biological importance score:
  - Local variance: for each pixel, compute variance of intensity among its k=8 nearest spatial neighbors.
  - Normalize to [0, 1].
  - Blend: `0.5 × normalized_variance + 0.5 × normalized_magnitude`.

- **`spatial_histogram`:** 10×10 grid binning of spatial coordinates, with average intensity per bin. Normalized to sum to 1.

- **`radial_profile`:** 10-ring profile of average intensity vs. distance from intensity-weighted centroid. Normalized to sum to 1.

- **`morans_i`:** Moran's I spatial autocorrelation with k=8 neighbors. Clamped to [0, 1].

Signature extraction is parallelized across m/z features using `joblib.Parallel`.

### Pair Scoring

For each candidate pair, compute all 9 similarity metrics and combine:

```
combined_score = Σ(weight_i × metric_i)
```

Also compute self-similarity scores for each m/z (scoring a feature against itself) to normalize:

```
max_self_score = max(self_score_mz1, self_score_mz2)
score_percentage = (combined_score / max_self_score) × 100
```

Pair scoring is also parallelized via `joblib`.

### Output

- `mz_to_mz_isotope_candidates.csv`: One row per (pair, sample) combination.
- `mz_matching_summary.csv`: Per-sample statistics (total pairs, mean score, etc.).

---

## Stage 2: Isotope Identification (`identify_isotopes`)

### Algorithm

1. **Round m/z values** to `HIERARCHY_PRECISION` decimal places for cross-sample matching.
2. **Group** results by `(mz_1_rounded, mz_2_rounded, mass_diff_type)`.
3. For each group:
   - Count how many samples have `score_percentage > MIN_SCORE`.
   - If count ≥ `MIN_ANIMALS`, mark as confirmed.
   - Compute aggregate statistics: mean, median, min, max, std of score_percentage.
4. **Output confirmed pairs** to `identified_isotopes.csv`.
5. **Output detailed per-sample data** for confirmed pairs to `identified_isotopes_detailed.csv`.

### Rationale for Cross-Sample Filtering

Requiring reproducibility across multiple biological replicates dramatically reduces false positives. A coincidental spatial overlap in one sample is unlikely to repeat across 12+ independent tissue sections.

---

## Stage 3: Parent–Children Hierarchy (`build_strict_hierarchy`)

### Algorithm

1. **Collect** all unique m/z values from confirmed isotope pairs.
2. **Sort** m/z values ascending (process from lightest to heaviest).
3. **Initialize** an assignment tracker to prevent double-assignment.
4. For each m/z (potential parent):
   - For each mass difference type (M+1, M+2, NH4, Na, K):
     - Compute expected child m/z: `parent_mz + mass_diff`.
     - Find the closest unassigned confirmed m/z within `HIERARCHY_TOLERANCE`.
     - If found, assign as child and mark as assigned.
5. **Filter** to parents that have at least one child.
6. **Output** to `parent_children_hierarchy.csv`.

### Greedy Assignment

The algorithm processes parents from lowest to highest m/z and assigns children greedily. Once a child m/z is assigned to a parent, it cannot be reassigned. This prevents the same m/z from appearing as a child of multiple parents.

### Output Format

| Column | Description |
|---|---|
| `Parent_mz` | The parent m/z value |
| `Child_1` | M+1 isotope child (if found) |
| `Child_2` | M+2 isotope child (if found) |
| `Child_3` | NH₄ adduct child (if found) |
| `Child_4` | Na adduct child (if found) |
| `Child_5` | K adduct child (if found) |

Empty cells indicate no confirmed child of that type.

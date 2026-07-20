# Spatial Similarity Metrics

This document provides detailed descriptions of the 9 spatial similarity metrics used by the MSI Isotope Detection Pipeline. All metrics return values in the range [0, 1], where 1 indicates perfect similarity.

---

## Coordinate-Based Metrics

These metrics operate directly on per-pixel intensity values using the shared spatial coordinate system.

### 1. Intensity Ratio Consistency

**Function:** `intensity_ratio_consistency(v1, v2)`

Measures how stable the pixel-wise intensity ratio is between two m/z features.

**Algorithm:**
1. Filter to pixels where both features exceed their respective 10th percentile values.
2. Compute per-pixel ratios `v1[i] / v2[i]`.
3. Calculate `1.0 - coefficient_of_variation(ratios)`, clamped to [0, 1].

**Intuition:** True isotope pairs maintain a relatively constant intensity ratio across all tissue pixels. If the ratio is highly variable, the two features are unlikely to come from the same molecule.

---

### 2. Value Correlation

**Function:** `value_correlation(v1, v2)`

Pearson correlation coefficient of pixel intensities, considering only pixels where at least one feature is nonzero.

**Algorithm:**
1. Select pixels where `v1 > 0` OR `v2 > 0`.
2. Compute Pearson's r on the selected subset.
3. Clamp to [0, 1] (negative correlations → 0).

**Intuition:** Spatially co-localized molecules will have correlated intensity patterns across the tissue.

---

### 3. Peak Colocalization

**Function:** `peak_colocalization(v1, v2)`

Intersection-over-Union (IoU) of the "hot spot" pixels for each feature.

**Algorithm:**
1. Define "peak pixels" as those above the 80th percentile of each feature's intensity distribution.
2. Compute IoU = |intersection| / |union| of the two peak pixel sets.

**Intuition:** Isotope features should have their highest-intensity regions in the same tissue areas.

---

### 4. Importance IoU

**Function:** `importance_iou(imp1, imp2)`

IoU of biological importance maps using a soft, value-weighted formulation.

**Algorithm:**
1. Importance maps are precomputed as `0.5 × normalized_local_variance + 0.5 × normalized_magnitude`.
2. Compute soft IoU: `sum(min(imp1, imp2)) / sum(max(imp1, imp2))`.

**Intuition:** Regions that are biologically "important" (high local variance and/or high magnitude) should overlap between isotope features.

---

### 5. Importance Correlation

**Function:** `importance_correlation(imp1, imp2)`

Pearson correlation of the biological importance maps.

**Algorithm:**
1. Compute Pearson's r between the two importance map vectors.
2. Clamp to [0, 1].

**Intuition:** Complementary to IoU — captures whether importance maps covary even if absolute magnitudes differ.

---

### 6. Value IoU

**Function:** `value_iou(v1, v2)`

Soft IoU computed directly on raw intensity values.

**Algorithm:**
1. Compute `sum(min(v1, v2)) / sum(max(v1, v2))`.

**Intuition:** A more granular measure than peak colocalization — considers the full intensity distribution rather than just binary hot spots.

---

## Descriptor-Based Metrics

These metrics compare compact spatial summaries (descriptors) of each feature.

### 7. Spatial Histogram Correlation

**Function:** `spatial_hist_corr(sig1, sig2)`

Correlation of 2D spatial histogram representations.

**Algorithm:**
1. Spatial coordinates are binned into a 10×10 grid.
2. Average intensity is computed per bin.
3. Pearson's r is computed between the two 100-element histogram vectors.
4. Clamped to [0, 1].

**Intuition:** Captures coarse spatial distribution patterns — are the two features concentrated in the same tissue regions?

---

### 8. Moran's I Similarity

**Function:** `morans_similarity(sig1, sig2)`

Similarity of spatial autocorrelation indices.

**Algorithm:**
1. Moran's I is precomputed for each feature using k=8 nearest-neighbor spatial weights.
2. Similarity = `1.0 - |I₁ - I₂|`, clamped to [0, 1].

**Intuition:** Isotope features should have similar spatial clustering patterns. If one feature is highly clustered (high Moran's I) and the other is spatially random (low Moran's I), they are unlikely to be isotopes.

---

### 9. Radial Profile Correlation

**Function:** `radial_profile_corr(sig1, sig2)`

Correlation of radial intensity profiles measured from each feature's centroid.

**Algorithm:**
1. Compute the intensity-weighted centroid of each feature.
2. Divide the spatial extent into 10 concentric rings.
3. Compute average intensity per ring (normalized to sum to 1).
4. Pearson's r between the two 10-element profile vectors.
5. Clamped to [0, 1].

**Intuition:** Captures the "shape" of spatial distribution — whether intensity falls off from center in a similar pattern for both features.

---

## Weight Calibration

The final similarity score is a weighted sum of all 9 metrics:

$$
S = \sum_{i=1}^{9} w_i \cdot m_i
$$

where weights $$w_i$$ are learned via logistic regression on control pairs and satisfy:

- $$w_i \geq 0$$ (ReLU rectification)
- $$\sum_{i=1}^{9} w_i = 1$$ (normalization)

The score is then expressed as a percentage of the maximum possible self-similarity score.

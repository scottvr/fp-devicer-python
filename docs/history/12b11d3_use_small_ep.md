# Commit: use small epsilon instead of 0 for crossings to account for floating point noise
**Hash:** `12b11d3bf804748040dded692ea2fb168f3ed0ac`  
**Date:** 2026-03-19  

## Editorial Rationale

> exact 0 was replaced by a really small number to account for float noise.

---

## Technical Diffs
```diff
commit 12b11d3bf804748040dded692ea2fb168f3ed0ac
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 10:16:56 2026 -0500

    use small epsilon instead of 0 for crossings to account for floating point noise

diff --git a/src/devicer/benchmarks/metrics.py b/src/devicer/benchmarks/metrics.py
index 230d238..9812996 100644
--- a/src/devicer/benchmarks/metrics.py
+++ b/src/devicer/benchmarks/metrics.py
@@ -3,6 +3,8 @@ from __future__ import annotations
 from dataclasses import dataclass
 from typing import List, Sequence, TypedDict
 
+EER_DELTA_EPS = 1e-12
+
 
 class ScoredPair(TypedDict):
     score: float
@@ -107,7 +109,7 @@ def calculate_true_eer(results: Sequence[BenchmarkResult]) -> EqualErrorRateResu
     previous = ordered[0]
     previous_delta = previous.far - previous.frr
 
-    if previous_delta == 0:
+    if abs(previous_delta) < EER_DELTA_EPS:
         return EqualErrorRateResult(
             threshold=float(previous.threshold),
             eer=previous.far,
@@ -119,7 +121,7 @@ def calculate_true_eer(results: Sequence[BenchmarkResult]) -> EqualErrorRateResu
     for current in ordered[1:]:
         current_delta = current.far - current.frr
 
-        if current_delta == 0:
+        if abs(current_delta) < EER_DELTA_EPS:
             return EqualErrorRateResult(
                 threshold=float(current.threshold),
                 eer=current.far,
```


---

### Navigation
[← Previous (Commit 23)](15c8f64_eer_was_not_.md) | [Back to Index](./index.md) | [Next (Commit 25) →](8572151_also_fixed_e.md)

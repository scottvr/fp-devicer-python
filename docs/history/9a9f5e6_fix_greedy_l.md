# Commit: fix greedy loading of benchmark modules, since they have main()'s in them and are intended to be used as CLI. (added lazy loading via getattr in case those exports are really needed so it didn't break something I wasn't testing, but I'd just yank that out. I won't be adding the additional benchmarks to the __init__.py at all.
**Hash:** `9a9f5e6b1d05584740f799f491664ed7c550add3`  
**Date:** 2026-03-19  

## Editorial Rationale

> I think this one is actually self explanatory from the commit message and diff

---

## Technical Diffs
```diff
commit 9a9f5e6b1d05584740f799f491664ed7c550add3
Author: ScottVR <scottvr@gmail.com>
Date:   Thu Mar 19 07:19:07 2026 -0500

    fix greedy loading of benchmark modules, since they have main()'s in them and are intended to be used as CLI. (added lazy loading via getattr in case those exports are really needed so it didn't break something I wasn't testing, but I'd just yank that out. I won't be adding the additional benchmarks to the __init__.py at all.

diff --git a/src/devicer/benchmarks/__init__.py b/src/devicer/benchmarks/__init__.py
index 9eead67..62f6472 100644
--- a/src/devicer/benchmarks/__init__.py
+++ b/src/devicer/benchmarks/__init__.py
@@ -1,3 +1,7 @@
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Any
+
 from .data_generator import (
 	create_attractor_fingerprint,
 	create_base_fingerprint,
@@ -8,8 +12,10 @@ from .data_generator import (
 	mutate,
 )
 from .metrics import BenchmarkResult, calculate_metrics
-from .accuracy_bench import run_accuracy_benchmark
-from .performance_bench import run_performance_benchmark
+
+if TYPE_CHECKING:
+	from .accuracy_bench import run_accuracy_benchmark
+	from .performance_bench import run_performance_benchmark
 
 __all__ = [
 	"BenchmarkResult",
@@ -24,3 +30,15 @@ __all__ = [
 	"run_accuracy_benchmark",
 	"run_performance_benchmark",
 ]
+
+
+def __getattr__(name: str) -> Any:
+	if name == "run_accuracy_benchmark":
+		from .accuracy_bench import run_accuracy_benchmark
+
+		return run_accuracy_benchmark
+	if name == "run_performance_benchmark":
+		from .performance_bench import run_performance_benchmark
+
+		return run_performance_benchmark
+	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```


---

### Navigation
[Back to Index](./index.md) | [Next (Commit 19) →](619d4ef_add_the_big_.md)

# Evidence

## 1. Brought library back into parity with devicer.js - Included newest features (new)

**Commits:** [03e1406](https://github.com/scottvr/fp-devicer-python/commit/03e1406)
**Files:** [README.md](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/README.md), [pyproject.toml](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/pyproject.toml), [src/devicer/__init__.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/__init__.py), [src/devicer/benchmarks/__init__.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/__init__.py), [src/devicer/benchmarks/accuracy.bench.out](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/accuracy.bench.out), [src/devicer/benchmarks/accuracy_bench.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/accuracy_bench.py), [src/devicer/benchmarks/data_generator.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/data_generator.py), [src/devicer/benchmarks/metrics.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/metrics.py), [src/devicer/benchmarks/performance.bench.out](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/performance.bench.out), [src/devicer/benchmarks/performance_bench.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/benchmarks/performance_bench.py), [src/devicer/confidence.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/confidence.py), [src/devicer/core/__init__.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/core/__init__.py), [src/devicer/core/adapter_factory.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/core/adapter_factory.py), [src/devicer/core/manager.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/core/manager.py), [src/devicer/hashing.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/hashing.py), [src/devicer/libs/__init__.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/libs/__init__.py), [src/devicer/libs/adapters/__init__.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/libs/adapters/__init__.py), [src/devicer/libs/adapters/inmemory.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/libs/adapters/inmemory.py), [src/devicer/libs/adapters/postgres.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/libs/adapters/postgres.py), [src/devicer/libs/adapters/redis.py](https://github.com/scottvr/fp-devicer-python/blob/03e1406d1fc34f7efea0105a2c7cea65552e793a/src/devicer/libs/adapters/redis.py)

## 2. add the big pairing samples and table for apples-to-apples comparison of the existing confidence metric and the proposed additional scoring metrics (new)

**Commits:** [deac2db](https://github.com/scottvr/fp-devicer-python/commit/deac2db), [3d41024](https://github.com/scottvr/fp-devicer-python/commit/3d41024), [619d4ef](https://github.com/scottvr/fp-devicer-python/commit/619d4ef)
**Files:** [src/devicer/benchmarks/demo_scoring_breakdown.py](https://github.com/scottvr/fp-devicer-python/blob/deac2db6b612dffb1b625ab42d53d3c844a7e57e/src/devicer/benchmarks/demo_scoring_breakdown.py), [src/devicer/benchmarks/scoring_breakdown.py](https://github.com/scottvr/fp-devicer-python/blob/deac2db6b612dffb1b625ab42d53d3c844a7e57e/src/devicer/benchmarks/scoring_breakdown.py)

## 3. formatting output md test (new)

**Commits:** [8975ae9](https://github.com/scottvr/fp-devicer-python/commit/8975ae9), [7855254](https://github.com/scottvr/fp-devicer-python/commit/7855254)
**Files:** [src/devicer/benchmarks/accuracy_bench.py](https://github.com/scottvr/fp-devicer-python/blob/8975ae92c1e55faff6c1299d01843d242c14c5d0/src/devicer/benchmarks/accuracy_bench.py), [src/devicer/benchmarks/demo_scenario_generator.py](https://github.com/scottvr/fp-devicer-python/blob/8975ae92c1e55faff6c1299d01843d242c14c5d0/src/devicer/benchmarks/demo_scenario_generator.py), [src/devicer/benchmarks/scenario_generator.py](https://github.com/scottvr/fp-devicer-python/blob/8975ae92c1e55faff6c1299d01843d242c14c5d0/src/devicer/benchmarks/scenario_generator.py)

## 4. add insufficiency_risj to breakdown model, narrow commonness semantics, explicit sparsity/insiffiency from low richness + missing families, trust adjustment combined both paths with profile-specific penalty strengths (new)

**Commits:** [534d32a](https://github.com/scottvr/fp-devicer-python/commit/534d32a), [737a534](https://github.com/scottvr/fp-devicer-python/commit/737a534), [8572151](https://github.com/scottvr/fp-devicer-python/commit/8572151)
**Files:** [src/devicer/benchmarks/demo_scenario_generator.py](https://github.com/scottvr/fp-devicer-python/blob/534d32a8300961c8ab76c7d0220ca703ebcacc06/src/devicer/benchmarks/demo_scenario_generator.py), [src/devicer/benchmarks/scoring_breakdown.py](https://github.com/scottvr/fp-devicer-python/blob/534d32a8300961c8ab76c7d0220ca703ebcacc06/src/devicer/benchmarks/scoring_breakdown.py), [src/devicer/benchmarks/accuracy_bench.py](https://github.com/scottvr/fp-devicer-python/blob/534d32a8300961c8ab76c7d0220ca703ebcacc06/src/devicer/benchmarks/accuracy_bench.py)

## 5. Updated code in pyproject.toml. (changed)

**Commits:** [bdd4a13](https://github.com/scottvr/fp-devicer-python/commit/bdd4a13)
**Files:** [pyproject.toml](https://github.com/scottvr/fp-devicer-python/blob/bdd4a134aba77b0f248813831e670cf44a015c91/pyproject.toml), [src/devicer/confidence_test.py](https://github.com/scottvr/fp-devicer-python/blob/bdd4a134aba77b0f248813831e670cf44a015c91/src/devicer/confidence_test.py)

## 6. Updated code in src. (changed)

**Commits:** [f779bb0](https://github.com/scottvr/fp-devicer-python/commit/f779bb0)
**Files:** [pyproject.toml](https://github.com/scottvr/fp-devicer-python/blob/f779bb0297444635cba0112049a6bc876f47638b/pyproject.toml), [src/devicer/confidence.py](https://github.com/scottvr/fp-devicer-python/blob/f779bb0297444635cba0112049a6bc876f47638b/src/devicer/confidence.py), [src/devicer/data_test.py](https://github.com/scottvr/fp-devicer-python/blob/f779bb0297444635cba0112049a6bc876f47638b/src/devicer/data_test.py), [src/devicer/hashing_test.py](https://github.com/scottvr/fp-devicer-python/blob/f779bb0297444635cba0112049a6bc876f47638b/src/devicer/hashing_test.py)

## 7. Updated code in pyproject.toml. (changed)

**Commits:** [4493337](https://github.com/scottvr/fp-devicer-python/commit/4493337), [3356940](https://github.com/scottvr/fp-devicer-python/commit/3356940)
**Files:** [pyproject.toml](https://github.com/scottvr/fp-devicer-python/blob/4493337f0561ba7aa4cc0f625a9d7e202cd2357f/pyproject.toml), [src/devicer/confidence.py](https://github.com/scottvr/fp-devicer-python/blob/4493337f0561ba7aa4cc0f625a9d7e202cd2357f/src/devicer/confidence.py)

## 8. Updated dependency or packaging metadata in .gitignore. (improved)

**Commits:** [7236eb6](https://github.com/scottvr/fp-devicer-python/commit/7236eb6)
**Files:** [.gitignore](https://github.com/scottvr/fp-devicer-python/blob/7236eb649fe65533920e65fe3f73f9d46e010f78/.gitignore), [README.md](https://github.com/scottvr/fp-devicer-python/blob/7236eb649fe65533920e65fe3f73f9d46e010f78/README.md), [pyproject.toml](https://github.com/scottvr/fp-devicer-python/blob/7236eb649fe65533920e65fe3f73f9d46e010f78/pyproject.toml)

## 9. Added functionality in .github/workflows/workflow.yml. (fixed)

**Commits:** [8d4c3c8](https://github.com/scottvr/fp-devicer-python/commit/8d4c3c8)
**Files:** [.github/workflows/workflow.yml](https://github.com/scottvr/fp-devicer-python/blob/8d4c3c835a88a7688ec2e4b64f0e3d4396b1382f/.github/workflows/workflow.yml), [dev-requirements.txt](https://github.com/scottvr/fp-devicer-python/blob/8d4c3c835a88a7688ec2e4b64f0e3d4396b1382f/dev-requirements.txt), [requirements.txt](https://github.com/scottvr/fp-devicer-python/blob/8d4c3c835a88a7688ec2e4b64f0e3d4396b1382f/requirements.txt), [src/devicer/libs/confidence.py](https://github.com/scottvr/fp-devicer-python/blob/8d4c3c835a88a7688ec2e4b64f0e3d4396b1382f/src/devicer/libs/confidence.py)

## 10. Updated code in src. (fixed)

**Commits:** [3a08008](https://github.com/scottvr/fp-devicer-python/commit/3a08008), [e3acfd9](https://github.com/scottvr/fp-devicer-python/commit/e3acfd9)
**Files:** [src/devicer/benchmarks/accuracy.bench.out](https://github.com/scottvr/fp-devicer-python/blob/3a08008bb2b3cbdbfa3eb0ef21af6511c97ca30c/src/devicer/benchmarks/accuracy.bench.out), [src/devicer/benchmarks/performance.bench.out](https://github.com/scottvr/fp-devicer-python/blob/3a08008bb2b3cbdbfa3eb0ef21af6511c97ca30c/src/devicer/benchmarks/performance.bench.out), [tests/fixtures/fingerprints.py](https://github.com/scottvr/fp-devicer-python/blob/3a08008bb2b3cbdbfa3eb0ef21af6511c97ca30c/tests/fixtures/fingerprints.py), [src/devicer/libs/hashing.py](https://github.com/scottvr/fp-devicer-python/blob/3a08008bb2b3cbdbfa3eb0ef21af6511c97ca30c/src/devicer/libs/hashing.py)

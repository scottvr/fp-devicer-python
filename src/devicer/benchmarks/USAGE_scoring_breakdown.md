```python
from scoring_breakdown import decompose_confidence, format_breakdown

# Compare two fingerprints
breakdown = decompose_confidence(fp1, fp2, top_n=5)
print(format_breakdown(breakdown))
```


```
=== Score Breakdown ===
Overall Confidence: 87.3/100

Dimensions:
  Device Similarity:     91.5/100
  Evidence Richness:     88.2/100
  Field Agreement:       85.7% (42 fields)
  Structural Stability:  94.3/100
  Entropy Contribution:  89.0/100
  Attractor Risk:        35.0/100

Top Contributing Matches:
  canvas: 100% (weight: 0.250, contribution: 25.00)
  webgl: 100% (weight: 0.200, contribution: 20.00)
  screen.width: 100% (weight: 0.080, contribution: 8.00)
  screen.height: 100% (weight: 0.080, contribution: 8.00)
  audio: 98% (weight: 0.100, contribution: 9.80)

Top Disagreements:
  userAgent: 72% (weight: 0.030, penalty: 0.84)
    A: Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36
    B: Mozilla/5.0 ... Chrome/125.0.0.0 Safari/537.36
  fonts: 87% (weight: 0.060, penalty: 0.78)
    A: [14 items]
    B: [16 items]

Missing Fields (0):
```

### Integration with Existing Benchmarks

```python
from accuracy_bench import run_accuracy_benchmark
from scoring_breakdown import decompose_confidence
from data_generator import generate_dataset

# Generate dataset
dataset = generate_dataset(size=100, sessions_per_device=3)

# For each pair, get detailed breakdown
for i in range(0, len(dataset) - 1, 2):
    fp1 = dataset[i].data
    fp2 = dataset[i + 1].data
    
    breakdown = decompose_confidence(fp1, fp2)
    
    # Use dimensions for decision logic
    if breakdown.evidence_richness < 50:
        print("Low evidence - require additional signals")
    
    if breakdown.attractor_risk > 70:
        print("High attractor risk - apply stricter threshold")
    
    if breakdown.entropy_contribution > 85 and breakdown.device_similarity > 85:
        print("High-confidence match")
```

### Attractor Detection

```python
from scoring_breakdown import calculate_attractor_risk

# Check individual fingerprint for attractor characteristics
risk = calculate_attractor_risk(fingerprint)

if risk > 70:
    print(f"High attractor risk ({risk:.1f}%) - generic fingerprint")
    print("Recommendation: Increase threshold or require IP continuity")
```

### Evidence Richness Check

```python
from scoring_breakdown import calculate_evidence_richness

richness = calculate_evidence_richness(fingerprint)

if richness < 50:
    print(f"Sparse fingerprint ({richness:.1f}% richness)")
    print("Recommendation: Fall back to IP/history signals")
```

## Decision Logic Examples

### Conservative Threshold Selection

```python
breakdown = decompose_confidence(fp1, fp2)

# Adjust threshold based on dimensions
if breakdown.attractor_risk > 70:
    threshold = 90  # Stricter for attractors
elif breakdown.evidence_richness < 60:
    threshold = 85  # Stricter for sparse data
else:
    threshold = 75  # Normal threshold

is_match = breakdown.overall_confidence >= threshold
```

### Risk Flagging

```python
risk_flags = []

if breakdown.attractor_risk > 70:
    risk_flags.append("HIGH_ATTRACTOR_RISK")

if breakdown.evidence_richness < 50:
    risk_flags.append("LOW_EVIDENCE")

if breakdown.entropy_contribution < 50 and breakdown.overall_confidence > 75:
    risk_flags.append("WEAK_ENTROPY_BUT_HIGH_SCORE")

if breakdown.structural_stability < 60:
    risk_flags.append("HARDWARE_CHANGE_DETECTED")

if risk_flags:
    print(f"Risk flags: {', '.join(risk_flags)}")
    print("Recommendation: Manual review or additional verification")
```

### Explainable Decisions

```python
breakdown = decompose_confidence(fp1, fp2)

if breakdown.overall_confidence >= 75:
    print("MATCH")
    print(f"Reason: {breakdown.entropy_contribution:.0f}% entropy agreement")
    print(f"Top signal: {breakdown.top_matches[0].field_name}")
else:
    print("NO MATCH")
    if breakdown.top_disagreements:
        print(f"Main issue: {breakdown.top_disagreements[0].field_name}")
    if breakdown.evidence_richness < 60:
        print(f"Issue: Low evidence ({breakdown.evidence_richness:.0f}%)")
```

## Field Comparison Logic

### Exact Match (100%)
- Values are identical
- Both `None`/missing

### List Comparison (Jaccard Similarity)
- Used for: `fonts`, `plugins`, `mimeTypes`
- Formula: `intersection / union * 100`
- Example: `[A, B, C]` vs `[B, C, D]` → 66.7%

### Numeric Comparison
- Percentage difference from average
- Example: `1920` vs `1366` → `100 - (|1920-1366| / avg * 100)` → ~67%

### String Comparison
- Character-level Jaccard similarity
- Example: "Chrome/120" vs "Chrome/125" → ~72%

### Dict Comparison
- Compares common keys
- Formula: `matching_values / common_keys * 100`



## Testing

Run the demo:

```bash
python demo_scoring_breakdown.py
```


- **Are the weights correct for your use case?** (Adjust `FIELD_WEIGHTS` if needed)
- **Should structural fields be weighted higher?** (Currently 20% of overall)
- **Is attractor risk detection too aggressive?** (Tune `ATTRACTOR_PATTERNS`)
- **Need more/fewer top matches?** (Change `top_n` parameter)

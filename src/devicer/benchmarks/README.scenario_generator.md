
The `scenario_generator.py` module generates test cases that mirror real-world failure modes. Instead of random synthetic mutations, these scenarios represent actual adversarial cases, privacy hardening, commodity collisions, and environmental changes that break fingerprinting in production.


Synthetic mutations (low/medium/high drift) don't capture:
- Browser updates with canvas rendering changes
- Privacy extensions that inject noise or strip fields
- Corporate fleets where 1000 users have identical laptops
- Tor users where everyone looks the same
- Cross-browser scenarios where same device switches browsers
- VPN/travel scenarios with timezone/network changes

---


## Usage


```python
from scenario_generator import generate_scenario_pair

# Generate a specific scenario
pair = generate_scenario_pair("BrowserDrift/CrossBrowser")

print(f"Expected Match: {pair.metadata.expected_match}")
print(f"Difficulty: {pair.metadata.difficulty}")
print(f"Description: {pair.metadata.description}")

# Access the fingerprints
fp1 = pair.fp1
fp2 = pair.fp2
```

### Score the Scenario

```python
from scenario_generator import generate_scenario_pair
from scoring_breakdown import decompose_confidence

pair = generate_scenario_pair("PrivacyHardening/TorBrowser")
breakdown = decompose_confidence(pair.fp1, pair.fp2)

print(f"Overall Confidence: {breakdown.overall_confidence:.1f}/100")
print(f"Attractor Risk: {breakdown.attractor_risk:.1f}/100")
print(f"Evidence Richness: {breakdown.evidence_richness:.1f}/100")

# Decision logic
threshold = 75
is_match_predicted = breakdown.overall_confidence >= threshold
is_match_actual = pair.metadata.expected_match

if is_match_predicted != is_match_actual:
    print("FAILURE CASE")
    if is_match_predicted and not is_match_actual:
        print(" False Positive: Different users detected as same")
    else:
        print(" False Negative: Same device not recognized")
```

### Generate Balanced Dataset

```python
from scenario_generator import generate_scenario_dataset

# Equal distribution across all 17 scenarios
dataset = generate_scenario_dataset(size=100)

# Count by difficulty
difficulty_counts = {}
for pair in dataset:
    diff = pair.metadata.difficulty
    difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

print(difficulty_counts)
# {'easy': 20, 'medium': 30, 'hard': 30, 'extreme': 20}
```

### Custom Distribution (Focus on Hard Cases)

```python
from scenario_generator import generate_scenario_dataset

# Focus heavily on extreme collision/privacy cases
custom_distribution = {
    # Minimal easy cases
    "BrowserDrift/Minor": 0.05,
    
    # Focus on failures
    "PrivacyHardening/TorBrowser": 0.20,
    "CommodityCollision/CorporateFleet": 0.20,
    "CommodityCollision/iPhoneDefaults": 0.15,
    "AdversarialPerturbation/CanvasNoise": 0.15,
    "BrowserDrift/CrossBrowser": 0.15,
    "PrivacyHardening/CanvasDefender": 0.10,
}

dataset = generate_scenario_dataset(size=200, scenario_distribution=custom_distribution)
```

### List Available Scenarios

```python
from scenario_generator import get_scenario_types, get_scenario_categories

# All 17 scenarios
all_scenarios = get_scenario_types()
print(all_scenarios)

# Grouped by category
categories = get_scenario_categories()
for category, scenarios in categories.items():
    print(f"{category}:")
    for s in scenarios:
        print(f"  - {s}")
```

---

## BrowserDrift/CrossBrowser (Hard)

- Same hardware (screen, memory, CPU)
- Canvas/WebGL completely different (different rendering engines)
- UserAgent, vendor, plugins all different
- Fonts may differ slightly

- Real users switch browsers
- High-entropy fields disagree but it's the same device
- Need to weight structural fields higher in this case

```python
pair = generate_scenario_pair("BrowserDrift/CrossBrowser")

# fp1: Chrome on Windows
# Canvas: hash_chrome_rendering
# WebGL: ANGLE (NVIDIA Direct3D)
# UserAgent: ...Chrome/124...

# fp2: Firefox on same Windows machine
# Canvas: hash_firefox_rendering (completely different!)
# WebGL: Mesa/X.org renderer (different!)
# UserAgent: ...Firefox/122...

# But:
# Screen: 1920×1080 (same)
# HardwareConcurrency: 8 (same)
# DeviceMemory: 16 (same)
```

---

- Two different users
- Both using Tor Browser Bundle
- Identical fingerprints (unified by design)
- Canvas/WebGL/Audio all blocked or unified

- Classic attractor collision
- Different people, same fingerprint
- False positive if you only use fingerprint
- Need IP/history to distinguish

```python
pair = generate_scenario_pair("PrivacyHardening/TorBrowser")

# fp1: User A in NYC
# fp2: User B in London

# But both have:
# Platform: Win32
# Screen: 1920×1080 (spoofed)
# HardwareConcurrency: 8 (spoofed)
# Fonts: [Arial, Times New Roman, Courier New] (minimal)
# Canvas: tor_unified_hash (same!)
# Timezone: UTC (same!)

# Expected Match: FALSE (different users!)
# But confidence will be HIGH (false positive risk)
```

---

- Two different employees
- Same laptop model, same OS image
- Only difference: actual hardware rendering (canvas/webgl/audio)
- Everything else identical (software config)

- Enterprise deployments are uniform
- Attractor collision at scale
- Canvas is the ONLY differentiator
- If canvas is blocked/spoofed, indistinguishable

```python
pair = generate_scenario_pair("CommodityCollision/CorporateFleet")

# Employee A and Employee B

# Identical:
# Platform: Win32
# Screen: 1920×1080
# Memory: 16GB
# CPU: 8 cores
# Fonts: [Arial, Calibri, Consolas, ...] (corporate image)
# UserAgent: Chrome 124

# Only difference:
# Canvas: device_001_rendering_hash
# Canvas: device_002_rendering_hash
# (but these are subtle - same GPU model, same drivers)

# Expected Match: FALSE
# But if attractor risk is high and canvas similarity is moderate,
# you might get a false positive
```

----

- Same device, same session
- Adversary injects random noise into canvas/webgl/audio
- Trying to evade tracking
- Hardware signals remain stable

- Tests whether structural stability can overcome entropy destruction
- Real adversarial tool behavior (FingerprintJS spoofing)
- Need to detect via hardware consistency even when canvas is randomized

```python
pair = generate_scenario_pair("AdversarialPerturbation/CanvasNoise")

# fp1: Original fingerprint
# Canvas: legitimate_device_hash
# Screen: 2560×1440
# HardwareConcurrency: 12

# fp2: After adversarial noise injection
# Canvas: random_12345678 (completely different!)
# WebGL: random_87654321 (completely different!)
# Audio: random_abcdef (completely different!)
# Screen: 2560×1440 (same - hardware is same)
# HardwareConcurrency: 12 (same - hardware is same)

# Expected Match: TRUE
# But entropy_contribution will be near 0
# Need to rely on structural_stability
```

---

### Use in accuracy_bench.py

```python
from scenario_generator import generate_scenario_dataset
from metrics import calculate_metrics
from scoring_breakdown import decompose_confidence

# Generate scenario dataset instead of synthetic
scenario_data = generate_scenario_dataset(size=500)

# Convert to scored pairs
scored_pairs = []
for pair in scenario_data:
    breakdown = decompose_confidence(pair.fp1, pair.fp2)
    scored_pairs.append({
        "score": breakdown.overall_confidence,
        "sameDevice": pair.metadata.expected_match,
        "isAttractor": breakdown.attractor_risk > 70,
    })

# Calculate metrics
results = calculate_metrics(scored_pairs)
best = max(results, key=lambda x: x.f1)

print(f"Best F1: {best.f1:.3f} at threshold {best.threshold}")
```

---


Run the demo:

```bash
python demo_scenario_generator.py
```

This will show:
1. Individual scenario types with scores
2. All scenario categories
3. Detailed cross-browser analysis
4. Attractor collision (corporate fleet)
5. Privacy hardening scenarios
6. Balanced dataset generation
7. Custom distribution (focus on hard cases)

---


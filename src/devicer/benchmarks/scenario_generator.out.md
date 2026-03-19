# Individual Scenario Types

### BrowserDrift/Minor
```
Expected Match: True
Difficulty: easy
Description: Same device, minor browser patch update
```
- Overall Confidence: 85.8/100
- Raw Similarity: 92.7/100
- Collision Risk: 20.0/100
- Insufficiency Risk: 0.0/100
- Trust Shift: -6.9
- Trust Adjustment: 6.9
- Confidence Label: ordinary
- Policy Action: normal
- Uncertainty Zone: False
- Distinctiveness: 77.3/100
- Commonness: 22.7/100
- Same Instance: 82.8/100
- Same Environment: 85.3/100
- Same Device: 85.8/100
- Same Entity: 86.0/100
- Raw Same Device: 92.7/100
- Entropy Contribution: 63.6/100
- Attractor Risk: 0.0/100

### BrowserDrift/CrossBrowser
```
Expected Match: True
Difficulty: hard
Description: Same device, different browser (Chrome ↔ Firefox/Safari)
```
- Overall Confidence: 81.5/100
- Raw Similarity: 88.1/100
- Collision Risk: 20.0/100
- Insufficiency Risk: 0.0/100
- Trust Shift: -6.6
- Trust Adjustment: 6.6
- Confidence Label: ordinary
- Policy Action: normal
- Uncertainty Zone: False
- Distinctiveness: 56.9/100
- Commonness: 43.1/100
- Same Instance: 75.4/100
- Same Environment: 79.9/100
- Same Device: 81.5/100
- Same Entity: 83.2/100
- Raw Same Device: 88.1/100
- Entropy Contribution: 44.0/100
- Attractor Risk: 35.0/100

### PrivacyHardening/TorBrowser
```
Expected Match: False
Difficulty: extreme
Description: Two different Tor Browser users (unified fingerprints)
```
- Overall Confidence: 55.0/100
- Raw Similarity: 98.2/100
- Collision Risk: 100.0/100
- Insufficiency Risk: 0.0/100
- Trust Shift: -43.2
- Trust Adjustment: 43.2
- Confidence Label: ordinary
- Policy Action: normal
- Uncertainty Zone: False
- Distinctiveness: 16.5/100
- Commonness: 83.5/100
- Same Instance: 68.8/100
- Same Environment: 62.9/100
- Same Device: 55.0/100
- Same Entity: 41.2/100
- Raw Same Device: 98.2/100
- Entropy Contribution: 100.0/100
- Attractor Risk: 55.0/100

### AdversarialPerturbation/CanvasNoise
```
Expected Match: True
Difficulty: extreme
Description: Same device, adversarial noise injection on canvas/WebGL
```
- Overall Confidence: 75.7/100
- Raw Similarity: 81.8/100
- Collision Risk: 20.0/100
- Insufficiency Risk: 0.0/100
- Trust Shift: -6.1
- Trust Adjustment: 6.1
- Confidence Label: ordinary
- Policy Action: normal
- Uncertainty Zone: False
- Distinctiveness: 70.7/100
- Commonness: 29.3/100
- Same Instance: 64.7/100
- Same Environment: 72.5/100
- Same Device: 75.7/100
- Same Entity: 79.9/100
- Raw Same Device: 81.8/100
- Entropy Contribution: 9.1/100
- Attractor Risk: 25.0/100

### CommodityCollision/CorporateFleet
```
Expected Match: False
Difficulty: extreme
Description: Different users, identical corporate laptops
```
- Overall Confidence: 47.3/100
- Raw Similarity: 83.7/100
- Collision Risk: 98.9/100
- Insufficiency Risk: 0.0/100
- Trust Shift: -36.4
- Trust Adjustment: 36.4
- Confidence Label: ordinary
- Policy Action: normal
- Uncertainty Zone: False
- Distinctiveness: 30.4/100
- Commonness: 69.6/100
- Same Instance: 51.4/100
- Same Environment: 51.7/100
- Same Device: 47.3/100
- Same Entity: 38.0/100
- Raw Same Device: 83.7/100
- Entropy Contribution: 27.8/100
- Attractor Risk: 70.0/100
#  Scenario Categories

### BrowserDrift:
  - BrowserDrift/Minor
  - BrowserDrift/Major
  - BrowserDrift/CrossBrowser

### EnvironmentChange:
  - EnvironmentChange/HomeOffice
  - EnvironmentChange/DockExternal
  - EnvironmentChange/MobileDesktop

### PrivacyHardening:
  - PrivacyHardening/TorBrowser
  - PrivacyHardening/ResistFingerprinting
  - PrivacyHardening/CanvasDefender

### AdversarialPerturbation:
  - AdversarialPerturbation/CanvasNoise
  - AdversarialPerturbation/FontRandomization
  - AdversarialPerturbation/UARotation

### MobilityChurn:
  - MobilityChurn/TimezoneTravel
  - MobilityChurn/VPNActivation

### CommodityCollision:
  - CommodityCollision/CorporateFleet
  - CommodityCollision/iPhoneDefaults
  - CommodityCollision/PublicTerminal
# Detailed Scenario Analysis

### Cross-Browser Scenario (Hard Case)
```

Ground Truth: True
Difficulty: hard
Description: Same device, different browser (Chrome ↔ Firefox/Safari)

```
```
=== Score Breakdown ===
Overall Confidence: 80.1/100

Identity Layer:
  Raw Similarity:        86.6/100
  Commonness Score:      41.4/100
  Distinctiveness Score: 58.6/100
  Collision Risk:        20.0/100
  Insufficiency Risk:    0.0/100
  Trust-Adjusted:        80.1/100
  Trust Shift:           -6.5
  Trust Adjustment:      6.5
  Confidence Label:      ordinary
  Policy Action:         normal
  Uncertainty Zone:      False
  Decision Threshold:    65.0
  Threshold Distance:    15.1

Dimensions:
  Device Similarity:     80.1/100
  Evidence Richness:     100.0/100
  Field Agreement:       87.1% (31 fields)
  Structural Stability:  100.0/100
  Entropy Contribution:  35.5/100
  Attractor Risk:        35.0/100
  Missing (one-side):    0
  Missing (both-side):   0

Profile Scores:
  Same Instance     raw= 76.8 adjusted= 72.8
  Same Environment  raw= 83.2 adjusted= 78.1
  Same Device       raw= 86.6 adjusted= 80.1
  Same Entity       raw= 91.4 adjusted= 82.4

Trust Policy Flags:
  - generic_software_locale

Family Scores (similarity / coverage / effective):
  rendering   35.5 / 100.0% /  35.5
  structural 100.0 / 100.0% / 100.0
  software    97.4 / 100.0% /  97.4
  locale     100.0 / 100.0% / 100.0
  misc        90.0 / 100.0% /  90.0

Top Contributing Matches:
 screen.height: 100% (weight: 0.100, contribution: 10.00)
 screen.width: 100% (weight: 0.100, contribution: 10.00)
 audio: 100% (weight: 0.062, contribution: 6.25)
 fonts: 100% (weight: 0.060, contribution: 6.00)
 hardwareConcurrency: 100% (weight: 0.060, contribution: 6.00)

Top Disagreements:
canvas: 0% (weight: 0.100, penalty: 10.00)
      A: 4fun5g
      B: wp6qv
webgl: 30% (weight: 0.087, penalty: 6.12)
      A: 1s5ntpo
      B: 1fg1ox5
vendor: 0% (weight: 0.005, penalty: 0.50)
      A: Google Inc.
      B: 

```
# Attractor Collision (Extreme Case)

###  Corporate Fleet Collision
```

Ground Truth: False (different users!)
 Difficulty: extreme
 Description: Different users, identical corporate laptops

=== Score Breakdown ===
Overall Confidence: 49.3/100

Identity Layer:
  Raw Similarity:        82.3/100
  Commonness Score:      68.1/100
  Distinctiveness Score: 31.9/100
  Collision Risk:        91.9/100
  Insufficiency Risk:    0.0/100
  Trust-Adjusted:        49.3/100
  Trust Shift:           -33.0
  Trust Adjustment:      33.0
  Confidence Label:      ordinary
  Policy Action:         normal
  Uncertainty Zone:      False
  Decision Threshold:    65.0
  Threshold Distance:    15.7

Dimensions:
  Device Similarity:     75.1/100
  Evidence Richness:     96.0/100
  Field Agreement:       89.3% (28 fields)
  Structural Stability:  100.0/100
  Entropy Contribution:  20.4/100
  Attractor Risk:        70.0/100
  Missing (one-side):    0
  Missing (both-side):   1

Profile Scores:
  Same Instance     raw= 70.5 adjusted= 51.2
  Same Environment  raw= 78.5 adjusted= 52.7
  Same Device       raw= 82.3 adjusted= 49.3
  Same Entity       raw= 88.1 adjusted= 41.6

Trust Policy Flags:
  - high_commonness_profile
  - rich_but_common
  - generic_software_locale

Family Scores (similarity / coverage / effective):
  rendering   20.4 / 100.0% /  20.4
  structural 100.0 / 100.0% / 100.0
  software   100.0 /  83.3% /  95.0
  locale     100.0 / 100.0% / 100.0
  misc       100.0 / 100.0% / 100.0

Top Contributing Matches:
 screen.height: 100% (weight: 0.100, contribution: 10.00)
 screen.width: 100% (weight: 0.100, contribution: 10.00)
 fonts: 100% (weight: 0.060, contribution: 6.00)
 hardwareConcurrency: 100% (weight: 0.060, contribution: 6.00)
 deviceMemory: 100% (weight: 0.050, contribution: 5.00)

Top Disagreements:
canvas: 22% (weight: 0.100, penalty: 7.78)
      A: gab1l2
      B: gauzzt
webgl: 20% (weight: 0.087, penalty: 7.00)
      A: 7j2ucy
      B: 7jmlgw
audio: 18% (weight: 0.062, penalty: 5.11)
      A: 1ruua5w
      B: 1rve3m7

```

**False Positive Risk:**
- Attractor Risk: 70.0/100
- Evidence Richness: 96.0/100
- Structural Stability: 100.0/100
**High confidence, but they're different users!**
# Privacy Hardening Scenarios

### PrivacyHardening/TorBrowser ---
```
Expected Match: False
Description: Two different Tor Browser users (unified fingerprints)

Scores:
  Overall Confidence: 55.0/100
  Evidence Richness: 96.0/100
  Entropy Contribution: 100.0/100
  Missing Fields: 0
```

### PrivacyHardening/ResistFingerprinting ---
```
Expected Match: True
Description: Same device, Firefox resist fingerprinting enabled

Scores:
  Overall Confidence: 49.9/100
  Evidence Richness: 75.0/100
  Entropy Contribution: 0.0/100
  Missing Fields: 3
```

### PrivacyHardening/CanvasDefender ---
```
Expected Match: True
Description: Same device, canvas defender extension active

Scores:
  Overall Confidence: 78.6/100
  Evidence Richness: 100.0/100
  Entropy Contribution: 25.0/100
  Missing Fields: 0
```
#  Balanced Dataset Generation


Generated 20 scenario pairs


### By Scenario Type:
-   AdversarialPerturbation/CanvasNoise: 2
-   AdversarialPerturbation/FontRandomization: 2
-   AdversarialPerturbation/UARotation: 2
-   BrowserDrift/CrossBrowser: 1
-   BrowserDrift/Major: 1
-   BrowserDrift/Minor: 1
-   CommodityCollision/CorporateFleet: 1
-   CommodityCollision/PublicTerminal: 1
-   CommodityCollision/iPhoneDefaults: 1
-   EnvironmentChange/DockExternal: 1
-   EnvironmentChange/HomeOffice: 1
-   EnvironmentChange/MobileDesktop: 1
-   MobilityChurn/TimezoneTravel: 1
-   MobilityChurn/VPNActivation: 1
-   PrivacyHardening/CanvasDefender: 1
-   PrivacyHardening/ResistFingerprinting: 1
-   PrivacyHardening/TorBrowser: 1

By Expected Match:
  Should Match: 16
  Should NOT Match: 4

By Difficulty:
  easy: 3
  extreme: 6
  hard: 7
  medium: 4
## Custom Distribution (Focus on Hard Cases)

  **Generated 50 pairs with custom distribution**


** Focus: Hard and extreme cases (privacy, collisions, adversarial)**

Difficulty Distribution:
  easy: 8 (16.0%)
  medium: 0 (0.0%)
  hard: 20 (40.0%)
  extreme: 22 (44.0%)
#  Scenario Benchmark (Profile-Aware)
### Generated scenario pairs: 500

### Scenario Type Means:
scenario_type                             | pairs | expected_match_pct | raw_overall_mean | overall_mean | trust_shift_mean | trust_adjustment_mean | collision_risk_mean | insufficiency_risk_mean | uncertainty_zone_pct | low_confidence_pct | distinctiveness_mean | commonness_mean | instance_mean | environment_mean | device_mean | entity_mean | richness_mean | attractor_risk_mean
------------------------------------------|-------|--------------------|------------------|--------------|------------------|-----------------------|---------------------|-------------------------|----------------------|--------------------|----------------------|-----------------|---------------|------------------|-------------|-------------|---------------|--------------------
AdversarialPerturbation/CanvasNoise       | 30    | 100.000            | 82.261           | 76.099       | -6.163           | 6.163                 | 20.000              | 0.000                   | 0.000                | 0.000              | 69.772               | 30.228          | 65.435        | 73.056           | 76.099      | 80.133      | 100.000       | 25.667             
AdversarialPerturbation/FontRandomization | 30    | 100.000            | 95.514           | 71.433       | -24.080          | 24.080                | 59.768              | 0.000                   | 0.000                | 0.000              | 49.638               | 50.362          | 78.167        | 74.922           | 71.433      | 63.958      | 100.000       | 26.250             
AdversarialPerturbation/UARotation        | 29    | 100.000            | 99.629           | 70.406       | -29.223          | 29.223                | 68.618              | 0.000                   | 0.000                | 0.000              | 38.491               | 61.509          | 79.627        | 75.646           | 70.406      | 61.123      | 100.000       | 38.276             
BrowserDrift/CrossBrowser                 | 29    | 100.000            | 84.259           | 77.152       | -7.107           | 7.107                 | 22.094              | 0.000                   | 0.000                | 0.000              | 63.918               | 36.082          | 69.461        | 74.780           | 77.152      | 79.442      | 100.000       | 28.448             
BrowserDrift/Major                        | 29    | 100.000            | 92.719           | 82.450       | -10.270          | 10.270                | 27.969              | 0.000                   | 0.000                | 0.000              | 57.702               | 42.298          | 80.791        | 82.662           | 82.450      | 81.312      | 100.000       | 26.724             
BrowserDrift/Minor                        | 30    | 100.000            | 93.049           | 77.803       | -15.246          | 15.246                | 39.878              | 0.000                   | 0.000                | 0.000              | 49.684               | 50.316          | 78.039        | 79.077           | 77.803      | 74.778      | 100.000       | 36.333             
CommodityCollision/CorporateFleet         | 29    | 0.000              | 82.722           | 48.684       | -34.038          | 34.038                | 94.021              | 0.000                   | 0.000                | 0.000              | 31.470               | 68.530          | 51.264        | 52.404           | 48.684      | 40.458      | 95.960        | 70.000             
CommodityCollision/PublicTerminal         | 29    | 100.000            | 100.000          | 77.347       | -22.653          | 22.653                | 54.228              | 0.000                   | 0.000                | 0.000              | 51.017               | 48.983          | 84.555        | 81.466           | 77.347      | 70.139      | 100.000       | 24.655             
CommodityCollision/iPhoneDefaults         | 30    | 0.000              | 87.819           | 50.325       | -37.494          | 37.494                | 97.201              | 0.000                   | 0.000                | 0.000              | 29.938               | 70.062          | 58.483        | 56.360           | 50.325      | 39.530      | 87.626        | 65.000             
EnvironmentChange/DockExternal            | 29    | 100.000            | 88.288           | 65.379       | -22.909          | 22.909                | 61.250              | 0.000                   | 0.000                | 0.000              | 45.948               | 54.052          | 75.426        | 70.864           | 65.379      | 60.297      | 100.000       | 30.172             
EnvironmentChange/HomeOffice              | 29    | 100.000            | 83.124           | 75.938       | -7.187           | 7.187                 | 22.676              | 0.000                   | 0.000                | 0.000              | 62.418               | 37.582          | 75.985        | 76.944           | 75.938      | 78.448      | 100.000       | 20.517             
EnvironmentChange/MobileDesktop           | 29    | 0.000              | 52.004           | 48.108       | -3.896           | 3.896                 | 20.000              | 0.000                   | 0.000                | 0.000              | 72.259               | 27.741          | 38.865        | 43.247           | 48.108      | 55.193      | 100.000       | 28.103             
MobilityChurn/TimezoneTravel              | 29    | 100.000            | 98.648           | 78.293       | -20.354          | 20.354                | 49.950              | 0.000                   | 0.000                | 0.000              | 52.513               | 47.487          | 84.770        | 80.874           | 78.293      | 69.127      | 100.000       | 24.310             
MobilityChurn/VPNActivation               | 29    | 100.000            | 96.482           | 78.326       | -18.157          | 18.157                | 45.226              | 0.000                   | 0.000                | 0.000              | 53.399               | 46.601          | 82.066        | 80.539           | 78.326      | 72.395      | 100.000       | 26.379             
PrivacyHardening/CanvasDefender           | 29    | 100.000            | 89.858           | 79.852       | -10.006          | 10.006                | 28.088              | 0.000                   | 0.000                | 0.000              | 61.056               | 38.944          | 75.983        | 79.357           | 79.852      | 79.848      | 100.000       | 26.034             
PrivacyHardening/ResistFingerprinting     | 31    | 100.000            | 56.434           | 54.227       | -2.207           | 2.330                 | 10.386              | 33.000                  | 0.000                | 0.000              | 64.605               | 35.395          | 47.687        | 53.694           | 54.227      | 60.543      | 75.000        | 37.984             
PrivacyHardening/TorBrowser               | 30    | 0.000              | 98.192           | 54.987       | -43.204          | 43.204                | 100.000             | 0.000                   | 0.000                | 0.000              | 16.500               | 83.500          | 68.842        | 62.941           | 54.987      | 41.182      | 95.960        | 55.000             

### Per-threshold table (overall):
threshold | precision | recall | f1    | far   | frr   | gap_far_frr
----------|-----------|--------|-------|-------|-------|------------
0         | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
5         | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
10        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
15        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
20        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
25        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
30        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
35        | 0.764     | 1.000  | 0.866 | 1.000 | 0.000 | 1.000      
40        | 0.766     | 1.000  | 0.867 | 0.992 | 0.000 | 0.992      
45        | 0.784     | 0.997  | 0.878 | 0.890 | 0.003 | 0.887      
50        | 0.870     | 0.966  | 0.916 | 0.466 | 0.034 | 0.432      
55        | 0.989     | 0.901  | 0.942 | 0.034 | 0.099 | 0.066      
60        | 0.987     | 0.791  | 0.878 | 0.034 | 0.209 | 0.176      
65        | 1.000     | 0.785  | 0.880 | 0.000 | 0.215 | 0.215      
70        | 1.000     | 0.715  | 0.834 | 0.000 | 0.285 | 0.285      
75        | 1.000     | 0.636  | 0.778 | 0.000 | 0.364 | 0.364      
80        | 1.000     | 0.453  | 0.623 | 0.000 | 0.547 | 0.547      
85        | 1.000     | 0.152  | 0.264 | 0.000 | 0.848 | 0.848      
90        | 0.000     | 0.000  | 0.000 | 0.000 | 1.000 | 1.000      
95        | 0.000     | 0.000  | 0.000 | 0.000 | 1.000 | 1.000      
100       | 0.000     | 0.000  | 0.000 | 0.000 | 1.000 | 1.000      

### Benchmark summary:
profile          | best_f1_threshold | best_f1 | eer_threshold | eer  
-----------------|-------------------|---------|---------------|------
raw_overall      | 50                | 0.876   | 88.160        | 0.346
overall          | 55                | 0.942   | 54.341        | 0.091
same_instance    | 60                | 0.913   | 66.121        | 0.197
same_environment | 60                | 0.895   | 61.873        | 0.159
same_device      | 55                | 0.942   | 54.341        | 0.091
same_entity      | 55                | 0.913   | 53.379        | 0.134

### Threshold Comparison (F1):
threshold | raw_overall_f1 | overall_f1 | instance_f1 | environment_f1 | device_f1 | entity_f1
----------|----------------|------------|-------------|----------------|-----------|----------
0         | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
5         | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
10        | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
15        | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
20        | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
25        | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
30        | 0.866          | 0.866      | 0.866       | 0.866          | 0.866     | 0.866    
35        | 0.866          | 0.866      | 0.874       | 0.867          | 0.866     | 0.866    
40        | 0.866          | 0.867      | 0.883       | 0.877          | 0.867     | 0.886    
45        | 0.869          | 0.878      | 0.880       | 0.885          | 0.878     | 0.901    
50        | 0.876          | 0.916      | 0.865       | 0.884          | 0.916     | 0.897    
55        | 0.870          | 0.942      | 0.884       | 0.894          | 0.942     | 0.913    
60        | 0.862          | 0.878      | 0.913       | 0.895          | 0.878     | 0.870    
65        | 0.851          | 0.880      | 0.873       | 0.880          | 0.880     | 0.844    
70        | 0.854          | 0.834      | 0.817       | 0.880          | 0.834     | 0.812    
75        | 0.853          | 0.778      | 0.703       | 0.714          | 0.778     | 0.766    
80        | 0.841          | 0.623      | 0.606       | 0.606          | 0.623     | 0.487    
85        | 0.775          | 0.264      | 0.339       | 0.388          | 0.264     | 0.279    
90        | 0.722          | 0.000      | 0.000       | 0.000          | 0.000     | 0.000    
95        | 0.515          | 0.000      | 0.000       | 0.000          | 0.000     | 0.000    
100       | 0.194          | 0.000      | 0.000       | 0.000          | 0.000     | 0.000    

### Threshold Comparison (FAR/FRR Gap):
threshold | raw_overall_gap | overall_gap | instance_gap | environment_gap | device_gap | entity_gap
----------|-----------------|-------------|--------------|-----------------|------------|-----------
0         | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
5         | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
10        | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
15        | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
20        | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
25        | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
30        | 1.000           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
35        | 1.000           | 1.000       | 0.932        | 0.992           | 1.000      | 1.000     
40        | 1.000           | 0.992       | 0.845        | 0.907           | 0.992      | 0.661     
45        | 0.975           | 0.887       | 0.776        | 0.828           | 0.887      | 0.139     
50        | 0.862           | 0.432       | 0.725        | 0.772           | 0.432      | 0.089     
55        | 0.788           | 0.066       | 0.425        | 0.476           | 0.066      | 0.043     
60        | 0.731           | 0.176       | 0.182        | 0.129           | 0.176      | 0.178     
65        | 0.699           | 0.215       | 0.089        | 0.215           | 0.215      | 0.239     
70        | 0.673           | 0.285       | 0.309        | 0.215           | 0.285      | 0.317     
75        | 0.670           | 0.364       | 0.458        | 0.445           | 0.364      | 0.380     
80        | 0.638           | 0.547       | 0.565        | 0.565           | 0.547      | 0.678     
85        | 0.200           | 0.848       | 0.796        | 0.759           | 0.848      | 0.838     
90        | 0.116           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
95        | 0.371           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     
100       | 0.893           | 1.000       | 1.000        | 1.000           | 1.000      | 1.000     

----

## Trust/Commonness Semantic Truth Table
case                              | expected_match | raw_device_similarity | commonness | distinctiveness | collision_risk | insufficiency_risk | trust_shift | trust_adjustment | final_profile_score | confidence_label | policy_action | uncertainty_zone | obs_commonness_band | obs_distinctiveness_band | obs_insufficiency_band | obs_trust_band | should_commonness | should_distinctiveness | should_insufficiency | should_trust_adjustment | semantic_check | semantic_mismatches        | policy_flags                                                                                                                                                                                                             
----------------------------------|----------------|-----------------------|------------|-----------------|----------------|--------------------|-------------|------------------|---------------------|------------------|---------------|------------------|---------------------|--------------------------|------------------------|----------------|-------------------|------------------------|----------------------|-------------------------|----------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Tor vs Tor (different users)      | False          | 98.192                | 83.500     | 16.500          | 100.000        | 0.000              | -43.204     | 43.204           | 54.987              | ordinary         | normal        | False            | high                | low                      | low                    | high           | high              | low                    | low                  | high                    | PASS           | -                          | high_commonness_profile,entropy_standardized,rich_but_common,generic_software_locale                                                                                                                                     
Corporate fleet (different users) | False          | 82.106                | 67.914     | 32.086          | 91.077         | 0.000              | -32.597     | 32.597           | 49.509              | ordinary         | normal        | False            | med                 | low                      | low                    | high           | high              | low                    | low                  | high                    | FAIL (3/4)     | commonness                 | high_commonness_profile,rich_but_common,generic_software_locale                                                                                                                                                          
Minor drift (same device)         | True           | 92.800                | 62.800     | 37.200          | 55.972         | 0.000              | -21.566     | 21.566           | 71.234              | ordinary         | normal        | False            | med                 | low                      | low                    | high           | low/med           | med/high               | low                  | low                     | FAIL (2/4)     | distinctiveness,trust      | rich_but_common,generic_software_locale                                                                                                                                                                                  
Cross-browser (same device)       | True           | 83.731                | 23.931     | 76.069          | 20.000         | 0.000              | -6.273      | 6.273            | 77.458              | ordinary         | normal        | False            | low                 | high                     | low                    | low            | low/med           | med/high               | low/med              | low/med                 | PASS           | -                          | -                                                                                                                                                                                                                        
Sparse fp (same device)           | True           | 66.350                | 43.250     | 56.750          | 0.000          | 80.653             | -8.101      | 8.101            | 58.249              | uncertain_zone   | review        | True             | med                 | med                      | high                   | med            | med/high          | low/med                | high                 | med/high                | PASS           | -                          | generic_software_locale,insufficient_evidence,low_comparable_fields,missing_key_families,entropy_family_absent,thin_software_family,low_confidence_by_insufficiency,near_threshold_under_insufficiency,review_recommended
Sparse fp (different device)      | False          | 32.166                | 35.038     | 64.962          | 0.000          | 77.515             | 13.684      | 13.684           | 45.850              | low_confidence   | review        | False            | low                 | med                      | high                   | med            | high              | low                    | high                 | med/high                | FAIL (2/4)     | commonness,distinctiveness | insufficient_evidence,low_comparable_fields,missing_key_families,entropy_family_absent,thin_software_family,low_confidence_by_insufficiency,review_recommended                                                           



# All scenarios Types:


  - BrowserDrift/Minor
  - BrowserDrift/Major
  - BrowserDrift/CrossBrowser
  - EnvironmentChange/HomeOffice
  - EnvironmentChange/DockExternal
  - EnvironmentChange/MobileDesktop
  - PrivacyHardening/TorBrowser
  - PrivacyHardening/ResistFingerprinting
  - PrivacyHardening/CanvasDefender
  - AdversarialPerturbation/CanvasNoise
  - AdversarialPerturbation/FontRandomization
  - AdversarialPerturbation/UARotation
  - MobilityChurn/TimezoneTravel
  - MobilityChurn/VPNActivation
  - CommodityCollision/CorporateFleet
  - CommodityCollision/iPhoneDefaults
  - CommodityCollision/PublicTerminal

----


# Project Evolution & Rationale

## Commit Index

* **2026-03-19 07:19:07**: [fix greedy loading of benchmark modules, since they have main()'s in them and are intended to be used as CLI. (added lazy loading via getattr in case those exports are really needed so it didn't break something I wasn't testing, but I'd just yank that out. I won't be adding the additional benchmarks to the __init__.py at all.](./9a9f5e6_fix_greedy_l.md)
* **2026-03-19 08:18:03**: [add the big pairing samples and table for apples-to-apples comparison of the existing confidence metric and the proposed additional scoring metrics](./619d4ef_add_the_big_.md)
* **2026-03-19 08:50:32**: [test profile/family ideas, and missingness-aware coverage](./3d41024_test_profile.md)
* **2026-03-19 09:25:33**: [make scoring_breakdown more in-line with existing benchmarks, but without adding imports for them](./deac2db_make_scoring.md)
* **2026-03-19 09:57:09**: [some realistic red-teaming scenarios to show where I think the synthetic data_generator is hiding things you'll want to test and surface](./7855254_some_realist.md)
* **2026-03-19 10:06:03**: [eer was not EER; it was abs(far, frr), so I've renamed it and added an actual eer calculation in its place.](./15c8f64_eer_was_not_.md)
* **2026-03-19 10:16:56**: [use small epsilon instead of 0 for crossings to account for floating point noise](./12b11d3_use_small_ep.md)
* **2026-03-19 10:18:13**: [also fixed eer in last commit, now adding the new eer and old far/frr columns](./8572151_also_fixed_e.md)
* **2026-03-19 10:30:11**: [commit accuracy bench out with accurate eer](./cdc9e0f_commit_accur.md)
* **2026-03-19 11:31:40**: [add insufficiency_risk to breakdown model, narrow commonness semantics, explicit sparsity/insiffiency from low richness + missing families, trust adjustment combined both paths with profile-specific penalty strengths](./534d32a_add_insuffic.md)
* **2026-03-19 11:57:04**: [add "uncertainty band"](./737a534_add_uncertai.md)
* **2026-03-19 15:13:14**: [formatting output md test](./8975ae9_formatting_o.md)

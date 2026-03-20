# Changeling Forensic Report

Range: `9a9f5e6b1d05584740f799f491664ed7c550add3..HEAD~3`
Commits: 8
Files changed: 18
Insertions: 3027
Deletions: 663

## Candidate Notes

- (new) some realistic red-teaming scenarios to show where I think the synthetic data_generator is hiding things you'll want to test and surface [supported]
- (new) add the big pairing samples and table for apples-to-apples comparison of the existing confidence metric and the proposed additional scoring metrics [supported]
- (fixed) eer was not EER; it was abs(far, frr), so I've renamed it and added an actual eer calculation in its place. [supported]
- (new) Updated code in src. [inferred]

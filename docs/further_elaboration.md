# Revised, less scatterbrained docs, specifically of the changes

OK. I looked like a drunken idiot in the drafts i was going to email you. I hadn't consciously been aware of this since working on it but seeing the date of most of the commits causes me to realize something. 

Probably one reason I jumped eagerly into playing with your benchmarks was a strong need to stay busy that day. 3/19/1990 is my son's birthday. My son passed away May 5, 2018. March to May each year since has been a rough time for me, mentally, and staying engaged in something new and challenging, staying up a night or two to do so, is a decent strategy for staying out of my head on these commerative days. It's probably why even acknowledging I am always verbose and often kidnda spiral around the core issue, arrriving via detours and tangents, the docs I put together for you that you've seen already are pretty rough,  now that I actually look at them, and the ones I was planning to send you are even more scatter-brained, and a bit embarassing; seeing the date I was doing all this work explains a lot. :-)

## annotated, editorialized git log/git show

OK So with all that said, I decided to take the time to do better. So, using a stripped down component of the `cling` tool I referred to earlier, I auto generated an index.md, and an md full of the `git show` for each commit, which I have gone through one at a time and edited with commetaary at the top explaining what and the rationale behind it. (I found some of my commit messages didn't really match whatever I comited at that point in time anyway so I hope this effort makes it more clear.)

## the initial motivation, more succinctly explained

I read your white paper, and looked at the code. As I said on the call, it seemed like "confidence" was ambiguous, and appeared to be doing a lot of heavy lifting that, if so, would provide benefit from being clearly shown as distinct.

These are not the same things:
- raw similarity scoring
- calibrated confidence
- weighting
- identification/clustering

But they all doculd be made to emerge from what you already had but were hiding behind a single scalar value.

I'm not criticizing you or the project; it's how early version of things are, but as I mentioned, I was motivated and wanted to help in a way that could prove beneficial as you figure out what you want the project to become.

Things that could emerge from this relatively small and simple architectural change:

- weights iwith a concept of "uniqueness" or "astonishment" based on historical frequency
- time-decay the confidence with soe factor for age of observations
- "missingness"-aware normalization
- explanation output per field
- learned scorer on top of comparator outputs (sounds like you may be working on something like that already with your stability term.)
- cross-schema matching mode
- cluster/device-history consistency checks instead of one-shot pair scoring

I did *not* give you those things, I simply scaffolded a way to surface the things that comprise your "legacy" scalar

## improvements I'd make that I didn't get to
You collect a bunch of user-agent data that is fairly useless and pretty redundant.  Check that the redundancy isn't causing same features by different names to be multiply-counted.
the fonts, plugins, webgl, etc type stuff can be quite noisy (or unavailable) which might fight against the stability you are aiming for.

## THings from the very fields I just mildly-criticize that I used
I tried to indicate what I think is a better use of them, by deriving "families" from them.  As you will see from the history report I generated (with commentary.) And then instead of trying to calculate similarity on pairs of the entire blobs od fields, I showed a way to measure similaroity by family. e.g., how similar are the platofmrs, how similar is the display hardware, how  much is missing or actively obfuscated? and so on.

## NExt steps

With the sets of changes you can now run the tests I was suggesting:

run tests on each field family

- same page relaod 
- same browser restart
- time difference (days)
- after updates
- ingognito
- vpn/tor
- etc


That's a lot of work.

But it would tell you what fields are stable. what are sorta stable, what are environment-sensitive, etc.  Which would be better than flat-weights, no matter how tuned.

I think thata classifying missing values is more important than it is being treated presently.  "no plugins? or just no data about plugins?"  those are distinct.


This is also a lot of *words*, and maybe I took your project too seriously; maybe it is just an experiment and you have no desire to add this additional work. LIke I said before, that's cool; won't hurt my feelings. I had reasons I didn't even realize until looking at the date in the git log for why I hyperfocused on it for a coupel of days. 

Your IP tool and other signals made me think this was wanting to be more than just "fingerprinting", and more akin to "identity resolution",  But if I was wrong, you have no obligation to take anything I said seiously. 

This is about all the time I have for today now, so let me wrap this up.


### motivation for the second branch where I merged the changes into your core library

Your TS implementation speaks of a plugin mechanism for identify(); I did not see this implemented in the python lib. Rather that try to decide what your plugin system (if any) should look like in python, I just merged a few small changes into the  relavant places in your existing modules. This is why I did it in two branches; so if you wanted to extened via a plugin, you'd have the code in the scoring branch where it is all localized in benchmarks/ and do so if you wanted.


### what are you wanting to measure
This reminds me of another thought I had at the time when looking at your existing benchmarks: you are doing pair-wsie classification, not identification. The benchmark is testing "given two devices, are they the same fingerprint?" but the DeviceManagere.identify() problem is more like "given one fingerprint and a history of stored  prior fingerprints, which devices does thiss print beloing to, or is it a new one?  At least that is a distinction I think should be called out. They are related problems and solutions, but not exactly the same. 

Your existing benchmark really is testing the validity of your scoring kernel, which I think would struggle and seems increasingly opaque as your dataset grows (and that dataset would no doubt include more scanarios, as in the scnario_generator I put in benchmarks/) This iss where I was trying to be helpful so that you don't just test an ideal syntheti world (with the negative samples I saw you do add, but it's only as realistic as whatever is in generate_dataset.py, so I hoepd the examples in the scnario_generator could be used in your generate_dataset.py in some fashion.)  The "fashion" I had in  mind was some sort of template + mutations in your generator, but I did not modify your generator.

I don't mean to beat a dead horse but "calculate_confidence" is an aggregate metric that does not tell us what fields the model cares about, i(which fields are dead weigh, , or brittle. Which dominate errors?) 

Like I said, I'm not a big stats guy, but I read a lot of papers, and initially thought an ablation study was what I'd tackkle, disabling/zeroing one feature at a time and seeing what changeed and by how much. It would probably have been a more disciplined way to start, but I was in no mood for discipline. :-)

## Attractors

I wanted to pay more attention to this, but as I've mentioned, after a quik burst of must-do-now energy, I got a bit paid contract and quickly had to shift gears.
Planned was demonstrataing the same metrics, but adding a summary for attractor pairs, and one for non-atrractor pairs.  Also, the fact that I woudln't really know what to *do* with that additional data, kept me from feeling very motivated to go down this route. You might waant to though.

# other improvements to your existing benchmarks.

Add to your aggregte reporttig:
- top false positives
- top false negatives
- collisions


The index into the git commits commentary is in [history/index.md](history/index.md)

A new document on parameter tuning the expanded confidence model that uses commonness, insufficiency, evidence richness, collision risk, structural stability, etc as part of the confidence model (I'll paste the breakdown below) can be found at [PARAMETER_TUNING.md](PARAMETER_TUNING.md)

### Confidence Score Breakdown
```python
    return ConfidenceBreakdown(
            primary_profile=primary_profile,
            overall_confidence=round(_clamp_0_100(overall), 3),
            profile_scores={name: round(_clamp_0_100(score), 3) for name, score in profile_scores.items()},
            family_scores=family_scores,
            evidence_richness=round(_clamp_0_100(evidence_richness), 3),
            field_agreement=round(_clamp_0_100(field_agreement), 3),
            structural_stability=round(_clamp_0_100(structural_stability), 3),
            entropy_contribution=round(_clamp_0_100(entropy_contribution), 3),
            attractor_risk=round(_clamp_0_100(attractor_risk), 3),
            device_similarity=round(_clamp_0_100(device_similarity), 3),
            total_fields_compared=comparable_fields,
            one_side_missing_fields=one_side_missing_fields,
            both_side_missing_fields=both_side_missing_fields,
            raw_similarity_score=round(_clamp_0_100(raw_primary), 3),
            commonness_score=round(_clamp_0_100(commonness_score), 3),
            distinctiveness_score=round(_clamp_0_100(distinctiveness_score), 3),
            collision_risk=round(_clamp_0_100(collision_risk * 100.0), 3),
            insufficiency_risk=round(_clamp_0_100(insufficiency_risk * 100.0), 3),
            trust_adjustment=round(_clamp_0_100(trust_adjustment), 3),
            trust_shift=round(trust_shift, 3),
            uncertainty_zone=uncertainty_zone,
            confidence_label=confidence_label,
            policy_action=policy_action,
            decision_threshold=round(_clamp_0_100(decision_threshold), 3),
            threshold_distance=round(max(0.0, threshold_distance), 3),
            raw_profile_scores={
                name: round(_clamp_0_100(score), 3)
                for name, score in raw_profile_scores.items()
            },
            policy_flags=policy_flags,
            family_similarities={
                name: round(_clamp_0_100(score), 3)
                for name, score in family_similarities.items()
            },
            family_coverages={
                name: round(_clamp01(score), 6)
                for name, score in family_coverages.items()
            },
            family_effective_scores={
                name: round(_clamp_0_100(score), 3)
                for name, score in family_effective_scores.items()
            },
        )
```


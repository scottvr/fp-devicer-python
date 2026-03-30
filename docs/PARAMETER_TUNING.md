# Decomposed (and recomposited) model Parameter Tuning
So... we briefly discussed that I wanted to draft a proper test plan. I haven't. But, here are my thoughts captured from when I did start working on it. 
If you have an LLM that you trust to take these thoughts and form them into something more coherent and structured, it's something I suggest maybe you do.

## GUTS
I added lots of multiplicative weights and various gates and thresholds; all of them essentially began as just a gut instinct/intuition after seeing where you had weighted fields, 
then making barely-better-than-random tweaks to knobs, noticed when results got "better" (from my subjective view against your existing benchmark data. Since there is a curve, with sweet spots,
where "confidence" rises and falls before and after, "better" depends a lot on what is important to the viewer, which was one motivator for the profiles and grouping by family.

## Shape
So *I* was satisfied that the shape of what I layed out was correct (or at least not wrong, but I would not call it necessarily "complete") 
So, if one assumes this is true, the next steps would be to call out that in its current state there are:
- hand-tuned policy engine (from gut)
- with many arbitrary constants (from ass)
- the hand-tuning does make it work better than when I started ("better" compared to itself, when I first broke the fields into groups)
- but its behavior is still anchored in intuition and local examples

## So...
- the coefficients are arbitrary
- arbitrary is not necessarily useless
- the knobs proved well-enough my hypothesis
- now they need to be turned to the right positions based on actual input and desired output

### Oh...
You mentioned a stability variable that you were using to tame your coefficients. I looked at your main branch and see that you have a stability_window_size and average the value for each field
as you iterate through multiple fingerprints. I found it as ` stabilities[field] = (total / count) if count else 1.0`
I actually carried this over and you will see it as `structural_stability` (the formula is the same, just worded slightly differently: `structural_stability = _weighted_mean(structural_pairs)` where `_weighted_mean` is exactly what you would expect the function to look like, summing each value * its weight, dividing by total_weight,   
in the reports I generated in `benchmarks/` AND... of course I assigned a weight to it too; there are family weights applied to component weights, there are what need to be tuned, (not just nultiplied by a moving average to enforce a level of stability) so we can say how important it is to the overall score. I think this is the inverse of what you were suggesting which was to use that value as a stabilizing coefficient to the weights I am using for the components that are shown in the `breakdown`. This is not the same thing as what I was suggesting ought to be a next step, and importantly, I have verified that I did carry your stabilizer variable over (and multiply *it* by an arbitraty weight that determines how much its input effects the final number.)

# What is there
Before I shared that fork with you I did implement:
- a non-linear collision ramp
- stopped punishing "missingness", moderating it instead, toward 'uncertainty'
- exact constants that should be considered placeholders
But the arbitrary constants are not exactly 'random'; each cluster of constants corresponds to a specific concept:
- when "common-ness" should start to matter (but not exactly where the threshold is, or what the slope should look like)
- when low distinctiveness should start to matter
- how strongly rich evidence should amplify collision risk
- how strongly each profile should penalize collision
- how strongly each profile should collapse toward uncertainty under insufficiency
- where each profile's uncertainty midpoint/band should live
- when collision caps should kick in
- and so on...
   
## What do do?
Decide which group should have learned values for these knobs. Which ones should be benchmark-tuned? Which ones should be a policy choice? (by "type" of client/user, by specific client/user, etc)

So that last bit is important, but also maybe it can be ignored until *after* a good set of default knob positions is determined for your opinioniated default view. You may find that your product has a different stance for different markets. Maybe not, but the concept is actionable with this implementation.

So, I said it needs to be "decided". *I* think:

### Policy choices
- `profile_uncertainty_midpoint`
- `profile_collision_cap`
- `profile_hard_collision_cap`
- uncertainty-zone boundaries / review policy
These are partly UX, partly business needs/preferences. How conservative is the end user? How much uncertainty is acceptable for their business case? WHen and how to things get routed for review?

### Calibration parameters
These are asking to be tuned in a data-driven fashion. These are the knobs that control:
- commonness ramp start/end
- distinctiveness ramp start/end
- richness activation threshold
- collision penalty strengths
- uncertainty pull strengths
- exponents
  
Bench-tuning applies here.

### Structural design choices
These are less about specific numerical choices, and more conceptual items for architecture decisions.
- collision as penalty
- insufficiency as moderation
- profile-specific scoring
- family aggregation
- caps for severe collision classes

## How?
I don't really know. I do know more than I did when I started this document. I was planning to just list some things and be done with this in about 10-15 minutes. It has been much 
longer than that so I have a better feel fow how *I* think I would go about it, but also testing and tuning of this sort is outside of my area of expertise and formal experience, so I hesitate to prosyletize too much, and suggest you take my suggesstions with a grain of salt. *I* think my ideas are great, all the time, for everything, but life has repeatedly showm be to be wrong. WIth that huge disclaimer, here are things I didn't have in the chamber when I started this document:

### Architecture freeze
Sure. It isn't perfect. It was a PoC. But.. it's been validated enough now that I say it should stay exactly as it is for the purpose of this phase of arriving at deserved constants, removing all the gut feel numbers.
So freeze it. And start validating the calibration layer. Systematically.

### What system?
This is where you ask an expert. Or an LLM you trust to play one on TV. But the basic steps (with a lot of details to fill in for execution) would be:
1. classify tunables into small groups.
   I have tried to do that for you already. Just above up there.
2. define what each group is supposed to improve.
  I have been a little hand-wavy there, but I was planning to figure it out as I spent more time on it. Time I don't have right now. This is the sort of stuff PM's love to put in Jira boards as "User Stories" and the like.
  But to try to give examples of something concrete, from the `scenario_generator` as examples:
  - "collision-risk params should reduce Tor/fleet/default false positives"  
  - "insufficiency params should improve sparse/partial-case semantics"
  - "profile params should preserve intended ordering and threshold behavior"
  - "review thresholds should route uncertain cases without wrecking auto-decision"
  - _and you add more stuff here..._
3. Create some sort of scorecard.
  For each run, track some small-ish set of conclusions from metrics. I don't know how many but I'll list as many as come to mind now:
  ```
  scenario benchmark best F1
  scenario benchmark true EER
  Tor false-match score
  corporate-fleet false-match score
  iPhone-default false-match score
  minor-drift true-match score
  cross-browser true-match score
  sparse same-device final score
  sparse different-device final score
  percent routed to review
  ...
  ```
  This gives a way to have measurable cost/benefit to analyze after each run.

4. Tune one group at a time
   This is what I was saying I was wanting to plan before I had to stop working on it. The plan I had was essentially a bunch of browser tabs (that are still open, waiting for me)
   about linear regression for parameter tuning, Grid or random searches for the same.
   It isn't something I have directly ever needed to do again. Intuition or pre-existing "not-my-department" business process logic has always worked well enough to excuse me from this responsibility. But, I figurewd it was time to figure it out.
   It is my current thinking that it isn't as difficult or far away as I had assumed. The high school stats I learned for writing the markdown tables of values of interest in the benchmarks is probably enough to get started. You may be far better equipped to take this on than I was, but I *felt* like it was pretty straightforward because these are things I've worked with for other purposes plenty of time.
   Three layers, essentially; maybe more but...
   - **1** feature similarity
   - **2** semantic transformaations
   - **3** policy outputs
  
      
   As I've already mentioned a few times now. I think this is it. At least for now.
   - **1** is reasonably solid.
   - **2** is conceptually solid, but the numbers are essentially intuitive guesses
   - **3** is always going to be at least partly hand-tuned

## So...
Next actionable step is calibrate **2**. And if **3** remains policy decision and hand-tuning, **2** is the _only_ thing that needs to be done next. This should feel promising to read. But it still will require some time and effort.

### But DON'T
Change things just because they're arbitrary. This was (and still is, kinda) my instinct, but it should be avoided as it is just spending more time testing the arbitrary or random.
And also, don't do it because I lie when I call it arbitrary and random. It is better than that. Time was spent tweaking knobs, running another pass; if things improved, keep new value, repeat.
But that's slow and not scalable. THis needs to be automated. There are probably off-the-shelf ways to do this, but I've never had a need to learn what they are.

## oddly-placed, unexpected random notes dump
- the "uncertainty zone" experiment shows something useful:
    - sparse same-device-> `uncertainty_zone`, `review`.
    - sparse different-device-> `low_confidence`, `reiew`.

This shows that downstream policy has the effect of reducing the load the final scalar value has to bear.
Which implies that not every number has to be precisely perfect, at least if the policy layer uses uncertainy, confidence label, and review routing properly.

- creat the list of outputs that will be compared. I gave a list of like 10
- create/adjust policies. These consume the core outputs from above and apply the things like collision penalty, confidence labels, actions (DENY, PERMIT, REVIEW, WHATEVER)
- prepare benchmark scripts. (generate cases, including adversarial, neative, etc.) There should call the core library code (or benchmark code, if that' the branch used) but not be responsible for the scoring logic themselves, so maybe new wrappers around what we've got now. (just to stay honest and scientific about things.)
- group the parameter knobvs in sematic bundles as suggested earlier above. This anables the user (you) to  decide things like "we should use the conservative/fraud profile", " we should use a softer review threshold", " we should optimize for ..."

## A Shape of Things to come
```
ScoringCOnfig:
    FieldDefinition
    FamilyDefinition
    ComparisonProfile
    CollisionRiskConfig
    InsufficiencyConfig
    TrustAdjustmentConfig
    DecisionPolicyConfig
```
### benchmark scripts own:
- scenario generation
- dataset generation
- threshold sweeps
- F1/FAR/FRR/EER computation
- truth-table assertions
- scorecards
Don't put these in the core library itself.

# Conclusion
I know this is a lot, but... if I was given this project as a work assignment, this is about what I would deliver I think. I'm not a Project Manager, or particulary good planner of anything. I am subject to whim and whimsy, and am easily distracted by shiny objects. Your project served as a shiny object, caused me to want to share ideas with you, some of which I implmented in code so I could feel good about suggesting them. I would have felt bad if I sent you a detailed document *first*, then you acted on it and found the hypothesis to have no merit. So.. IMHO even the incomplete design has proven its worth, but it needs real tuned paramter values to work as well as it could, and my opinion is that doing this now will set your fp-devicer up for success, should you choose to push further forward with it.

I genuinely hope this is helpful to you.

Cheers!

### References from my browser tabs
1. https://apmonitor.com/me575/index.php/Main/LinearMultivariateRegression#:~:text=Regression%20is%20the%20method%20of,outputs%20(multivariate%20linear%20regression).&text=In%20machine%20learning%20terminology%2C%20the,and%20c%20is%20the%20intercept.&text=An%20alternate%20way%20to%20write,the%20intercept%20to%20%CE%B22%20.&text=Capital%20letters%20are%20often%20used,output%20is%20the%20error%20%CE%B5%20.
2. https://medium.com/artificial-intelligence-jillani-softech/deep-dive-into-parameter-tuning-techniques-grid-search-random-search-and-bayesian-7324e43157d7
3. ALthough it is increasingly difficult to seaarch for anything today that uses the word "model" or "agent" and not be deluged with ML research (I wonder how "modeling agents", like those who act as business representatives for fashion models, are able to get their websites seen today. hmm.. I digress.) I think I would likely use one of scikit-lears functions for grid search. But in any case, if you search for info on this, I think it might be ok that 99% of the results are focused on ML model training hyperparameter tuning, because the basic premise, of seaarching a parameter space - is going to be similar, even if your use case - your model - is not a neural network or the like.
4. I found that there is literature specifically on database parameter tuning, and some on exactly what I was looking for (a  benchmarking suite, or at least papers describing them). One example: https://dl.acm.org/doi/10.1145/3716638


 ### motivation that lead to all of this stuff
 ### sorry it has taken so long to document

Your project looks well structured and as I mentioned in that rambling text from an uber the other day, it happened to overlap with a few things I have been working on, but for different overall purposes, so I got nerdsniped.

The one specific thing I wanted to explore (and hopefully, find something useful I could share with you) was the  single "confidence score". Addiitonally, the fact that your benchmarks looked so good. :-) I didnt doubt they were real, or think that you were misrepresenting numbers, or anything of that sort, but from experience I know that sometimes the happy path yields great metrics,  but any deviation from the synthetic tests can make everything crumble in unexpected ways. So I thought it would be fun to create some adversarial test cases to see how your fingerprinter did with then.

Oh, also, I read your whitepaper shortly after I started looking at the code, so that made me really pay attention to what it was doing, simply because I was reading the paper. That lead to these sorts of thoughts:

- how browser fingerprinting and entity/identity resolution overlap in ways
- perhaps evil ways from ad/tracking companies and all the other companies that harvest so much data about us
- butI tried to steer away from that particular topic; it still informed some of my other later thoughts about what does he want to be, just a finfgerprinter? or might he have the same Entity Resolver thoughts as I do?

But then, seeing it for what it is now,m my mind turned to:

- what breaks it in practice
- what kinds of drift it tolerates
- what kinds of collisions it invites
- what exactly that single scaalar confidence score means.


 A single confidence number like that has ambiguous meanings
- Does it mean "definitely same device" or "probably same, needs confirmation"?
- Is it high because of strong canvas match, or many weak signals?
- Does low evidence richness drag it down?
- Is this a generic fingerprint (attractor) that many devices share?

Long bunch of rambling typing delete so I can get to the point. I wanted to see if anything "better materialized from exposing more metrics, and calculatingf scores based on these multiple  metrics.

This lead to more of the "what does he want this product to do ultimately?" type questions, so fast-forwarding a bit, thats how I ended up adding the stuff from the "profiles"a branch. I thought the same numbers could result in a different score because they would weight certain types of matches/failures/etc diffefrently than a different business model using the same product. So, profiles  - different lenses through which to look ata the samae numbers.

Fir thge soeciufiuc branches and phases, will after merging it all into the profile-family branach, it's a bit of a blue to me how it happened, but see the other two README anbd their companio USAGE files and I think you'll get the whole picture.

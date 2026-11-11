# Attention and salience: why the eye goes where it goes

Part V, Hierarchy science. This chapter covers the perception research behind [HIERARCHY.md](../../HIERARCHY.md): what wins attention bottom-up, what the eye does next, and what people simply miss. Each section ends with the rule it gives our games. [Chapter 85](85-measuring-hierarchy.md) turns these into measurements.

## Takeaway

Attention goes to the place that **differs most from its surroundings** in a few basic features (colour, motion, orientation, size, luminance), **appears suddenly**, or **approaches**. It then moves on and is briefly slow to come back. Everything that isn't attended is close to invisible, however big it is. Hierarchy is therefore about **difference, not volume**. A bright thing among bright things is quiet; a dim thing in a calm field is loud.

## 1. Pre-attentive features: what can win without searching

**Findings**
- Feature Integration Theory (Treisman & Gelade, 1980) separates features that are registered in parallel across the whole view from conjunctions, which need attention item by item. Guided Search (Wolfe; version 6.0 in 2021) refines this: pre-attentive features *guide* a serial deployment of attention, and guidance comes from top-down and bottom-up feature maps plus scene structure, history and value. ([Wolfe 2021, GS6](https://pmc.ncbi.nlm.nih.gov/articles/PMC8965574))
- Wolfe estimates there are about one to two dozen guiding attributes. **Colour, size, motion and orientation appear on essentially every list**; others, such as faces, are still contested. ([Wolfe 2021](https://search.bwh.harvard.edu/new/pubs/Wolfe2021_GS6.pdf); [Wolfe & Horowitz 2004](https://search.bwh.harvard.edu/new/pubs/WolfeHorowitzNRN04.pdf))
- A pre-attentive feature is defined as one that guides search and can't be broken into simpler features. There is no single foolproof test for one. ([Wolfe & Utochkin, PMC6513732](https://pmc.ncbi.nlm.nih.gov/articles/PMC6513732))

**Rules for us**
1. **Code each hierarchy level with one undoubted feature first** (colour, size, motion or orientation). Conjunctions such as "the gold one with the small star" need search and don't pop out.
2. **Pop-out only works against a uniform background.** One gold card among grey cards pops; one gold card among rainbow cards is a search task. This is why HIERARCHY §5 gives colour jobs and §13 allows one loud element per panel.
3. **Don't rely on faces, words or icons to pop out.** They are read, not pre-attended, so they work once the player is already looking at them.

## 2. Salience maps: a computable model of "what differs"

**Findings**
- Itti, Koch & Niebur (1998) compute salience as centre-surround differences: fine scale minus coarse scale, as in early visual neurons. They build 42 feature maps (6 intensity, 12 colour, 24 orientation), merge them into one salience map, and a winner-take-all network picks locations in decreasing order of salience. ([Itti et al. 1998, IEEE TPAMI 20(11)](https://sites.krieger.jhu.edu/cns/files/2021/08/Itti_etal98.pdf))
- Their normalisation step promotes maps with **a few strong peaks** and suppresses maps with many similar peaks. That is the computational form of "one odd item beats a texture".
- Hou & Zhang (2007) get a fast, training-free salience map from the **spectral residual**: the image's log-amplitude spectrum minus its local average, transformed back to space. ([CVPR 2007](https://mlanthology.org/cvpr/2007/hou2007cvpr-saliency); [project page](https://bcmi.sjtu.edu.cn/~zhangliqing/Projects/SpectralResidualApproach/spectralresidual.htm))
- Real fixations also have a strong **centre bias** that is largely independent of content and task (Tatler 2007). A central Gaussian blob alone beats many salience models at predicting fixations. In one study, image salience models explained 23% less variance than centre bias alone. ([Hayes & Henderson](https://viscoglab.ucdavis.edu/sites/g/files/dgvnsk12381/files/inline-files/hayeshendersoncenterbias.pdf); [Frontiers 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5671469))

**Rules for us**
1. **Salience is measurable, so measure it.** `tools/hierarchy` combines both models (spectral residual plus an OKLab centre-surround with Itti normalisation) and predicts the first five fixations ([chapter 85](85-measuring-hierarchy.md)).
2. **The centre is already loud.** Put tier 1–2 events at or near the character or screen centre, where eyes rest anyway. Corners need a stronger cue to win (§5 below).
3. **Bottom-up salience is half the story.** Players also look where their goal points them: the next upgrade they can afford, or the enemy about to hit them. A screen passes only when salience *and* the task point at the same element.

## 3. What captures attention involuntarily: onsets and looming

**Findings**
- **Abrupt onsets capture attention.** In Yantis & Jonides (1984), an item that appeared suddenly was processed first, while items revealed gradually (by removing camouflage) were not. Jonides & Yantis (1988) found that colour or luminance *changes* of existing items did not capture the same way. Later work ties capture to the **appearance of a new object**, even an equiluminant one (Hillstrom & Yantis 1994; Gellatly et al. 1999). ([Yantis & Jonides 1984](https://link.springer.com/content/pdf/10.3758/BF03208805.pdf); [review, Frontiers 2013](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2013.00958/pdf))
- **Moving and looming stimuli capture attention; in Franconeri & Simons (2003), receding ones did not.** The authors proposed a "behavioural urgency" account. Later work is mixed: receding stimuli in stereoscopic depth did capture attention (Abrams & Christ), and one study found looming and receding equal. ([Franconeri & Simons 2003](https://visualcognition.psych.northwestern.edu/publications/FranconeriSimons_Motion.pdf); [Skarratt et al.](https://hull-repository.worktribe.com/output/460957/prioritization-of-looming-and-receding-objects-equal-slopes-different-intercepts))

**Rules for us**
1. **New objects are the loudest thing we can make.** Reserve sudden spawns of UI elements (popups, banners, new icons) for tiers 1–3. Tier 4–6 content fades in, grows in from scale 0.9 or slides; it never pops in on one frame.
2. **Recolouring an existing element is quieter than spawning a new one.** Use recolours and fills for state changes (affordable, cooldown ready), and spawns for events.
3. **Approach is urgent.** Scale-up and toward-camera motion (projectiles, boss lunges, a reward flying *at* the player) read as "act now". Effects leaving the screen (coins flying to the counter) read as "done". Use this direction rule for telegraphs versus confirmations.

## 4. After capture: inhibition of return and the attentional blink

**Findings**
- **Inhibition of return (IOR):** after attention leaves a cued place, responses there are *slower* than elsewhere. In Posner & Cohen (1984), the early advantage at the cued location reversed from roughly 300 ms after the cue. The effect is about 20 ms, and its mechanism is still debated. ([psytoolkit summary](https://www.psytoolkit.org/library/ior.html); [Klein review, PMC3064739](https://pmc.ncbi.nlm.nih.gov/articles/PMC3064739))
- **Attentional blink:** the second of two targets is often missed if it comes about **200–500 ms** after the first (Raymond, Shapiro & Arnell 1992). A target within about 100–150 ms is spared ("lag-1 sparing"). ([review, PMC2915904](https://pmc.ncbi.nlm.nih.gov/articles/PMC2915904); [Potter, MIT](https://dspace.mit.edu/bitstream/1721.1/110428/1/Potter_Attentional%20episodes.pdf))

**Rules for us**
1. **Space separate messages at least 500 ms apart**, or merge them into one beat that arrives within about 100 ms. "+1 level", then "new skill" 300 ms later, then "chest" 300 ms later loses the middle one. This sets the timing for reward sequencing (HIERARCHY §14).
2. **A repeated cue in the same place gets weaker.** If a warning must fire again, change its place, size or modality (add sound) instead of re-flashing the same spot.
3. Our scanpath model applies IOR by suppressing each fixated area before picking the next, which is how the auditor predicts fixations 2–5.

## 5. Peripheral vision and crowding

**Findings**
- **Bouma's law:** a target in peripheral vision can't be identified when flankers sit closer than about **0.4–0.5 × its eccentricity** (its distance from where you're looking). In a 50-observer study, the linear law explained about 82% of the variance. ([Bouma law in 50 observers, PMC10408772](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10408772/); [review, PMC3070834](https://pmc.ncbi.nlm.nih.gov/articles/PMC3070834))
- Peripheral **temporal** sensitivity is about as good as foveal (McKee & Nakayama 1984), and flicker sensitivity rises somewhat with eccentricity, while spatial resolution falls steeply. ([Bex & Dakin](https://www.ucl.ac.uk/~smgxpbe/BexDakin05.pdf); [Chapiro et al. 2023](https://www.cl.cam.ac.uk/~rkm38/pdfs/chapiro2023_cff_high_lum.pdf))
- The useful field of view (Ball et al. 1988) shrinks under load and varies a lot between people. ([Loschky et al. 2017](https://www.bu.edu/ballab/pubs/Loschky_2017.pdf))

**Rules for us**
1. **Bouma in pixels:** the ratio has no units, so measure in screen pixels from where the player is looking (usually the character). A HUD icon 800 px from the character needs about 400 px of clear space around it to be *identified* without a glance. Corners can't afford that, so **peripheral HUD elements must signal by colour, motion or a single big shape, not detail.**
2. **Motion and flicker are the right tools for the periphery,** which is why a gentle pulse on a ready ability works in a corner where a text change doesn't. The flip side: peripheral flicker is hard to ignore, so ambient effects near the edges must stay slow.
3. **Under load, the useful field of view shrinks.** In surge, boss and finale rungs (HIERARCHY §4), move critical cues closer to the character, or add sound.

## 6. Blindness to the unattended

**Findings**
- **Inattentional blindness:** with attention on a counting task, many observers miss a person in a gorilla suit walking through the scene. About half is the commonly quoted rate (Simons & Chabris 1999; the 50% figure is from a later account by Chabris). ([Simons & Chabris 1999](https://moodle2.units.it/pluginfile.php/242405/mod_resource/content/0/Simons1999.pdf); [Scientific American](https://www.scientificamerican.com/article/how-blind-are-we/))
- **Change blindness:** large changes go unnoticed when a brief blank or another disturbance masks the change signal, as in the flicker paradigm of Rensink et al. 1997. ([Simons 2000](https://home.cs.colorado.edu/~mozer/Teaching/syllabi/3702/readings/Simons2000.pdf); [Simons & Rensink 2005](https://www.cs.ubc.ca/~rensink/publications/download/S&R-TICS-05a.pdf))

**Rules for us**
1. **Never change important state during a screen flash, camera cut, screen-shake peak or window transition.** The transition masks the change signal. Change it after the transition settles and give it its own onset.
2. **During a task, the player sees almost nothing outside it.** A new shop item announced only by a badge while the player fights will be missed. Queue it for the next calm frame (HIERARCHY §6).
3. Our auditor can't predict what a busy player will miss. Treat any important element that isn't in the predicted top three fixations as missed.

## 7. Gaps

- Salience models predict free viewing. Games are task-driven, so top-down goals, learned layouts and reward history are missing from them. Guided Search 6 models these as separate guidance sources, but we have no measured weights for game HUDs. **UNKNOWN — needs our own playtest data** (see [chapter 85](85-measuring-hierarchy.md#5-validating-with-people)).
- Crowding constants vary with stimulus and task. 0.4–0.5 is a first-order rule, not a guarantee.
- The looming-versus-receding debate is unresolved. Treat "approach is urgent" as a design convention backed by one strong result, not a law.

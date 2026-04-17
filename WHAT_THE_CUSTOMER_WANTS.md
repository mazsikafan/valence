# What The Customer Wants To See

## Who are the customers and what do they care about?

### Customer 1: AI Station Technician (Daily Use)
**Question:** "Can I process this ejaculate into straws?"

They need in under 60 seconds:
1. **Concentration** — is it above 500 M/mL? (below = reject immediately)
2. **Motility** — is progressive motility above 60%? (below = discard ejaculate)
3. **Dose calculation** — how many straws can I make from this ejaculate?
4. **Pass/Fail** — green light or red light

They do NOT care about per-cell kinematics. They want a traffic light.

### Customer 2: Veterinarian (Breeding Soundness Exam)
**Question:** "Is this bull fit to breed?"

They need a standardized BSE form:
1. **Scrotal circumference** — meets age-based minimum?
2. **Gross motility score** — Fair or better?
3. **Individual progressive motility** — >=30%?
4. **Morphology** — >=70% normal?
5. **Classification** — Satisfactory / Deferred / Unsatisfactory
6. Physical exam findings (they enter manually, our system fills semen part)

### Customer 3: Breeding Company Manager
**Question:** "Is this bull's semen quality stable or declining?"

They need:
1. **Trend charts** — motility and morphology over time per bull
2. **Bull comparison** — rank bulls by quality score
3. **Seasonal patterns** — summer heat stress effects
4. **Alerts** — "Bull XYZ quality dropped 15% this month"

### Customer 4: Researcher
**Question:** "Give me all the raw data."

They need:
1. Per-cell data export (CSV)
2. All kinematic parameters per sperm
3. Morphometric measurements
4. Reproducible analysis with parameter settings documented

---

## The Scoring Scales That Exist

### Scale 1: Mass/Wave Motility (0-5 scale, Evans & Maxwell 1987)
Used for undiluted semen under low magnification. The classic field test.

| Score | Motility | What You See |
|-------|----------|-------------|
| **0** | 0% | Dead. No movement at all |
| **1** | ~10% | Occasional twitching, very few active cells |
| **2** | 20-40% | Some movement, no wave pattern |
| **3** | 40-70% | Small, slow waves visible. **MINIMUM for AI** |
| **4** | 75-90% | Dense, vigorous waves. Good quality |
| **5** | >90% | Intense, rapid swirling. Excellent |

### Scale 2: Gross Motility (4 categories, North American BSE)
Same observation, different labeling:

| Rating | Equivalent | Passes BSE? |
|--------|-----------|-------------|
| Very Good | Score 4-5 | Yes |
| Good | Score 3-4 | Yes |
| Fair | Score 2-3 | Yes (minimum) |
| Poor | Score 0-2 | No |

### Scale 3: WHO Individual Motility Grades (a/b/c/d)
Assessed on diluted sample at high magnification:

| Grade | Name | Speed | In Our System |
|-------|------|-------|---------------|
| **a** | Rapid progressive | >25 um/s forward | Progressive (fast) |
| **b** | Slow progressive | Forward but slower | Progressive (slow) |
| **c** | Non-progressive | Moving, no forward progress | Non-progressive |
| **d** | Immotile | No movement | Static |

WHO 5th edition collapsed a+b into "progressive" and kept c and d. WHO 6th edition restored a/b/c/d.

### Scale 4: BSE Classification (3 tiers, Society for Theriogenology)
The final verdict:

| Classification | Criteria | Action |
|---------------|----------|--------|
| **Satisfactory** | SC meets minimum + motility >=30% + morphology >=70% | Cleared for breeding |
| **Deferred** | Marginal results or temporary condition | Retest in 30-60 days |
| **Unsatisfactory** | Fails criteria, structural defects | Replace bull |

### There is NO standard "8-layer scale"
Searched exhaustively. The scales that exist are: 0-5 (mass motility), 4-category (gross), a/b/c/d (WHO), 3-tier (BSE). Some CASA vendors may use proprietary composite scores but none are an industry-standard 8-point scale.

---

## The Exact Report Fields (What Goes On Paper)

### Section A: Sample Identification
```
Report ID:           _______________
Date/Time:           _______________
Bull ID:             _______________
Breed:               _______________
Age:                 ___ years ___ months
Owner/Station:       _______________
Collection Method:   [ ] AV  [ ] EE
Ejaculate Number:    _____ (today)
Sample Type:         [ ] Fresh  [ ] Frozen-Thawed
Straw Lot Number:    _______________ (if frozen)
```

### Section B: Macroscopic Evaluation
```
Volume:              ___ mL
Color:               [ ] Creamy  [ ] Milky  [ ] Watery  [ ] Bloody
Consistency:         [ ] Thick  [ ] Medium  [ ] Thin
```

### Section C: Concentration
```
Method:              [ ] Photometer  [ ] CASA  [ ] Hemocytometer
Concentration:       ___ million/mL
Total Sperm Count:   ___ billion (volume x concentration)
```

### Section D: Motility Assessment
```
Mass Motility Score: [ ]0  [ ]1  [ ]2  [ ]3  [ ]4  [ ]5
Total Motility:      ____%
Progressive Motility: ____%
  - Rapid (WHO a):   ____%
  - Slow (WHO b):    ____%
Non-Progressive:     ____%
Immotile:            ____%
```

### Section E: Kinematic Parameters (CASA only)
```
VCL:    ___ um/s    (curvilinear velocity)
VSL:    ___ um/s    (straight-line velocity)
VAP:    ___ um/s    (average path velocity)
LIN:    ____%       (linearity = VSL/VCL)
STR:    ____%       (straightness = VSL/VAP)
WOB:    ____%       (wobble = VAP/VCL)
ALH:    ___ um      (lateral head amplitude)
BCF:    ___ Hz      (beat cross frequency)
```

### Section F: Morphology
```
Method:              [ ] Eosin-nigrosin  [ ] Spermac  [ ] Phase contrast
Cells Counted:       ___ (minimum 100)
Normal Forms:        ____%

Defect Breakdown:
  Head defects:      ____%  (pyriform, tapered, detached, vacuoles)
  Midpiece defects:  ____%  (bent, thickened, DMR)
  Tail defects:      ____%  (coiled, bent, short)
  Prox. droplets:    ____%
  Distal droplets:   ____%
  Other:             ____%
Total Abnormal:      ____%
```

### Section G: Quality Decision
```
                    ┌─────────────────────────┐
                    │                         │
                    │    [ ] SATISFACTORY      │
                    │    [ ] DEFERRED          │
                    │    [ ] UNSATISFACTORY    │
                    │                         │
                    └─────────────────────────┘

Reason (if deferred/unsatisfactory): _______________
Recommended retest date: _______________
```

### Section H: Dose Calculation (AI Stations Only)
```
Target sperm/straw:  ___ million (standard: 15-25M)
Straw size:          [ ] 0.25 mL  [ ] 0.50 mL
Expected survival:   ___% (post-thaw, typically 50-60%)

Calculated:
  Total motile sperm:    ___ billion
  Post-thaw motile:      ___ billion
  Number of straws:      ___
  Extender volume:       ___ mL
  Dilution ratio:        1:___
```

### Section I: Post-Thaw QC (Frozen Semen Only)
```
Thaw protocol:       ___ °C for ___ seconds
Post-thaw motility:  ____%  (minimum: 30%)
Acrosome integrity:  ____%  (minimum: 65%)
HOST result:         ____%  (minimum: 40%)
Incubation test:     <10% drop per 30 min? [ ] Yes [ ] No
Bacterial count:     ___ CFU/mL (maximum: 5000)

RELEASE DECISION:    [ ] APPROVED  [ ] REJECTED
```

---

## What Our System Can Fill vs What It Cannot (Today)

| Report Section | We Can Do It? | How |
|---|---|---|
| Sample identification | Partially | User enters in upload form |
| Volume | No | Requires physical measurement |
| Color/consistency | No | Requires visual inspection |
| Concentration | No | Needs video (Module 2) or hemocytometer |
| Mass motility score (0-5) | No | Needs video (Module 2) |
| Total motility % | No | Needs video (Module 2) |
| Progressive motility % | No | Needs video (Module 2) |
| Kinematic parameters | No | Needs video (Module 2) |
| **Morphology — normal %** | **YES** | **Module 1 (86% AUC)** |
| **Morphology — defect breakdown** | **YES** | **Module 1 (10 classes)** |
| **Quality decision (morphology component)** | **YES** | **>=70% normal = satisfactory** |
| Dose calculation | Partially | If user enters volume + concentration |
| Post-thaw QC | No | Needs thawed sample analysis |

### Our value proposition today:
**We automate the morphology section** — which is the most tedious, subjective, and time-consuming part of semen evaluation. Counting 100+ cells under oil immersion takes 15-30 minutes manually. We do it in seconds.

### With Module 2 (video):
We'd cover morphology + motility + concentration = **the three core measurements** that together determine the BSE classification.

---

## How iSperm / Ongo / SQA-V Present Results (Competitor UX)

### iSperm (iPad)
- Big numbers front and center: **Total Motility** and **Concentration**
- Color-coded sperm tracks on microscopy image
- Dose calculation built in (enter volume → get straw count)
- One-tap export to email/cloud
- Under 10 seconds per analysis

### Ongo Vision
- Two-panel: left = sample info + repeat measurements, right = current reading
- Shows: cell count, concentration, motility
- Export: CSV, PDF, MP4 video
- 30-50 seconds per analysis

### SQA-Vb
- Single readout screen: concentration, motility %, progressive %, morphology %
- Under 1 minute
- Includes B-Sperm data management software
- Validated against >8000 bovine inseminations

### What they all have in common:
1. **Big, bold primary numbers** (motility %, concentration)
2. **Traffic light quality indicator** (pass/fail/review)
3. **One-click report export**
4. **Fast** (<60 seconds)
5. **Dose calculator** built in

---

## Recommendation: Our Report Should Look Like This

### Priority 1 (immediate — what we show today):
```
┌──────────────────────────────────────────────┐
│  MORPHOLOGY ANALYSIS                         │
│                                              │
│  Normal: ██████████████░░░░░░ 72%            │
│                                              │
│  ● SATISFACTORY                              │
│                                              │
│  Head defects:    8%   Tail defects:   12%   │
│  Droplets:        4%   Other:          4%    │
│                                              │
│  Cells analyzed: 147   Time: 4.2s            │
│  [Annotated image]  [Download PDF]           │
└──────────────────────────────────────────────┘
```

### Priority 2 (with Module 2 — video):
```
┌──────────────────────────────────────────────┐
│  COMPLETE SEMEN ANALYSIS                     │
│                                              │
│  Motility: 72%    Progressive: 48%           │
│  Concentration: 1,240 M/mL                  │
│  Morphology: 74% normal                     │
│                                              │
│  ● SATISFACTORY                              │
│                                              │
│  Doses (@ 20M/straw): ~380 straws           │
│  Extender needed: 181.5 mL                  │
│                                              │
│  [Motility tracks]  [Morphology detail]      │
│  [Download Full Report]                      │
└──────────────────────────────────────────────┘
```

### Priority 3 (with university data — trending):
```
┌──────────────────────────────────────────────┐
│  BULL PERFORMANCE DASHBOARD                  │
│                                              │
│  Bull: HU-042 Holstein | 4.2 years           │
│  Last 6 ejaculates:                          │
│  [trend line chart: motility + morphology]   │
│                                              │
│  ⚠ Motility trending down (-8% over 3 mo)  │
│  ✓ Morphology stable (73-76%)               │
│                                              │
│  Season comparison: Summer vs Winter         │
│  [comparison bar chart]                      │
└──────────────────────────────────────────────┘
```

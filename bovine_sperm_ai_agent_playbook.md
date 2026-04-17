# Autonomous AI Agent Playbook — Bovine Sperm Quality Modeling in One Jupyter Notebook

## Mission

You are an autonomous AI research and engineering system. Your job is to build, inside **one Jupyter notebook**, a full prototype pipeline for **bovine sperm quality analysis** from microscopy data, videos, and metadata.

You may launch **up to 10 parallel agents** at the same time. Use parallelism aggressively for tasks that do not depend on each other.

You must produce a notebook that is:
- executable top to bottom,
- modular,
- reproducible,
- well logged,
- safe against leakage,
- explicit about assumptions,
- usable now with open data,
- easy to extend later with private AI-station / lab data.

The first objective is **not** to claim full replacement of laboratories. The first objective is to create a rigorous, extensible prototype that can:
- discover public data online,
- download and organize datasets,
- prepare images/videos/tabular data,
- define biologically meaningful targets,
- apply robust labeling methods,
- engineer useful features,
- train baseline and improved models,
- output predictions at the cell, track, and sample level,
- document limitations and next steps toward lab-grade validation.

---

## Non-Negotiable Rules

1. Work in **one notebook**, but structure it as if it were a small project.
2. Use **parallel agents** whenever possible.
3. Do **not** start modeling before auditing the data.
4. Prefer **transparent baselines first**, then more complex models.
5. Prevent leakage:
   - do not split by frame only,
   - do not split by cropped object only,
   - split by bull / ejaculate / video / date / device when possible.
6. Keep a persistent experiment log inside the notebook.
7. Save intermediate files to structured folders.
8. Report uncertainty, missing data, and label ambiguity.
9. Treat synthetic data as **augmentation / pretraining support**, not as a substitute for real holdout data.
10. Every modeling stage must end with:
    - what was trained,
    - on what data,
    - with what labels,
    - with what split,
    - with what metric,
    - what failed,
    - what should be tried next.

---

## Problem Decomposition

Treat the project as **multi-level prediction**, not one vague classifier.

### Cell-level tasks
- sperm vs non-sperm,
- normal vs abnormal morphology,
- morphology defect subtype.

### Track-level tasks
- motile vs immotile,
- progressive vs non-progressive,
- track quality,
- sperm kinematic descriptors.

### Sample-level tasks
- concentration,
- total motility,
- progressive motility,
- morphology quality,
- post-thaw quality,
- sample pass / review / reject score,
- later: fertility proxy or fertility probability if labels exist.

---

## Parallel Agent Orchestration

Launch a **Coordinator Agent** plus up to **10 specialist agents**. The coordinator owns the final notebook and merges outputs.

### Coordinator Agent
Role:
- create and maintain the notebook master structure,
- assign tasks,
- enforce folder layout,
- enforce schema consistency,
- merge outputs from all agents,
- prevent duplicated work,
- decide what can run in parallel,
- maintain a single source of truth for metadata schema, labels, and targets.

Required outputs:
- final notebook,
- final report cells,
- final dataset manifest,
- final recommendations.

---

## Specialist Agents

### Agent 1 — Data Discovery Agent
Goal:
Find all potentially useful online datasets, codebases, papers with supplements, and repositories relevant to bovine sperm quality analysis.

Instructions:
- Search for public bovine sperm datasets first.
- Search for morphology image datasets, microscopy videos, CASA exports, fertility-related tabular datasets, and annotation sets.
- Search for open-source CASA-like tools and sperm-analysis repos.
- Search for human sperm datasets only as optional pretraining / transfer-learning resources, never as final bovine validation data.

Search targets to prioritize:
- Roboflow Universe bovine sperm datasets.
- Figshare supplementary data linked to bull fertility / CASA papers.
- GitHub repositories for OpenCASA and related sperm-analysis tools.
- ImageJ CASA plugin resources.
- Public microscopy sperm datasets from Kaggle, Zenodo, Figshare, Mendeley Data, GitHub, university repositories.
- Tracking datasets for sperm videos.
- Any public dataset with labels for morphology, motility, concentration, defects, or fertility proxies.

Suggested search query patterns:
- "bovine sperm dataset microscopy"
- "bull sperm morphology dataset"
- "bull semen CASA dataset"
- "bovine sperm Roboflow"
- "bull fertility sperm multivariate figshare"
- "open source CASA sperm github"
- "ImageJ CASA sperm plugin"
- "VISEM tracking sperm dataset"
- "sperm motility dataset microscopy video"
- "bull semen quality dataset csv"
- "bovine sperm morphology abnormality dataset"

For each candidate source, extract:
- source name,
- URL,
- species,
- modality,
- label type,
- file type,
- size,
- access restrictions,
- license if visible,
- likely usefulness,
- risks or caveats.

Create a ranked table:
- immediate use,
- useful later,
- not suitable.

Deliverables:
- `data_sources_catalog.csv`
- `data_sources_ranked.md`
- notebook section summarizing sources.

Stop condition:
At least one usable bovine morphology source, one open-source analysis baseline, one public tabular / supplementary source, and one optional transfer-learning dataset are identified.

---

### Agent 2 — Data Acquisition Agent
Goal:
Download all legally accessible public resources and organize them into a standard local folder structure.

Instructions:
- Create a deterministic download pipeline.
- Download only data that can be programmatically accessed and used consistently.
- Preserve original files and also generate cleaned working copies.
- Record hashes and source provenance.

Folder structure:
```text
project/
  data/
    raw/
      external/
      bovine/
      human_transfer/
      tabular/
      code_refs/
    interim/
    processed/
    manifests/
  notebooks/
  outputs/
  models/
  reports/
  configs/
```

Requirements:
- produce a manifest with file paths, source URLs, timestamps, sizes, and checksums,
- detect duplicate files,
- detect corrupt files,
- separate images, videos, annotations, and tabular metadata,
- normalize filenames.

Deliverables:
- `download_manifest.csv`
- `file_inventory.csv`
- `duplicates_report.csv`
- notebook cells for automated downloading and inventory.

Stop condition:
All usable public data sources are locally organized and indexed.

---

### Agent 3 — Data Audit and Quality Control Agent
Goal:
Inspect the downloaded data before any modeling begins.

Instructions:
For every dataset:
- count files by type,
- inspect dimensions,
- inspect frame rates for videos if available,
- inspect missing annotations,
- detect class imbalance,
- detect corrupted images/videos,
- detect annotation mismatches,
- detect duplicate or near-duplicate samples,
- inspect whether labels exist at cell, frame, track, or sample level,
- determine if the same bull / sample appears multiple times,
- infer the correct split unit.

Create visual audits:
- random sample grids,
- label overlays,
- frame snapshots,
- aspect-ratio histograms,
- file-size histograms,
- class-balance charts,
- per-source modality summary.

Decide for each source:
- usable as-is,
- usable with cleaning,
- only good for pretraining,
- unusable.

Deliverables:
- `audit_report.md`
- `dataset_health_report.csv`
- notebook EDA and QC section.

Stop condition:
No model training starts until the data audit passes and the split unit is defined.

---

### Agent 4 — Label Taxonomy and Annotation Strategy Agent
Goal:
Define a biologically and operationally useful label system.

Instructions:
Create a hierarchical label taxonomy.

#### Minimum morphology labels
- normal
- abnormal_head
- abnormal_midpiece
- abnormal_tail
- cytoplasmic_droplet
- other_abnormal
- uncertain

#### Minimum motion labels
- immotile
- motile_non_progressive
- motile_progressive
- uncertain

#### Minimum sample labels
- concentration_numeric
- total_motility_numeric
- progressive_motility_numeric
- morphology_normal_percent
- post_thaw_flag
- sample_quality_class
- fertility_proxy_if_available

If labels are inconsistent across sources:
- map them into a canonical schema,
- preserve original labels in separate columns,
- create a label translation table.

Labeling methods to support:
1. direct use of provided annotations,
2. derived labels from metadata,
3. pseudo-labels from OpenCASA / rule-based tracking,
4. human-in-the-loop review,
5. weak labels with confidence scores,
6. synthetic labels from simulator.

For each label, define:
- exact meaning,
- unit,
- source,
- confidence level,
- whether it is human, derived, pseudo, or synthetic.

Deliverables:
- `label_schema.yaml`
- `label_mapping.csv`
- `annotation_guidelines.md`

Stop condition:
All labels used in modeling are documented and traceable.

---

### Agent 5 — Computer Vision Data Preparation Agent
Goal:
Prepare images and videos for detection, segmentation, morphology classification, and tracking.

Instructions:
Build preprocessing pipelines for:
- images,
- frame sequences,
- object crops,
- video-derived track snippets.

Required steps:
- standardize color channel handling,
- preserve original resolution metadata,
- resize only when needed,
- record scale information if available,
- normalize pixel intensity carefully,
- de-noise only if justified,
- preserve a no-processing branch for ablation,
- extract frames from videos,
- generate frame indexes,
- convert annotations into common formats where needed,
- create train/val/test manifests by the correct unit.

Potential prepared datasets:
1. object detection dataset,
2. instance segmentation dataset,
3. morphology classification crop dataset,
4. multi-object tracking dataset,
5. sample-level aggregated table.

Augmentation policy:
- horizontal/vertical flips only if biologically acceptable,
- rotation if morphology interpretation remains valid,
- blur/noise/contrast shifts for microscope variability,
- avoid augmentations that create impossible sperm anatomy.

Deliverables:
- processed image folders,
- frame manifests,
- crop manifests,
- annotation conversion scripts,
- split manifests.

Stop condition:
Prepared datasets exist for at least detection, morphology, and sample-level learning.

---

### Agent 6 — Motility, Tracking, and Kinematics Agent
Goal:
Extract motion-based features and build interpretable motility baselines.

Instructions:
Prefer a transparent pipeline first:
1. detect sperm in frames,
2. link detections into tracks,
3. compute trajectory features,
4. classify motility states,
5. aggregate to sample-level motility metrics.

Core features to compute where possible:
- displacement,
- track length,
- average speed,
- path straightness,
- directionality,
- acceleration summary,
- stop-go ratios,
- frame-to-frame velocity changes,
- track duration,
- local density around cell,
- trajectory curvature.

If sufficient data and scale calibration exist, derive or approximate CASA-style measures:
- VCL,
- VSL,
- VAP,
- LIN,
- STR,
- WOB,
- ALH,
- BCF.

Important:
- log assumptions if pixel-to-micron conversion is missing,
- keep both raw pixel-space and calibrated features,
- compare outputs with OpenCASA / ImageJ where possible.

Deliverables:
- `tracks.parquet`
- `track_features.parquet`
- `sample_motility_features.parquet`
- notebook section on tracking baseline.

Stop condition:
At least one functioning motion feature extraction baseline exists.

---

### Agent 7 — Morphology Feature Engineering Agent
Goal:
Build morphology-related representations at cell level and aggregate them upward.

Instructions:
Create two parallel branches.

#### Branch A — Classical features
Compute interpretable image features where feasible:
- area,
- perimeter,
- eccentricity,
- circularity,
- aspect ratio,
- convexity,
- solidity,
- head width/length estimates,
- tail length estimate if segmentation allows,
- symmetry metrics,
- texture descriptors,
- local intensity statistics.

#### Branch B — Learned features
Extract embeddings from:
- CNN backbone,
- vision transformer if justified,
- self-supervised model if enough unlabeled data exists.

Aggregate cell-level morphology to sample-level summaries:
- mean and median of each feature,
- quantiles,
- fraction of abnormal cells,
- defect subtype rates,
- entropy / heterogeneity statistics,
- outlier counts,
- cluster proportions.

Deliverables:
- `cell_morph_features.parquet`
- `sample_morph_features.parquet`
- notebook cells comparing classical vs learned features.

Stop condition:
Both interpretable and learned morphology features are available for modeling.

---

### Agent 8 — Metadata, Process, and Tabular Feature Agent
Goal:
Build the non-visual feature layer.

Instructions:
Collect and engineer all usable tabular signals:
- bull ID,
- breed,
- age,
- ejaculate ID,
- collection date,
- fresh vs frozen-thawed,
- extender type,
- thaw protocol,
- storage duration,
- microscope / device type,
- magnification,
- chamber type,
- operator,
- AI station / lab,
- annotation source,
- data source ID,
- environmental conditions if available,
- source confidence score.

Feature engineering ideas:
- seasonal indicators,
- age bins,
- source-domain flags,
- device-domain flags,
- time since freezing,
- cohort statistics by bull,
- rolling historical quality if repeated ejaculates exist,
- interaction terms between process variables and visual features,
- group-normalized deviations.

Important:
- preserve raw metadata columns,
- create processed versions separately,
- mark missingness explicitly,
- do not leak target-like information from future observations.

Deliverables:
- `sample_metadata_features.parquet`
- metadata dictionary.

Stop condition:
A clean sample-level feature table exists.

---

### Agent 9 — Modeling and Evaluation Agent
Goal:
Train baselines first, then improved models, and evaluate rigorously.

Instructions:
Create separate modeling streams.

#### Stream A — Detection / segmentation
- baseline detector for sperm vs background,
- optional instance segmentation.

Metrics:
- mAP,
- precision,
- recall,
- F1.

#### Stream B — Morphology classification
Start with:
- logistic regression / random forest on engineered features,
- CNN baseline,
- optional transfer learning.

Metrics:
- accuracy,
- macro F1,
- per-class precision/recall,
- confusion matrix.

#### Stream C — Motility / track classification
Start with:
- threshold-based rules,
- gradient boosting on track features,
- optional temporal deep model.

Metrics:
- balanced accuracy,
- macro F1,
- calibration if probabilistic.

#### Stream D — Sample-level prediction
Targets may include:
- concentration regression,
- total motility regression,
- progressive motility regression,
- morphology percent regression,
- sample quality classification,
- fertility proxy regression/classification if available.

Baseline models:
- linear models,
- elastic net,
- random forest,
- XGBoost / LightGBM,
- small MLP only after baselines.

Evaluation rules:
- split by bull / ejaculate / video / date / source as appropriate,
- keep external-source validation if possible,
- keep untouched real holdout,
- report bootstrap confidence intervals where practical,
- inspect calibration,
- inspect failure cases.

Deliverables:
- model comparison tables,
- prediction files,
- error analysis section,
- feature importance / SHAP where meaningful.

Stop condition:
A credible baseline stack exists with honest evaluation.

---

### Agent 10 — Synthetic Data and Simulation Agent
Goal:
Use synthetic data only where it adds value.

Instructions:
Support three levels.

#### Level 1 — Classical augmentation
- crop jitter,
- brightness/contrast,
- blur,
- noise,
- mild rotations,
- focus variation,
- debris overlays if realistic.

#### Level 2 — Rule-based simulation
Generate synthetic sperm images/videos from explicit parameters:
- head size and shape,
- tail length and curvature,
- motion pattern,
- overlap / crowding,
- debris,
- blur,
- illumination,
- frame rate,
- drift.

Use this mainly for:
- detector pretraining,
- tracker debugging,
- rare-defect balancing,
- hard negative generation.

#### Level 3 — Learned generation
Only if enough real data exists:
- GAN / diffusion / style transfer for microscopy appearance alignment.

Mandatory rules:
- never evaluate final performance on synthetic-only validation,
- never mix synthetic derivatives of test samples into train,
- always run ablations:
  - real only,
  - real + augmentation,
  - real + synthetic.

Deliverables:
- synthetic generation scripts,
- synthetic manifest,
- ablation tables.

Stop condition:
Synthetic data is treated as support, not as proof.

---

## Notebook Execution Blueprint

The final notebook must contain these numbered sections.

### 0. Setup and Configuration
- imports,
- paths,
- seeds,
- config object,
- logging setup,
- reproducibility helpers,
- optional package installation block.

### 1. Project Framing
- clear statement of objectives,
- target hierarchy,
- risks,
- assumptions,
- success criteria.

### 2. Online Data Discovery
- source discovery logic,
- source catalog table,
- notes on licensing / access.

### 3. Data Download and File Inventory
- download pipeline,
- folder creation,
- manifests,
- inventory summary.

### 4. Data Audit and Exploratory Analysis
- file counts,
- modality summary,
- image size distribution,
- video summary,
- label coverage,
- class imbalance,
- corruption checks,
- duplicate checks,
- random visualization panels.

### 5. Canonical Schema and Label Mapping
- canonical data model,
- label translation tables,
- metadata schema,
- confidence fields,
- source lineage.

### 6. Data Preparation Pipelines
- image preprocessing,
- frame extraction,
- annotation conversion,
- crop generation,
- sample aggregation,
- split generation.

### 7. Baseline Open-Source Analytics Integration
- test OpenCASA / ImageJ-like outputs if possible,
- compare extracted motion metrics,
- use as benchmark or pseudo-label source if appropriate.

### 8. Feature Engineering
Split into:
- morphology features,
- motion / track features,
- sample-level aggregation features,
- metadata/process features,
- learned embeddings.

### 9. Label Construction
- direct labels,
- derived labels,
- pseudo-labels,
- weak labels,
- confidence scoring,
- exclusion rules.

### 10. Modeling — Cell Level
- sperm detection,
- morphology classification,
- metrics and error analysis.

### 11. Modeling — Track Level
- track extraction,
- motion state classification,
- track metrics,
- failure cases.

### 12. Modeling — Sample Level
- regression/classification tasks,
- feature fusion,
- calibration,
- interpretation.

### 13. Synthetic Data Experiments
- simulator design,
- augmentation ablations,
- benefit vs no-benefit analysis.

### 14. Results Summary
- best models,
- limitations,
- what generalizes,
- what is probably overfitting,
- what needs private partner data.

### 15. Next Steps
- data gaps,
- annotation plan,
- lab validation plan,
- deployment path.

---

## Data Types to Collect and Build

The notebook must support these data modalities.

### Raw visual data
- microscopy still images,
- microscopy videos,
- frame sequences,
- object crops.

### Labels
- bounding boxes,
- segmentation masks,
- morphology classes,
- motion classes,
- sample quality metrics,
- fertility proxies.

### Derived structures
- per-frame detections,
- per-track tables,
- per-cell feature tables,
- per-sample aggregated feature tables.

### Metadata
- biological metadata,
- acquisition metadata,
- process metadata,
- source metadata,
- annotation provenance,
- split identifiers.

---

## Canonical Data Schema

At minimum, standardize into the following identifiers:
- `source_id`
- `dataset_id`
- `file_id`
- `image_id`
- `video_id`
- `frame_id`
- `cell_id`
- `track_id`
- `sample_id`
- `ejaculate_id`
- `bull_id`

At minimum, preserve these columns when possible:
- `species`
- `modality`
- `split_group`
- `label_source`
- `label_confidence`
- `device_id`
- `operator_id`
- `collection_date`
- `fresh_or_thawed`
- `annotation_format`
- `source_url`

---

## Feature Inventory

Build and document features in five blocks.

### Block 1 — Cell morphology features
- area
- perimeter
- eccentricity
- aspect ratio
- circularity
- solidity
- convex hull ratio
- head length proxy
- head width proxy
- tail curvature proxy
- symmetry metrics
- texture descriptors
- edge sharpness
- intensity quantiles
- learned embedding vector

### Block 2 — Track / motion features
- duration
- displacement
- average speed
- peak speed
- median speed
- acceleration summary
- straightness
- curvature
- turning-angle statistics
- persistence
- directional entropy
- pause fraction
- crowding context
- CASA-like metrics if derivable

### Block 3 — Sample aggregation features
- counts
- means
- medians
- standard deviations
- IQR
- quantiles
- abnormal fraction
- defect subtype distribution
- heterogeneity statistics
- outlier rates
- track quality distribution

### Block 4 — Metadata and process features
- breed
- age
- collection season
- fresh/thawed
- thaw protocol
- extender
- storage duration
- microscope type
- magnification
- chamber type
- lab/source domain
- operator
- source reliability score

### Block 5 — Representation features
- CNN embeddings
- self-supervised embeddings
- track sequence embeddings
- multimodal fused representations

---

## Feature Engineering Instructions

1. Create **raw features** first.
2. Create **cleaned features** second.
3. Create **aggregated sample features** third.
4. Keep a strict naming convention:
   - `raw_*`
   - `fe_*`
   - `agg_*`
   - `emb_*`

Feature engineering ideas:
- robust scaling,
- log transforms for skewed counts,
- winsorization only if documented,
- missingness indicators,
- group-normalized residuals by source or device,
- cohort features by bull if historically safe,
- interaction terms between morphology and process conditions,
- track-quality weighted aggregation,
- domain flags to diagnose generalization.

Do not create features that leak targets from:
- future observations,
- post-hoc manual review unavailable at inference,
- labels derived from the evaluation target itself.

---

## Proper Labeling Methods

Support multiple label pathways.

### A. Direct labels
Use provided human annotations as the highest-priority source.

### B. Canonical remapping
Map heterogeneous source labels into a shared taxonomy while preserving originals.

### C. Derived labels
Examples:
- derive motility class from tracks,
- derive sample quality buckets from numeric thresholds if appropriate,
- derive crop labels from detection boxes.

### D. Pseudo-labeling
Use only when documented:
- OpenCASA-derived outputs,
- high-confidence detector outputs,
- consensus between multiple models.

### E. Weak labels
Use for noisy metadata-derived targets with confidence scores.

### F. Synthetic labels
Use only for simulator-generated data; mark clearly.

Every label record must track:
- `label_name`
- `label_value`
- `label_source_type`
- `label_source_id`
- `label_confidence`
- `label_notes`

If multiple annotators or multiple systems exist:
- compute agreement,
- identify disagreement hotspots,
- consider adjudication rules,
- preserve uncertainty instead of forcing false certainty.

---

## Predictions to Produce

The notebook must produce predictions at multiple levels.

### Cell-level predictions
- sperm probability,
- morphology class probabilities,
- defect subtype probabilities,
- uncertainty score.

### Track-level predictions
- motility state probability,
- progressive motility probability,
- kinematic estimates,
- track quality score.

### Sample-level predictions
- concentration estimate,
- total motility estimate,
- progressive motility estimate,
- morphology quality estimate,
- pass/review/reject class,
- fertility proxy estimate if labels exist,
- confidence / calibration score.

### Report-level outputs
For each sample, generate a compact summary:
- number of cells analyzed,
- number of tracks analyzed,
- predicted concentration,
- predicted total motility,
- predicted progressive motility,
- predicted abnormality rate,
- major defect profile,
- final quality class,
- reasons / top contributing factors.

---

## Baseline Tools and External References to Try First

Treat the following as useful starting points if accessible:
- public bovine morphology datasets on Roboflow Universe,
- supplementary bull fertility / CASA files on Figshare,
- OpenCASA on GitHub,
- ImageJ CASA plugin resources,
- VISEM / VISEM-Tracking only for transfer-learning or pipeline testing, not final bovine validation.

For each baseline tool or dataset:
- document what it provides,
- explain why it is used,
- state whether it is bovine or non-bovine,
- state whether it is used for final evaluation or only pretraining/benchmarking.

---

## Data Acquisition Heuristics

When searching online, prioritize:
1. bovine over non-bovine,
2. video over still images for motility tasks,
3. labeled over unlabeled,
4. sample-linked metadata over isolated images,
5. fertility-linked data over proxy-only data,
6. open license or clearly accessible download over vague references.

Mark each source with one of:
- `production_candidate`
- `prototype_candidate`
- `transfer_only`
- `reference_only`
- `reject`

---

## Recommended Modeling Order

Do not jump straight into end-to-end deep learning.

### Phase 1
- data audit
- rule-based / OpenCASA baseline
- simple detection baseline
- classical morphology features
- sample-level aggregation

### Phase 2
- CNN morphology classifier
- track extraction
- gradient boosting on track + morphology + metadata features

### Phase 3
- multimodal fusion
- calibrated sample scoring
- synthetic data ablations
- domain robustness checks

### Phase 4
- optional temporal deep models
- optional self-supervised learning
- optional learned generative augmentation

---

## Evaluation Design

At a minimum:
- one train split,
- one validation split,
- one untouched real test split.

Prefer split units in this order:
1. bull
2. ejaculate / sample
3. video
4. acquisition date
5. microscope or source domain

Never let:
- crops from the same source object,
- adjacent frames from the same short clip,
- synthetic derivatives of test items
cross between train and test.

Required analysis:
- performance by source,
- performance by class,
- performance by label confidence,
- calibration,
- confusion matrix,
- hardest false positives,
- hardest false negatives,
- robustness to domain shift.

---

## Error Analysis Instructions

Every model section must include:
- top successes,
- top failures,
- likely reasons,
- what labels or features are missing,
- whether failure is due to biology, imaging, preprocessing, or split leakage risk.

Build at least one curated table of:
- false positives,
- false negatives,
- uncertain predictions,
- out-of-domain cases.

---

## Synthetic Data Policy

Synthetic data is allowed, but only with discipline.

Use it for:
- rare defects,
- detector pretraining,
- track simulation,
- domain randomization,
- negative examples,
- robustness stress tests.

Do not use it as proof of real performance.

Required experiment table:
- real only,
- real + augmentation,
- real + rule-based synthetic,
- real + learned synthetic.

If synthetic data helps:
- state on which real holdout metric it helps,
- state by how much,
- state on which task,
- state the likely reason.

If it does not help:
- say so clearly.

---

## Notebook Output Requirements

By the end of execution, the notebook must produce:

### Files
- source catalog,
- download manifest,
- file inventory,
- audit report,
- label schema,
- mapping tables,
- processed manifests,
- engineered feature tables,
- track tables,
- prediction files,
- model comparison table,
- synthetic ablation table.

### Visuals
- source summary table,
- QC plots,
- sample image grids,
- track overlays,
- feature distributions,
- model performance plots,
- calibration plots,
- error examples.

### Narrative
- what data was actually found online,
- what was good enough to use,
- what labels were available,
- what targets were realistic,
- what worked,
- what did not,
- what data is still missing,
- what would be needed from a private AI center or reproduction lab.

---

## Minimal Deliverable Definition

The notebook is considered successful if it can do all of the following:
1. discover and download at least one bovine public dataset and one open-source benchmark tool,
2. organize the data reproducibly,
3. build a canonical schema,
4. generate at least one cell-level prepared dataset,
5. generate at least one sample-level feature table,
6. train at least one honest baseline model,
7. produce predictions on a real holdout set,
8. report limitations and next data needs.

---

## Stretch Goals

If time and data allow:
- compare classical and deep features,
- compare bovine-only vs bovine+transfer pretraining,
- build a sperm video simulator,
- test self-supervised representation learning,
- create a lightweight report generator for sample quality,
- benchmark OpenCASA outputs against the custom pipeline.

---

## Final Coordinator Instructions

At the end:
1. merge all agent outputs,
2. remove duplicate code,
3. ensure the notebook runs top to bottom,
4. ensure filenames and schemas are consistent,
5. add a final executive summary,
6. explicitly separate:
   - what is based on public data,
   - what is inferred,
   - what would require private lab data,
   - what is ready for prototyping,
   - what is not yet trustworthy for production.

Be comprehensive, explicit, and practical.
When in doubt, prefer a more detailed, auditable workflow over a magical black-box approach.


---

## Parallel Execution Plan

Use the dependency graph below to maximize parallel work.

### Wave 1 — Can start immediately in parallel
- Agent 1 — Data Discovery
- Agent 2 — Data Acquisition
- Agent 4 — Label Taxonomy and Annotation Strategy
- Agent 10 — Synthetic Data and Simulation design (design only, not final training)
- Coordinator Agent — notebook scaffold, config, and folder layout

### Wave 2 — Starts after first usable downloads exist
- Agent 3 — Data Audit and Quality Control
- Agent 5 — Computer Vision Data Preparation
- Agent 8 — Metadata, Process, and Tabular Feature Agent

### Wave 3 — Starts after prepared data exists
- Agent 6 — Motility, Tracking, and Kinematics
- Agent 7 — Morphology Feature Engineering
- Agent 9 — Modeling and Evaluation

### Wave 4 — Integration and ablations
- Coordinator Agent merges outputs
- Agent 9 runs final benchmark comparisons
- Agent 10 runs synthetic-data ablations against real holdout performance

### Merge rules
- all agents must read from shared config and manifests,
- no agent should invent a schema independently,
- the Coordinator owns:
  - canonical IDs,
  - split assignments,
  - path conventions,
  - label taxonomy,
  - final target definitions.

---

## Initial Public Source Shortlist to Check First

Treat these as initial high-priority leads, then expand outward.

### Bovine-first sources
1. Roboflow Universe — bovine sperm morphology project(s)
   - Search names like:
     - `Bovine sperm cells test`
     - `bull sperm morphology`
   - Expected use:
     - object detection / morphology prototype
   - Typical value:
     - fast prototype,
     - annotation format conversion,
     - initial CV pipeline.

2. Figshare supplementary files linked to bull fertility / CASA papers
   - Search patterns:
     - `bull fertility multivariate sperm figshare`
     - `bull semen CASA figshare`
   - Expected use:
     - tabular modeling,
     - sample-level features,
     - fertility-related exploratory analysis.

3. Any paper supplement or institutional repository containing:
   - sperm morphology images,
   - CASA export tables,
   - bull fertility supplementary data,
   - post-thaw semen quality tables.

### Open-source analysis baselines
4. OpenCASA
   - Use as:
     - reference baseline,
     - pseudo-label source,
     - motion/morphometry benchmark,
     - reproducibility check.

5. ImageJ CASA plugin resources
   - Use as:
     - transparent low-cost benchmark,
     - motion feature sanity check,
     - validation reference for video processing assumptions.

### Transfer-learning-only sources
6. VISEM / VISEM-Tracking
   - Use as:
     - tracking experiments,
     - detection pretraining,
     - self-supervised representation learning,
     - pipeline stress testing.
   - Do not use as final bovine performance proof.

7. Other public sperm datasets from Kaggle / Mendeley / Zenodo / GitHub
   - Use only if:
     - labels are clear,
     - download is reliable,
     - domain mismatch is documented.

---

## Concrete Online Search Procedure

When operating online, do not perform vague browsing. Use a structured procedure.

### Step 1 — Search by dataset repositories
Search each of:
- Roboflow Universe
- Figshare
- Kaggle
- Mendeley Data
- Zenodo
- GitHub
- Google Scholar / paper supplements / institutional repositories

### Step 2 — Search by species + modality + label
Use template queries:
- `bovine sperm microscopy dataset`
- `bull sperm video dataset`
- `bull sperm morphology abnormality dataset`
- `bull semen CASA dataset`
- `bovine sperm object detection dataset`
- `bull fertility sperm supplementary data`
- `post thaw bull semen dataset`
- `bovine semen motility tracking dataset`

### Step 3 — Search by tool + source code
Use template queries:
- `OpenCASA GitHub`
- `ImageJ CASA sperm plugin`
- `sperm motility analysis github`
- `sperm tracking dataset github`

### Step 4 — Search by paper + supplement
Use template queries:
- `bull fertility sperm supplementary`
- `bull semen figshare supplementary`
- `bovine sperm morphology YOLO`
- `multivariate analysis sperm bull fertility supplementary`

### Step 5 — Rank results using this priority score
Rank each candidate on:
- bovine relevance,
- presence of labels,
- presence of videos,
- presence of sample metadata,
- data accessibility,
- size,
- annotation quality,
- fitness for target tasks,
- legal usability.

---

## Notebook Engineering Rules

Even though the project stays inside one notebook, enforce project discipline.

### Required coding rules
- every section starts with a markdown cell stating purpose, inputs, and outputs,
- every major function gets a docstring,
- no hidden global state beyond config,
- cache expensive intermediate outputs to disk,
- all random seeds must be set,
- all paths must come from a central config block,
- all experiment names must be deterministic,
- all plots should include source / split / sample counts.

### Required engineering artifacts
- central `CONFIG` dictionary or dataclass,
- `PATHS` object,
- logger helper,
- reusable plotting helpers,
- manifest loader,
- schema validator,
- split validator,
- metric helpers,
- checkpoint save/load helpers.

### Recommended notebook execution pattern
- section headers,
- helper function cells,
- execution cells,
- audit output cells,
- assertions after critical transformations.

Use assertions for:
- no missing IDs in critical tables,
- split exclusivity,
- non-empty training data,
- label range checks,
- file existence checks.

---

## Canonical Split Strategy

The Coordinator must infer the best split unit from the data. Default policy:

1. if bull ID exists, split by bull;
2. else if ejaculate/sample ID exists, split by sample;
3. else if video ID exists, split by video;
4. else split by source file group and document the risk.

Also create:
- `split_reason`
- `split_group`
- `split_version`

No downstream agent may override the split without Coordinator approval.

---

## Minimum Tables to Build

At minimum, the notebook must create these tables.

### Source-level
- `sources_catalog`
- `downloads_manifest`
- `file_inventory`

### Visual-level
- `images_table`
- `videos_table`
- `frames_table`
- `detections_table`
- `crops_table`

### Biological object-level
- `cells_table`
- `tracks_table`

### Sample-level
- `samples_table`
- `sample_metadata_table`
- `sample_feature_table`

### Label-level
- `labels_long_table`
- `label_mapping_table`
- `annotation_agreement_table` if possible

### Prediction-level
- `cell_predictions`
- `track_predictions`
- `sample_predictions`

---

## Specific Label Confidence Policy

Every label should get a confidence tier:
- `gold` = expert human, high confidence
- `silver` = curated or consensus
- `bronze` = derived or weak
- `synthetic` = simulator generated
- `unknown` = provenance unclear

All evaluation tables must be stratified by confidence tier where possible.

---

## Suggested Target Definitions for the First Prototype

If data is sparse, prioritize these targets first.

### Priority 1
- sperm detection
- normal vs abnormal morphology
- total motility proxy
- progressive vs non-progressive motion proxy

### Priority 2
- morphology subtype classification
- concentration estimation
- sample-level quality class

### Priority 3
- fertility proxy or fertility prediction
- post-thaw outcome modeling
- domain-robust multimodal quality scoring

Do not force a fertility model unless genuine sample-level labels exist.

---

## What to Look For in Real Data

When reviewing any candidate dataset or supplement, explicitly check for:
- does it contain bovine samples?
- are the files images, videos, or tables?
- are there morphology labels?
- are there motion labels?
- are there concentration labels?
- are there sample IDs?
- are there bull IDs?
- are there repeated samples per bull?
- are there post-thaw measurements?
- are there field fertility or conception labels?
- are microscope settings available?
- is scale calibration available?
- is the download actually possible?
- is the dataset large enough to be useful?
- is the annotation consistent?
- is the source trustworthy?

Create a `usefulness_notes` field for each source.

---

## Pseudo-Code Coordination Outline

Use the following planning logic:

```python
# Coordinator outline
init_project()
build_folder_tree()
build_notebook_scaffold()

parallel_run([
    agent_data_discovery,
    agent_data_acquisition,
    agent_label_taxonomy,
    agent_synthetic_design
])

merge_source_catalogs()
merge_manifests()

parallel_run([
    agent_data_audit,
    agent_cv_preparation,
    agent_metadata_features
])

freeze_split_strategy()

parallel_run([
    agent_tracking_features,
    agent_morphology_features
])

run_modeling_baselines()
run_synthetic_ablations()
run_error_analysis()
assemble_final_report()
```

---

## Final Deliverable Standard

The final notebook should read like a serious research engineering artifact, not a messy scratchpad.

It must be suitable for:
- direct experimentation in Jupyter,
- later refactoring into a package,
- handoff to a technical cofounder, ML engineer, or research assistant,
- extension with private semen-station or lab data.

# AlertForge — Outcome-Aware Follow-Up Prioritization for LSST Alert Streams

## Problem

The Vera C. Rubin Observatory will generate ~10 million alerts per night (~10,000–100,000 actionable new transients after quality cuts). Existing alert brokers (Fink, ALeRCE, ANTARES, Lasair) classify these events using ML models and let astronomers define static SQL-like filters for selection.

**The gap:** No current system closes the feedback loop. Brokers classify but never learn whether follow-up was scientifically productive. Static filters:

- Do not adapt from follow-up outcomes
- Suppress unexpected or novel events by design
- Cannot estimate expected scientific return

## Hypothesis

An outcome-aware ranking model that continuously learns from follow-up results can:

1. Measurably improve follow-up efficiency over static filters (fewer wasted triggers)
2. Surface anomalous/novel events that static filters discard

## Architecture: Broker-Agnostic Downstream Layer

AlertForge does not replace existing brokers. It sits downstream and consumes their outputs:

```
LSST Alert Stream
       │
  ┌────┴─────┐
  │ Brokers  │  (Fink, ALeRCE, ANTARES, Lasair)
  │ classify │
  └────┬─────┘
       │  classifications, features, scores
       ▼
  ┌──────────────┐
  │  AlertForge  │  ranks by expected scientific return
  └──────┬───────┘
         │  ranked list (recommendation, not control)
         ▼
  ┌──────────────┐
  │  Follow-up   │  astronomer decides (AlertForge does not control this)
  │  Decision    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  Outcomes    │  scraped from public records (TNS, BTS catalog)
  └──────┬───────┘
         │  labels flow back to model
         ▼
  ┌──────────────┐
  │  Feedback    │  model retrains on outcome-labeled alerts
  │  Loop        │
  └──────────────┘
```

### How each stage works in practice

**Follow-up decision:** AlertForge does not control which alerts get followed up. It provides a ranked recommendation list. In Phase 1-2 we evaluate retroactively on historical data where astronomers already made decisions. In Phase 3 we simulate the selection loop by replaying the ZTF archive chronologically.

**Outcome collection:** We do not get outcomes from astronomers directly. We scrape public records:
- **TNS (Transient Name Server)** — when a transient is spectroscopically classified, it gets reported to TNS. We match reports back to alerts by coordinates + time.
- **BTS catalog** — already contains spectroscopic classifications for followed-up alerts.
- **Absence of report** — an alert never reported to TNS is a weak negative signal (could mean nobody looked, not that it was uninteresting).

**Scientific return measurement:** There is no universal "scientific value" metric. We define one using class-weighted rarity with multi-tier labels:
- **Class-weighted value** — assign scores by rarity. Rarer classes score higher because they represent greater discovery potential:
  - Kilonova, TDE, SLSN → high value
  - SN Ia, SN II → medium value
  - CV, known variable, artifact → low/zero value
  - Weights derived from class frequency in BTS (rarer = higher)
- **Multi-tier label structure** — not all labels are equal quality:
  - Tier 1: Spectroscopic classification (strongest signal, sparse — only followed-up alerts)
  - Tier 2: Photometric classification by brokers (weaker but abundant — available for most alerts)
  - Tier 3: No follow-up / no report (weak negative, propensity-corrected — absence of follow-up doesn't mean uninteresting)
- This multi-tier approach addresses the sparse outcome problem: we don't rely only on spectroscopic labels, which cover a tiny biased fraction of alerts.

## Continuous Learning Loop

| Phase | Data Source | Training Approach |
|---|---|---|
| **Cold start** | ZTF BTS historical outcomes + ELAsTiCC simulations | Pre-train ranking model on historical follow-up decisions and results |
| **Early operation** | Accumulating LSST follow-up outcomes | Fine-tune weekly from new labeled data |
| **Steady state** | Ongoing follow-up feedback | Incremental updates with exploration budget |

## Success Criteria

Measured against static-filter baselines on held-out ZTF BTS data. Specific numerical targets will be set after Phase 1 baseline measurement — we need to know how well static filters actually perform before defining what "better" means.

| Metric | Target | Measured against |
|---|---|---|
| **Precision@k** | Measurably outperform static filters | Held-out ZTF BTS data |
| **Rare-class recall** | Meaningful improvement over static filters | Known rare transients in ZTF archive (TDEs, kilonovae, SLSNe) |
| **Spectroscopic waste** | Fewer non-informative follow-ups | Simulated follow-up decisions on BTS |
| **Continuous improvement** | Measurable precision gain over simulated weeks | Chronological replay of ZTF archive |
| **Anomaly surfacing** | Surface known rare events that static filters missed | Retrospective on ZTF rare transient catalog |

## Ranking Signal: Expected Scientific Return

Each alert receives a composite score combining:

- **Classification confidence** — low confidence = potentially novel (upweight)
- **Context rarity** — unusual host galaxy, position, light curve morphology
- **Follow-up feasibility** — magnitude, visibility window, complementary data
- **Time-to-fade estimate** — fast-fading transients get urgency boost (the ranker learns this weighting from features, not hardcoded)
- **Historical outcome rate** — for similar alerts, what fraction yielded valuable science
- **Broker disagreement** — alerts where brokers disagree may be more interesting
- **Anomaly score** — reconstruction error or isolation score flags novel events
- **Classification information gain** — how much would following up this alert improve our classifier? (surfaces uncertain/novel events as a feature, not used as a label)

## Exploration Strategy

To avoid selection bias (only learning from what we already recommend):

- **Epsilon-greedy exploration** — reserve ~5–10% of follow-up budget for random/low-ranked alerts
- **Inverse propensity weighting** — correct for the bias in training data
- **Uncertainty sampling** — prioritize alerts where model is least certain
- **Replay buffer** — retain and re-sample rare class examples to prevent catastrophic forgetting

## Technical Challenges

| Challenge | Mitigation |
|---|---|
| **Selection bias** — training only on followed-up alerts | Exploration budget + counterfactual/off-policy methods (IPW, doubly-robust estimators) |
| **Sparse/slow feedback** — spectroscopy takes hours to days | Weekly retraining cadence; augment with photometric pseudo-labels |
| **Catastrophic forgetting** — rare classes seen early get forgotten | Replay buffers, elastic weight consolidation |
| **Class imbalance** — common transients vastly outnumber rare ones | Focal loss, oversampling rare classes, anomaly-aware objective |
| **Adoption** — astronomers want interpretable, controllable filters | Provide explanations per ranking (SHAP/feature attribution), allow user constraints |

## Datasets

| Dataset | Role | Access |
|---|---|---|
| **ZTF Bright Transient Survey (BTS)** | Primary training — contains follow-up decisions + spectroscopic outcomes | Public (Fremling et al. 2020) |
| **ELAsTiCC** | Benchmarking — simulated LSST alerts with ground truth including rare classes | Public (LSST DESC) |
| **PLAsTiCC** | Additional simulated light curves with labels | Public (Kaggle) |
| **ALeRCE broker outputs** | Classification probabilities, stamp classifier scores, light curve classifier scores | Public API (api.alerce.online) |
| **Fink alert archive** | Enriched ZTF alerts with science module outputs (SuperNNova, anomaly scores, cross-matches) | Public API (fink-portal.org) |
| **TNS (Transient Name Server)** | Confirmed post-follow-up classifications (Tier 1 labels) | Public API |
| **Open Supernova Catalog** | Historical supernovae with metadata | Public |

## Evaluation Metrics

| Metric | What it measures |
|---|---|
| **Precision@k** | Of top-k recommended alerts, how many had valuable follow-up outcomes |
| **Rare-class recall** | Fraction of genuinely novel/rare events surfaced in top rankings |
| **nDCG** | Overall ranking quality weighted by scientific value |
| **Follow-up efficiency** | Confirmed discoveries per follow-up trigger vs. static filter baseline |
| **Exploration coverage** | Diversity of event classes in recommendations over time |

## Implementation Phases

### Phase 1 — Baseline & Data Pipeline
- Ingest ZTF BTS data (alerts + spectroscopic outcomes)
- Cross-match with TNS for confirmed classifications (Tier 1 labels)
- Pull ALeRCE broker features (classification probabilities, stamp/LC classifier scores)
- Pull Fink alert history (science module outputs, anomaly scores, cross-matches)
- Build feature extraction pipeline:
  - Light curve features: rise rate, peak magnitude, decline rate, color, duration
  - Context features: galactic latitude, host galaxy offset, nearest source distance
  - Broker features: ALeRCE/Fink classification probabilities and scores
  - Temporal features: time since first detection, estimated time-to-fade
- Define follow-up outcome labels using multi-tier structure:
  - Tier 1: Spectroscopic classification from BTS/TNS (strongest, sparse)
  - Tier 2: Photometric classification from ALeRCE/Fink brokers (weaker, abundant)
  - Tier 3: No follow-up (weak negative, propensity-corrected)
  - Class-weighted value scores (rarer class = higher value, derived from BTS class frequencies)
  - Combined into single scalar training label per alert
- Implement static-filter baseline (replicate typical astronomer filter patterns from broker docs)
- Evaluate baseline precision@k and rare-class recall against success criteria

### Phase 2 — Ranking Model + Anomaly Detection
- Train a learning-to-rank model (LambdaMART or neural ranker) on historical BTS outcomes
- Add anomaly detection as a ranking feature from the start:
  - Isolation forest on feature vectors
  - Autoencoder on light curves (reconstruction error = anomaly score)
- Features include: broker classifications, light curve properties, host galaxy context, anomaly scores, time-to-fade estimate, broker disagreement
- Train/val/test split by time (chronological, not random) to simulate real deployment
- Evaluate against static-filter baseline on held-out BTS data
- Benchmark on ELAsTiCC with ground truth labels
- Retrospective: would the model have surfaced known rare ZTF transients?
- Validate against success criteria (precision@20, rare-class recall, waste reduction)

### Phase 3 — Continuous Learning Loop
- Implement feedback ingestion pipeline (outcome labels from TNS / spectroscopic reports)
- Add incremental retraining with replay buffer
- Implement exploration strategy (epsilon-greedy + uncertainty sampling)
- Add selection bias correction (inverse propensity weighting)
- Simulate multi-night operation on ZTF archive to measure adaptation over time
- Validate: does the model measurably improve over simulated weeks?

### Phase 4 — Interpretability & Deployment Interface
- Per-alert explanations (SHAP values, top contributing features)
- User constraint interface (astronomer can set hard filters + soft preferences)
- Cross-broker meta-ranking (combine outputs from multiple brokers)
- Dashboard for monitoring model drift and exploration coverage

## Key References

- Narayan et al. (2018) — ML-based brokers for LSST alert stream classification
- Fremling et al. (2020) — ZTF Bright Transient Survey (key outcome dataset)
- Möller & de Boissière (2020) — SuperNNova photometric SN classification
- Muthukrishna et al. (2019) — RAPID real-time transient classification
- Ishida et al. (2019) — Active learning for SN photometric classification (closest to feedback-loop idea)
- Lochner & Bassett (2021) — ASTRONOMALY anomaly detection for transients
- Malz et al. (2019) — PLAsTiCC results and photometric classification challenges
- Kessler et al. (2019) — PLAsTiCC models and lessons learned
- Sravan et al. (2020) — Real-time follow-up prioritization
- ELAsTiCC (2023) — Extended LSST Astronomical Time-series Classification Challenge
- Ishida et al. (2019b) — Active learning for optimizing spectroscopic follow-up (arXiv:1804.03765)
- Ishida et al. (2019c) — Optimizing spectroscopic follow-up strategies (MNRAS 483, 2)
- Aleo et al. (2024) — Classifier-based multi-class anomaly detection for transients (arXiv:2403.14742)

## What Makes This Novel

Individual components exist in the literature — anomaly detection for transients (Lochner & Bassett 2021, Aleo et al. 2024), active learning for follow-up optimization (Ishida et al. 2019), broker classification pipelines (ALeRCE, Fink). AlertForge's contribution is the combination at scale:

1. **Continual outcome-ranking** — not a one-off classifier but a system that retrains from follow-up results over time. Existing active learning work (Ishida et al.) retrains classifiers but doesn't rank by scientific return.
2. **Broker-agnostic aggregation** — consumes outputs from any broker as features, rather than competing with broker classifiers. No existing system combines broker outputs into a unified ranking.
3. **Multi-tier label framework** — addresses the sparse/biased outcome problem by combining spectroscopic labels (sparse), photometric classifications (abundant), and propensity-corrected negatives. Existing work typically uses only one label tier.
4. **Anomaly as a ranking feature, not the goal** — anomaly detection exists, but nobody integrates anomaly scores into an outcome-aware ranker. AlertForge uses novelty as one input to expected scientific return, not as the end product.
5. **Selection bias awareness** — explicitly models and corrects for the bias introduced by the current follow-up policy, using IPW and exploration budgets.

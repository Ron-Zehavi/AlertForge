# AlertForge — Outcome-Aware Follow-Up Prioritization for LSST Alert Streams

## Problem

The Vera C. Rubin Observatory will generate ~10 million alerts per night (~10,000–100,000 actionable new transients after quality cuts). Existing alert brokers (Fink, ALeRCE, ANTARES, Lasair) classify these events using ML models and let astronomers define static SQL-like filters for selection.

**The gap:** No current system closes the feedback loop. Brokers classify but never learn whether follow-up was scientifically productive. Static filters:

- Do not adapt from follow-up outcomes
- Suppress unexpected or novel events by design
- Cannot estimate expected scientific return

## Hypothesis

An outcome-aware ranking model that continuously learns from follow-up results can:

1. Improve follow-up efficiency by 10–30% (fewer wasted triggers)
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
         │  ranked list
         ▼
  ┌──────────────┐
  │  Follow-up   │  astronomer selects top-k
  │  Decision    │
  └──────┬───────┘
         │  outcome (spectrum, classification, null)
         ▼
  ┌──────────────┐
  │  Feedback    │  labels flow back to model
  │  Loop        │
  └──────────────┘
```

## Continuous Learning Loop

| Phase | Data Source | Training Approach |
|---|---|---|
| **Cold start** | ZTF BTS historical outcomes + ELAsTiCC simulations | Pre-train ranking model on historical follow-up decisions and results |
| **Early operation** | Accumulating LSST follow-up outcomes | Fine-tune weekly from new labeled data |
| **Steady state** | Ongoing follow-up feedback | Incremental updates with exploration budget |

## Ranking Signal: Expected Scientific Return

Each alert receives a composite score combining:

- **Classification confidence** — low confidence = potentially novel (upweight)
- **Context rarity** — unusual host galaxy, position, light curve morphology
- **Follow-up feasibility** — magnitude, visibility window, complementary data
- **Historical outcome rate** — for similar alerts, what fraction yielded valuable science
- **Broker disagreement** — alerts where brokers disagree may be more interesting

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
| **ZTF alert archive / ALeRCE** | Feature extraction, broker classification outputs | Public API |
| **Fink alert archive** | Enriched ZTF alerts with Fink science module outputs | Public API |
| **TNS (Transient Name Server)** | Confirmed post-follow-up classifications | Public API |
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
- Build feature extraction pipeline (light curve features, context features, broker scores)
- Implement static-filter baseline (replicate typical astronomer filters)
- Evaluate baseline precision@k and rare-class recall

### Phase 2 — Static Ranking Model
- Train a learning-to-rank model (LambdaMART or neural ranker) on historical BTS outcomes
- Features: broker classifications, light curve properties, host galaxy context, positional info
- Evaluate against static-filter baseline on held-out BTS data
- Benchmark on ELAsTiCC with ground truth labels

### Phase 3 — Continuous Learning Loop
- Implement feedback ingestion pipeline (outcome labels from TNS / spectroscopic reports)
- Add incremental retraining with replay buffer
- Implement exploration strategy (epsilon-greedy + uncertainty sampling)
- Add selection bias correction (inverse propensity weighting)
- Simulate multi-night operation on ZTF archive to measure adaptation over time

### Phase 4 — Anomaly-Aware Ranking
- Add anomaly detection component (isolation forest, autoencoder on light curves)
- Integrate anomaly score into ranking — novel events get boosted
- Evaluate: does the system surface events that static filters would have missed?
- Case study: identify known rare transients in ZTF archive that were initially missed

### Phase 5 — Interpretability & Deployment Interface
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

## What Makes This Novel

1. **Closed feedback loop** — no existing broker learns from follow-up outcomes
2. **Ranking by scientific return** — not just classification, but expected value of follow-up
3. **Continuous adaptation** — model improves weekly as outcomes accumulate
4. **Anomaly-aware** — explicitly boosts novel events that static filters suppress
5. **Broker-agnostic** — works downstream of any broker, can combine multiple broker outputs
6. **Selection bias awareness** — addresses the fundamental statistical challenge head-on

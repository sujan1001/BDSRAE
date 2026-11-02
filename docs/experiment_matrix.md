# Experiment matrix

| ID | Retrieval | Encoder | Mitigation | Primary evidence |
|---|---|---|---|---|
| E0 | BM25 | lexical | none | lexical baseline by language |
| E1 | Dense | LaBSE | none | cross-lingual dense baseline |
| E2 | Dense | multilingual-e5-base | none | cross-lingual dense baseline |
| E3 | Hybrid | BM25 + best dense | none | quality-cost trade-off |
| E4 | Dense | best dense | translate-to-English query | translation gain and cost |
| E5 | Dense | Indic encoder | multilingual fine-tuning pilot | quality and fairness gain |
| E6 | Hybrid | best dense | metadata / lexical blend | robustness and latency |
| E7 | Best cost | selected | selected mitigation | final recommendation |

## Metrics

- Retrieval: Recall@1, Recall@5, Recall@10, MRR and nDCG@10.
- Answer quality: exact answer-key match for the smoke test; human/bilingual rubric for final runs.
- Fairness: maximum minus minimum language mean for each metric, with 95% confidence intervals.
- Systems: documents processed, partition count, throughput, elapsed time, storage/index bytes, peak memory and query latency.
- Cost: CPU/GPU hours, translation calls/tokens, model size and storage footprint.

The smoke runner exposes E0-E6 as deterministic or optional pilots. It must not be treated as final evidence until the planned public datasets and locked experiment protocol are used.


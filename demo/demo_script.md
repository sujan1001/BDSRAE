# Three-minute demo script

## 0:00-0:25 - Problem

“This project tests whether the same public-service retrieval task works comparably in English, Malayalam and Hindi. We measure language gaps rather than relying on a single average score.”

## 0:25-0:55 - Reproducibility

Run:

```bash
python scripts/run_pipeline.py --config configs/smoke.json
```

Show the generated manifest and point out that the smoke data is synthetic, offline and contains no personal data.

## 0:55-1:35 - Retrieval comparison

Open `metrics.csv`. Explain the BM25, optional dense, hybrid, translation and alignment-pilot rows. Show that every query has a language, gold document, rank and answer-quality result.

## 1:35-2:10 - Fairness and systems evidence

Open `fairness_summary.json` and show the per-language means, 95% intervals and max-minus-min gaps. Open `system_metrics.json` and show scale points, partition count, storage bytes and throughput. Explain that the Spark runner is available for the distributed run.

## 2:10-2:40 - Governance

Show `data/source_registry.csv`, `cards/data_card.md` and `cards/model_card.md`. Call out license verification, Malayalam coverage checks, model fallback logging, and the no-real-personal-data rule.

## 2:40-3:00 - Close

“The smoke pipeline proves the reproducible path. Phase-II will replace the synthetic fixture with verified public data, run the locked experiment matrix at scale, conduct bilingual answer review, and report quality gains together with cost and fairness changes.”


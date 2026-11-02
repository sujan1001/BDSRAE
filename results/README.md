# Results directory

Generated result folders are ignored by Git to avoid committing machine-specific outputs. Run:

```bash
python scripts/run_pipeline.py --config configs/smoke.json
```

The smoke run writes `metrics.csv`, `fairness_summary.json`, `system_metrics.json`, and `run_manifest.json` under `results/smoke/`.


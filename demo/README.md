# Demo

`demo_video.avi` is a dependency-light, three-minute visual companion built from the synthetic smoke fixture. It is intentionally silent and pairs with `demo_script.md` for narration; it does not record a user's screen, voice or personal data.

To rebuild it offline:

```text
python scripts/build_demo_video.py
```

The demo is intentionally scripted so it can be recorded in approximately three minutes without exposing private data or requiring a live external service.

1. Show the repository and run the smoke command.
2. Open `results/smoke/fairness_summary.json` and point out English, Hindi and Malayalam rows and the gap calculation.
3. Open `results/smoke/system_metrics.json` and point out scale points, partitions, storage bytes and throughput.
4. Compare BM25, dense fallback, hybrid, translation and alignment-pilot experiment IDs.
5. Show the source registry, data card and model card.
6. Close with the limitation: smoke results are not final benchmark evidence; the Phase-II public-data run must be executed before making performance claims.


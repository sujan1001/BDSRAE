# Data card: Multilingual Retrieval Fairness

## Summary

The repository includes a small synthetic parallel public-service document set in English, Hindi and Malayalam for offline smoke testing. It contains no real personal data and no copied external text.

## Motivation and intended use

The synthetic set tests that the pipeline can preserve language labels, align equivalent information needs, compute retrieval metrics, and produce language-wise fairness summaries. It is not intended to estimate real-world public-service performance.

## Composition

- 9 documents: 3 topics x 3 languages.
- 9 queries: one per document.
- Topics: senior pension, water-supply complaint, public-safety emergency.
- Each row has a language, topic ID, answer key and gold document ID.

## Source and license

The smoke data is generated for this project and is treated as project-created synthetic data. It is included for reproducibility. External suggested resources are recorded in `data/source_registry.csv` but are not downloaded automatically.

## Privacy and safety

No names, addresses, phone numbers, account numbers or real cases are included. The examples are generic public-service instructions. Do not add real user queries or personal data to this repository.

## Known limitations

- Tiny topic and query coverage.
- Synthetic language may not represent natural variation, dialects or code-switching.
- Exact answer-key match is only a smoke-test metric.
- The set cannot support claims about production fairness or user harm.

## Expansion protocol

Before adding external data, record the exact release, license, source attribution, language coverage, access date, preprocessing and exclusion rules. Keep external raw data out of Git unless redistribution rights are explicit.


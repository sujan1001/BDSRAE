# Model card: Multilingual Retrieval Fairness baselines

## Models and code

The pipeline supports:

- BM25 lexical retrieval.
- A deterministic local hashing encoder for offline smoke tests.
- Optional SentenceTransformers models such as LaBSE and multilingual-e5-base.
- Reciprocal-rank-fusion hybrid retrieval.
- Translation and alignment-feature mitigation pilots.

When optional transformer packages or model weights are unavailable, the pipeline uses a deterministic hashing fallback and records `encoder_requested`, `encoder_used` and `encoder_error` in `run_manifest.json`. Fallback output must not be reported as transformer output.

## Intended use

Benchmarking retrieval quality and language-wise gaps on public or synthetic document sets. The project is not a production public-services assistant and should not be used to make eligibility, emergency, legal or financial decisions.

## Evaluation

The runner reports Recall@1/5/10, MRR, nDCG@10, answer quality, language gaps, confidence intervals, latency, storage and scale-sweep evidence. Final model selection must use the locked public-data protocol, not only the smoke test.

## Responsible-AI risks

- Lower scores can reflect corpus coverage, tokenizer behavior, query translation, or annotation quality rather than a single model defect.
- Answer-key exact match can undercount valid paraphrases and overcount templated matches.
- Malayalam coverage must be independently supported; MIRACL is not assumed to provide it.
- Translation can alter meaning and introduce cost or safety failures.
- Dense models may encode stereotypes or unsafe associations from their pretraining data.

## Human oversight

For final answer-quality evaluation, use bilingual review for a stratified sample, publish the rubric and agreement statistics, and preserve unresolved cases as limitations.


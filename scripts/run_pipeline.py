"""Run the reproducible multilingual retrieval fairness evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrfairness.data import read_jsonl, validate_parallel_set  # noqa: E402
from mrfairness.metrics import summarise  # noqa: E402
from mrfairness.retrieval import (  # noqa: E402
    BM25,
    HashingEncoder,
    OptionalSentenceTransformer,
    dense_rank,
    ranking_metrics,
    reciprocal_rank_fusion,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/smoke.json")
    parser.add_argument("--input", default=None, help="Override document JSONL path")
    parser.add_argument("--queries", default=None, help="Override query JSONL path")
    parser.add_argument("--output", default=None, help="Override result directory")
    parser.add_argument("--spark", action="store_true", help="Attempt an optional Spark probe")
    return parser.parse_args()


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def make_encoder(spec: dict):
    backend = spec.get("backend", "hashing")
    if backend == "hashing":
        return HashingEncoder(int(spec.get("dimensions", 256)), salt=spec.get("salt", spec["id"])), spec["id"], None
    if backend == "sentence_transformers":
        encoder = OptionalSentenceTransformer(spec["model_name"], int(spec.get("fallback_dimensions", 256)))
        error = getattr(encoder, "load_error", None)
        return encoder, getattr(encoder, "actual_model", "unknown"), error
    raise ValueError(f"Unknown encoder backend: {backend}")


def query_text(query: dict, mitigation: str) -> str:
    if mitigation == "translation":
        return query.get("pivot_query", query["text"])
    if mitigation == "alignment_pilot":
        return f"{query['text']} topic_{query['topic_id']}"
    return query["text"]


def candidate_documents(documents: list[dict], query: dict, cross_language: bool) -> list[dict]:
    if cross_language:
        return documents
    return [document for document in documents if document["language"] == query["language"]]


def evaluate_experiment(documents: list[dict], queries: list[dict], experiment: dict, cross_language: bool) -> tuple[list[dict], dict]:
    model_spec = experiment["model"]
    encoder, encoder_used, encoder_error = make_encoder(model_spec)
    rows: list[dict] = []
    for query in queries:
        candidates = candidate_documents(documents, query, cross_language)
        texts = [document["text"] for document in candidates]
        query_value = query_text(query, experiment.get("mitigation", "none"))
        if experiment["method"] == "bm25":
            ranking = BM25(texts).rank(query_value)
        elif experiment["method"] == "dense":
            ranking = dense_rank(query_value, texts, encoder)
        elif experiment["method"] == "hybrid":
            ranking = reciprocal_rank_fusion([BM25(texts).rank(query_value), dense_rank(query_value, texts, encoder)])
        else:
            raise ValueError(f"Unknown retrieval method: {experiment['method']}")
        gold_index = next((index for index, document in enumerate(candidates) if document["doc_id"] == query["gold_doc_id"]), None)
        if gold_index is None:
            raise ValueError(f"Gold document {query['gold_doc_id']} is not in the candidate set for {query['query_id']}")
        metric_values = ranking_metrics(ranking, gold_index)
        top_index = ranking[0][0] if ranking else None
        top_document = candidates[top_index] if top_index is not None else None
        rows.append({
            "experiment_id": experiment["id"],
            "experiment_label": experiment["label"],
            "language": query["language"],
            "query_id": query["query_id"],
            "topic_id": query["topic_id"],
            "gold_doc_id": query["gold_doc_id"],
            "encoder_requested": model_spec.get("id"),
            "encoder_used": encoder_used,
            "mitigation": experiment.get("mitigation", "none"),
            "method": experiment["method"],
            "answer_quality": int(top_document is not None and top_document.get("answer_key") == query.get("answer_key")),
            **metric_values,
        })
    metadata = {"encoder_requested": model_spec.get("id"), "encoder_used": encoder_used, "encoder_error": encoder_error}
    return rows, metadata


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_scale_sweep(documents: list[dict], scale_points: list[int], partitions: int) -> list[dict]:
    rows = []
    for requested_size in scale_points:
        replicated = [documents[index % len(documents)] for index in range(requested_size)]
        start = time.perf_counter()
        bytes_count = sum(len(json.dumps(row, ensure_ascii=False).encode("utf-8")) for row in replicated)
        _index = BM25([row["text"] for row in replicated])
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        rows.append({
            "engine": "python-local",
            "rows": requested_size,
            "partitions": min(partitions, max(1, requested_size)),
            "storage_bytes": bytes_count,
            "elapsed_ms": round(elapsed_ms, 3),
            "throughput_rows_per_second": round(requested_size / max(elapsed_ms / 1000.0, 1e-9), 2),
        })
    return rows


def spark_probe() -> dict:
    try:
        import pyspark  # type: ignore

        return {"available": True, "version": getattr(pyspark, "__version__", "unknown"), "status": "not_started"}
    except Exception as exc:
        return {"available": False, "status": "optional_dependency_missing", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    args = parse_args()
    config_path = (ROOT / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)
    document_path = (ROOT / (args.input or config["data"]["documents"])).resolve()
    query_path = (ROOT / (args.queries or config["data"]["queries"])).resolve()
    output_dir = (ROOT / (args.output or config["output_dir"])).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    documents = read_jsonl(document_path)
    queries = read_jsonl(query_path)
    validation = validate_parallel_set(documents, queries)
    if not validation["valid"]:
        raise ValueError(f"Parallel data validation failed: {validation}")

    all_rows: list[dict] = []
    experiment_metadata = []
    for experiment in config["experiments"]:
        rows, metadata = evaluate_experiment(documents, queries, experiment, config["evaluation"].get("cross_language", False))
        all_rows.extend(rows)
        experiment_metadata.append({"experiment_id": experiment["id"], **metadata})

    write_csv(output_dir / "metrics.csv", all_rows)
    summaries = {}
    for experiment_id in sorted({row["experiment_id"] for row in all_rows}):
        summaries[experiment_id] = summarise([row for row in all_rows if row["experiment_id"] == experiment_id])
    (output_dir / "fairness_summary.json").write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    scale_rows = run_scale_sweep(documents, config["systems"]["scale_points"], config["systems"]["partitions"])
    (output_dir / "system_metrics.json").write_text(json.dumps({"scale_sweep": scale_rows, "spark": spark_probe() if args.spark else {"status": "not_requested"}}, indent=2), encoding="utf-8")
    manifest = {
        "run_started_utc": datetime.now(timezone.utc).isoformat(),
        "project": "Multilingual Retrieval Fairness",
        "run_scope": config.get("run_scope", "smoke_test"),
        "documents": str(document_path.relative_to(ROOT)),
        "queries": str(query_path.relative_to(ROOT)),
        "data_validation": validation,
        "experiments": experiment_metadata,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": git_commit(),
        "responsible_ai": {
            "personal_data_used": False,
            "source_type": "synthetic_public-service_parallel_documents",
            "coverage_note": "MIRACL is not used as the smoke-test source; external dataset integrations require a separate licence and coverage audit.",
        },
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "rows": len(all_rows), "experiments": len(config["experiments"]), "languages": validation["languages"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


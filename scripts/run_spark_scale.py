"""Optional Spark scale evidence runner.

This script is intentionally separate from the smoke pipeline so the project can
run offline without downloading Spark. Use the full requirements in Docker or a
cluster environment for the distributed-processing evidence section.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_parallel_documents.jsonl")
    parser.add_argument("--output", default="results/spark_scale.json")
    parser.add_argument("--partitions", type=int, default=4)
    args = parser.parse_args()
    try:
        from pyspark.sql import SparkSession
    except Exception as exc:
        payload = {"status": "not_run", "reason": f"pyspark unavailable: {type(exc).__name__}: {exc}"}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0

    spark = SparkSession.builder.master("local[*]").appName("multilingual-retrieval-fairness").getOrCreate()
    started = time.perf_counter()
    frame = spark.read.json(args.input).repartition(args.partitions)
    count = frame.count()
    by_language = {row["language"]: row["count"] for row in frame.groupBy("language").count().collect()}
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    payload = {"status": "pass", "rows": count, "partitions": frame.rdd.getNumPartitions(), "by_language": by_language, "elapsed_ms": round(elapsed_ms, 3)}
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    spark.stop()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


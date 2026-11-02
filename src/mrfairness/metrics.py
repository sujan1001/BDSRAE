"""Fairness, confidence interval and cost summaries."""

from __future__ import annotations

import math
from collections import defaultdict


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def confidence_interval(values: list[float]) -> list[float]:
    if not values:
        return [0.0, 0.0]
    average = mean(values)
    if len(values) < 2:
        return [average, average]
    variance = sum((value - average) ** 2 for value in values) / (len(values) - 1)
    margin = 1.96 * math.sqrt(variance / len(values))
    return [average - margin, average + margin]


def summarise(rows: list[dict]) -> dict:
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["language"]].append(row)
    languages = sorted(grouped)
    language_metrics = {}
    for language in languages:
        language_rows = grouped[language]
        language_metrics[language] = {}
        for metric in ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10", "answer_quality"):
            values = [float(row[metric]) for row in language_rows]
            language_metrics[language][metric] = {
                "mean": mean(values),
                "ci95": confidence_interval(values),
                "n": len(values),
            }
    gaps = {}
    for metric in ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10", "answer_quality"):
        values = [language_metrics[language][metric]["mean"] for language in languages]
        gaps[metric] = max(values) - min(values) if values else 0.0
    return {"languages": languages, "language_metrics": language_metrics, "gap_max_minus_min": gaps}


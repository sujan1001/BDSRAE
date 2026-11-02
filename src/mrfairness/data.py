"""Data loading and provenance helpers for public or synthetic data only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def normalize_text(text: str) -> str:
    return " ".join(str(text).strip().split())


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(normalize_text(text))]


def read_jsonl(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def validate_parallel_set(documents: list[dict], queries: list[dict]) -> dict:
    languages = sorted({row["language"] for row in documents})
    document_ids = {row["doc_id"] for row in documents}
    missing = [row["gold_doc_id"] for row in queries if row["gold_doc_id"] not in document_ids]
    return {
        "document_count": len(documents),
        "query_count": len(queries),
        "languages": languages,
        "missing_gold_documents": sorted(set(missing)),
        "language_query_counts": {
            language: sum(1 for row in queries if row["language"] == language)
            for language in languages
        },
        "valid": not missing and len(languages) >= 3,
    }


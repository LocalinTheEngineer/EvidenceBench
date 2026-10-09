"""Independent indexing and search for one corpus variant."""
from __future__ import annotations

import hashlib
import json
import platform
import statistics
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .adapters.bm25 import BM25Retriever
from .chunking import chunks_for_corpus
from .corpus import CorpusError, load_corpus
from .metrics import aggregate, score_question


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def run(corpus: Path, out: Path, split: str = "dev", include_draft: bool = False,
        smoke: bool = False, retriever_name: str = "bm25") -> dict:
    if retriever_name != "bm25":
        raise CorpusError(f"unavailable retriever: {retriever_name}")
    manifest, symbols, questions = load_corpus(corpus)
    if split not in {"dev", "test"}:
        raise CorpusError("split must be dev or test")
    selected = [q for q in questions if q.split == split]
    scored = [q for q in selected if q.review_status == "reviewed" or include_draft or smoke]
    chunks = chunks_for_corpus(corpus, manifest, symbols)
    before = time.perf_counter()
    retrievers = {}
    for repo_id in {q.repo_id for q in selected}:
        retriever = BM25Retriever()
        retriever.index([chunk for chunk in chunks if chunk.path.startswith(f"repos/{repo_id}/")])
        retrievers[repo_id] = retriever
    index_ms = (time.perf_counter() - before) * 1000
    rows = []
    search_ms = []
    for question in selected:
        before = time.perf_counter()
        retriever = retrievers[question.repo_id]
        hits = retriever.search(question.text, max(5, len(retriever.chunks)))
        search_ms.append((time.perf_counter() - before) * 1000)
        score = score_question(question, hits) if question in scored else None
        rows.append({"question_id": question.question_id, "repo_id": question.repo_id,
                     "text": question.text, "review_status": question.review_status,
                     "answerable": question.answerable, "relevant_symbols": list(question.relevant_symbols),
                     "ranked": [asdict(hit) for hit in hits], "metrics": score})
    scored_rows = [row["metrics"] for row in rows if row["metrics"] is not None]
    label_data = [asdict(q) for q in selected]
    config = {"retriever": retriever_name, "split": split, "k_values": [1, 3, 5],
              "include_draft": include_draft, "smoke": smoke}
    label_hash = hashlib.sha256(canonical_json(label_data)).hexdigest()
    config_hash = hashlib.sha256(canonical_json(config)).hexdigest()
    summary = aggregate(scored, scored_rows)
    result = {
        "schema_version": 1, "variant_id": manifest["variant_id"],
        "corpus_mode": "smoke" if smoke else "evaluation",
        "score_label": "synthetic smoke" if smoke else ("unreviewed exploratory" if include_draft else "reviewed evaluation"),
        "labels_hash": label_hash, "config_hash": config_hash, "config": config,
        "question_count": len(selected), "scored_question_count": len(scored),
        "summary": summary, "rows": rows,
        "performance": {"index_ms": index_ms,
                        "search_p50_ms": statistics.median(search_ms) if search_ms else None,
                        "search_p95_ms": sorted(search_ms)[min(len(search_ms) - 1, int(len(search_ms) * .95))] if search_ms else None,
                        "query_count": len(selected), "chunk_count": len(chunks),
                        "source_bytes": sum((corpus / path).stat().st_size for path in {s.path for s in symbols}),
                        "python": sys.version.split()[0], "os": platform.platform(),
                        "warmup": 0, "repeats": 1, "cache": "none"},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "run.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

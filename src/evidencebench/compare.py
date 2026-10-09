"""Paired variant comparison and opt-in regression gate."""
from __future__ import annotations

import json
from pathlib import Path

from .corpus import CorpusError
from .reports.html import render_comparison


def compare(base_file: Path, mutant_file: Path, out: Path, max_drop: float | None = None,
            min_reviewed: int = 10, allowed_invalid_citations: int = 0,
            citations_file: Path | None = None) -> dict:
    base = json.loads((base_file / "run.json").read_text(encoding="utf-8"))
    mutant = json.loads((mutant_file / "run.json").read_text(encoding="utf-8"))
    if base.get("schema_version") != 1 or mutant.get("schema_version") != 1:
        raise CorpusError("unsupported run schema_version")
    if base.get("labels_hash") != mutant.get("labels_hash") or base.get("config_hash") != mutant.get("config_hash"):
        raise CorpusError("comparison labels/config mismatch")
    if base.get("question_count") != mutant.get("question_count"):
        raise CorpusError("comparison question count mismatch")
    by_id = {row["question_id"]: row for row in mutant["rows"]}
    if set(by_id) != {row["question_id"] for row in base["rows"]}:
        raise CorpusError("comparison question IDs mismatch")
    rows = []
    for old in base["rows"]:
        new = by_id[old["question_id"]]
        old_rank = old["metrics"]["first_relevant_rank"] if old["metrics"] else None
        new_rank = new["metrics"]["first_relevant_rank"] if new["metrics"] else None
        old_paths = {hit["canonical_id"]: hit["path"] for hit in old["ranked"] if hit["canonical_id"]}
        new_paths = {hit["canonical_id"]: hit["path"] for hit in new["ranked"] if hit["canonical_id"]}
        rows.append({"question_id": old["question_id"], "text": old["text"],
                     "base_rank": old_rank, "mutant_rank": new_rank,
                     "rank_delta": old_rank - new_rank if old_rank and new_rank else None,
                     "canonical_paths": {symbol: {"base": old_paths.get(symbol),
                                                   "mutant": new_paths.get(symbol)}
                                         for symbol in old["relevant_symbols"]},
                     "failure_category": new["metrics"]["failure_category"] if new["metrics"] else None})
    delta = None
    if base["summary"] is not None and mutant["summary"] is not None:
        delta = mutant["summary"]["macro_recall"]["@1"] - base["summary"]["macro_recall"]["@1"]
    gate = None
    if max_drop is not None:
        if max_drop < 0 or min_reviewed < 1 or allowed_invalid_citations < 0:
            raise CorpusError("invalid gate configuration")
        if base["score_label"] != "reviewed evaluation" or mutant["score_label"] != "reviewed evaluation":
            raise CorpusError("regression gate requires reviewed evaluation labels")
        reviewed = base["scored_question_count"]
        if reviewed < min_reviewed:
            gate = {"passed": False, "reason": "insufficient_reviewed_questions", "reviewed_count": reviewed}
        else:
            invalid = None
            if citations_file:
                citations = json.loads(citations_file.read_text(encoding="utf-8"))
                if citations.get("variant_id") != mutant["variant_id"]:
                    raise CorpusError("citation report variant mismatch")
                invalid = citations["structural_invalid_count"]
            passed = delta is not None and delta >= -max_drop and (invalid is None or invalid <= allowed_invalid_citations)
            gate = {"passed": passed, "reason": "within_limits" if passed else "regression_or_invalid_citations",
                    "reviewed_count": reviewed, "recall_at_1_drop": -delta if delta is not None else None,
                    "structural_invalid_citations": invalid}
    report = {"schema_version": 1, "base_variant_id": base["variant_id"],
              "mutant_variant_id": mutant["variant_id"], "score_label": base["score_label"],
              "labels_hash": base["labels_hash"], "config_hash": base["config_hash"],
              "base_summary": base["summary"], "mutant_summary": mutant["summary"],
              "recall_at_1_delta": delta, "gate": gate, "rows": rows}
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "index.html").write_text(render_comparison(report), encoding="utf-8")
    return report

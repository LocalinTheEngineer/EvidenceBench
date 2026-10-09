"""Structural, exact-content, and gold-span citation checks."""
from __future__ import annotations

import json
from pathlib import Path

from .corpus import CorpusError, load_corpus, safe_source


def normalize_newlines(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def validate_citations(input_file: Path, corpus: Path, out: Path) -> dict:
    manifest, symbols, questions = load_corpus(corpus)
    by_question = {q.question_id: q for q in questions}
    by_symbol = {s.canonical_id: s for s in symbols}
    rows = []
    for number, line in enumerate(input_file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            citation = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CorpusError(f"invalid citation JSON at line {number}") from exc
        if citation.get("question_id") not in by_question:
            raise CorpusError(f"unknown citation question at line {number}")
        if citation.get("variant_id") != manifest["variant_id"]:
            raise CorpusError(f"citation variant mismatch at line {number}")
        path = citation.get("path")
        start = citation.get("start_line")
        end = citation.get("end_line")
        structural = False
        content_valid = None
        relevant = False
        precision = 0.0
        reason = None
        if not isinstance(path, str) or type(start) is not int or type(end) is not int or start < 1 or end < start:
            reason = "invalid_path_or_span"
        else:
            try:
                source = safe_source(corpus, path).read_text(encoding="utf-8")
                lines = normalize_newlines(source).splitlines(keepends=True)
                if end > len(lines):
                    reason = "span_past_eof"
                else:
                    structural = True
                    span = "".join(lines[start - 1:end])
                    if "quoted_excerpt" in citation:
                        excerpt = citation["quoted_excerpt"]
                        content_valid = isinstance(excerpt, str) and bool(excerpt) and normalize_newlines(excerpt) == span
                    question = by_question[citation["question_id"]]
                    covered = set()
                    for symbol_id in question.relevant_symbols:
                        symbol = by_symbol[symbol_id]
                        if symbol.path == path:
                            covered.update(range(max(start, symbol.start_line), min(end, symbol.end_line) + 1))
                    relevant = bool(covered)
                    precision = len(covered) / (end - start + 1)
            except CorpusError:
                reason = "missing_or_unsafe_path"
        rows.append({"question_id": citation["question_id"], "variant_id": citation["variant_id"],
                     "path": path, "start_line": start, "end_line": end,
                     "structural_valid": structural, "content_valid": content_valid,
                     "relevance_valid": relevant, "span_precision": precision, "reason": reason})
    result = {"schema_version": 1, "variant_id": manifest["variant_id"],
              "citation_count": len(rows),
              "structural_invalid_count": sum(not row["structural_valid"] for row in rows),
              "rows": rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result

"""One-command authored smoke demonstration."""
from __future__ import annotations

import json
from pathlib import Path

from .citations import validate_citations
from .compare import compare
from .corpus import CorpusError, load_corpus
from .mutations import mutate
from .runner import run


def demo(out: Path) -> dict:
    if out.exists() and any(out.iterdir()):
        raise CorpusError("demo output directory must be empty")
    corpus = Path(__file__).resolve().parents[2] / "corpus" / "smoke"
    out.mkdir(parents=True, exist_ok=True)
    base = run(corpus, out / "base", smoke=True)
    reports = {}
    for kind in ("move_file", "prefix_comments", "add_distractor"):
        variant_dir = out / "variants" / kind
        mutate(corpus, kind, 42, variant_dir)
        mutant = run(variant_dir, out / "runs" / kind, smoke=True)
        reports[kind] = compare(out / "base", out / "runs" / kind, out / "comparisons" / kind)
        if mutant["question_count"] != base["question_count"]:
            raise CorpusError("demo question count changed")
    _, symbols, _ = load_corpus(corpus)
    old = next(s for s in symbols if s.canonical_id == "auth.validate_token")
    _, moved_symbols, _ = load_corpus(out / "variants" / "move_file")
    moved = next(s for s in moved_symbols if s.canonical_id == old.canonical_id)
    citations = [
        {"question_id": "auth-q001", "variant_id": "move_file-42", "path": old.path,
         "start_line": old.start_line, "end_line": old.start_line},
        {"question_id": "auth-q001", "variant_id": "move_file-42", "path": moved.path,
         "start_line": moved.start_line, "end_line": moved.end_line},
    ]
    citation_input = out / "citations.jsonl"
    citation_input.write_text("\n".join(json.dumps(row) for row in citations) + "\n", encoding="utf-8")
    citation_report = validate_citations(citation_input, out / "variants" / "move_file", out / "citations.json")
    return {"base": base, "comparisons": reports, "citations": citation_report}

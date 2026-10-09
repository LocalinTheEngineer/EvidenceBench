import json
import tempfile
import unittest
from pathlib import Path

from evidencebench.citations import validate_citations
from evidencebench.corpus import load_corpus
from evidencebench.mutations import mutate


SMOKE = Path(__file__).resolve().parents[1] / "corpus" / "smoke"


class CitationTests(unittest.TestCase):
    def check(self, corpus, citations):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "citations.jsonl"
            source.write_text("\n".join(json.dumps(item) for item in citations), encoding="utf-8")
            return validate_citations(source, corpus, Path(temporary) / "result.json")

    def test_valid_invalid_and_wide_span(self):
        manifest, symbols, _ = load_corpus(SMOKE)
        symbol = symbols[0]
        source = (SMOKE / symbol.path).read_text(encoding="utf-8")
        excerpt = "".join(source.splitlines(keepends=True)[symbol.start_line - 1:symbol.end_line])
        common = {"question_id": "auth-q001", "variant_id": manifest["variant_id"], "path": symbol.path}
        rows = self.check(SMOKE, [
            {**common, "start_line": symbol.start_line, "end_line": symbol.end_line, "quoted_excerpt": excerpt},
            {**common, "start_line": 1, "end_line": len(source.splitlines())},
            {**common, "start_line": symbol.start_line, "end_line": symbol.end_line, "quoted_excerpt": "wrong"},
            {**common, "start_line": -1, "end_line": 2},
            {**common, "path": "../escape.py", "start_line": 1, "end_line": 2},
            {**common, "start_line": 1, "end_line": 1000},
        ])["rows"]
        self.assertTrue(rows[0]["structural_valid"] and rows[0]["content_valid"] and rows[0]["relevance_valid"])
        self.assertLess(rows[1]["span_precision"], 1)
        self.assertFalse(rows[2]["content_valid"])
        self.assertTrue(all(not row["structural_valid"] for row in rows[3:]))

    def test_stale_citations_after_mutation(self):
        _, symbols, _ = load_corpus(SMOKE)
        old = symbols[0]
        with tempfile.TemporaryDirectory() as temporary:
            shift = Path(temporary) / "shift"
            move = Path(temporary) / "move"
            mutate(SMOKE, "prefix_comments", 42, shift)
            mutate(SMOKE, "move_file", 42, move)
            stale = {"question_id": "auth-q001", "path": old.path,
                     "start_line": old.start_line, "end_line": old.start_line}
            shifted = self.check(shift, [{**stale, "variant_id": "prefix_comments-42"}])["rows"][0]
            moved = self.check(move, [{**stale, "variant_id": "move_file-42"}])["rows"][0]
            self.assertTrue(shifted["structural_valid"])
            self.assertFalse(shifted["relevance_valid"])
            self.assertFalse(moved["structural_valid"])

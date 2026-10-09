import json
import tempfile
import unittest
from pathlib import Path

from evidencebench.compare import compare
from evidencebench.corpus import CorpusError
from evidencebench.mutations import mutate
from evidencebench.reports.html import render_comparison
from evidencebench.runner import run


SMOKE = Path(__file__).resolve().parents[1] / "corpus" / "smoke"


class CompareTests(unittest.TestCase):
    def test_paired_move(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mutant = root / "mutant"
            mutate(SMOKE, "move_file", 42, mutant)
            run(SMOKE, root / "base", include_draft=True)
            run(mutant, root / "moved", include_draft=True)
            report = compare(root / "base", root / "moved", root / "report")
            self.assertEqual(5, len(report["rows"]))
            self.assertIn("/moved/", report["rows"][0]["canonical_paths"]["auth.validate_token"]["mutant"])

    def test_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run(SMOKE, root / "base")
            run(SMOKE, root / "other", include_draft=True)
            with self.assertRaisesRegex(CorpusError, "mismatch"):
                compare(root / "base", root / "other", root / "report")

    def test_gate_requires_reviewed_and_html_escapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run(SMOKE, root / "base", include_draft=True)
            with self.assertRaisesRegex(CorpusError, "reviewed"):
                compare(root / "base", root / "base", root / "report", max_drop=0.1)
        html = render_comparison({"score_label": "<script>", "rows": [{"question_id": "q",
            "text": "<img src=x>", "base_rank": 1, "mutant_rank": 2,
            "failure_category": "miss"}]})
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img src=x>", html)

    def test_gate_minimum_and_drop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run(SMOKE, root / "base", include_draft=True)
            for name, recall in (("base", 0.8), ("mutant", 0.6)):
                folder = root / name
                folder.mkdir(exist_ok=True)
                data = json.loads((root / "base" / "run.json").read_text())
                data["score_label"] = "reviewed evaluation"  # isolated gate fixture, not corpus data
                data["scored_question_count"] = 5
                data["summary"]["macro_recall"]["@1"] = recall
                (folder / "run.json").write_text(json.dumps(data))
            insufficient = compare(root / "base", root / "mutant", root / "small", max_drop=.05, min_reviewed=10)
            self.assertFalse(insufficient["gate"]["passed"])
            regression = compare(root / "base", root / "mutant", root / "drop", max_drop=.05, min_reviewed=5)
            self.assertFalse(regression["gate"]["passed"])

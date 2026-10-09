import json
import tempfile
import unittest
from pathlib import Path

from evidencebench.corpus import CorpusError, load_corpus, safe_source


SMOKE = Path(__file__).resolve().parents[1] / "corpus" / "smoke"


class CorpusTests(unittest.TestCase):
    def test_smoke_corpus_loads(self):
        _, symbols, questions = load_corpus(SMOKE)
        self.assertEqual(6, len(symbols))
        self.assertEqual(7, len(questions))
        self.assertTrue(all(q.review_status == "draft" for q in questions))

    def test_path_traversal_rejected(self):
        with self.assertRaises(CorpusError):
            safe_source(SMOKE, "../questions.jsonl")

    def test_invalid_unanswerable_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_bytes((SMOKE / "manifest.json").read_bytes())
            (root / "repos").mkdir()
            import shutil
            shutil.copytree(SMOKE / "repos", root / "repos", dirs_exist_ok=True)
            rows = [json.loads(line) for line in (SMOKE / "questions.jsonl").read_text().splitlines()]
            rows[2]["relevant_symbols"] = ["auth.validate_token"]
            (root / "questions.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
            with self.assertRaisesRegex(CorpusError, "answerability"):
                load_corpus(root)

    def test_unknown_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text('{"schema_version":99}')
            with self.assertRaisesRegex(CorpusError, "unsupported"):
                load_corpus(root)

    def test_split_contamination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            import shutil
            shutil.copytree(SMOKE, root, dirs_exist_ok=True)
            rows = [json.loads(line) for line in (root / "questions.jsonl").read_text().splitlines()]
            rows[0]["split"] = "test"
            (root / "questions.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
            with self.assertRaisesRegex(CorpusError, "both dev and test"):
                load_corpus(root)

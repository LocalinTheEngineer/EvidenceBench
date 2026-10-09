import unittest
import tempfile
from pathlib import Path

from evidencebench.metrics import aggregate, score_question
from evidencebench.models import Question, RankedChunk
from evidencebench.runner import run


def question(labels):
    return Question("q", "r", "dev", "query", True, tuple(labels), "reviewed", "reason", "human")


def hit(symbol, i):
    return RankedChunk(f"c{i}", symbol, "file.py", 1, 2, 1.0, "hash", "base")


class MetricTests(unittest.TestCase):
    def test_multilabel_recall_differs_from_hit_rate(self):
        q = question(["a", "b"])
        row = score_question(q, [hit("a", 1), hit("x", 2)])
        self.assertEqual(.5, row["recall"]["recall@1"])
        self.assertEqual(1, row["hit_rate"]["hit_rate@1"])

    def test_first_relevant_rank_and_duplicate_collapse(self):
        row = score_question(question(["a"]), [hit("x", 1), hit("x", 2), hit("a", 3)])
        self.assertEqual(2, row["first_relevant_rank"])
        self.assertEqual(.5, row["mrr"])

    def test_no_hit(self):
        row = score_question(question(["a"]), [hit("x", 1)])
        self.assertEqual(0, row["mrr"])

    def test_empty_reviewed_aggregate(self):
        self.assertIsNone(aggregate([], []))

    def test_run_draft_opt_in(self):
        corpus = Path(__file__).resolve().parents[1] / "corpus" / "smoke"
        with tempfile.TemporaryDirectory() as temporary:
            result = run(corpus, Path(temporary) / "base")
            self.assertIsNone(result["summary"])
            self.assertEqual(0, result["scored_question_count"])
            exploratory = run(corpus, Path(temporary) / "draft", include_draft=True)
            self.assertEqual("unreviewed exploratory", exploratory["score_label"])
            self.assertEqual(5, exploratory["scored_question_count"])

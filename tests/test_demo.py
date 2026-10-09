import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evidencebench.cli import main
from evidencebench.demo import demo


class DemoTests(unittest.TestCase):
    def test_end_to_end_demo(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "demo"
            result = demo(out)
            self.assertEqual("synthetic smoke", result["base"]["score_label"])
            self.assertEqual(3, len(result["comparisons"]))
            self.assertEqual(1, result["citations"]["structural_invalid_count"])
            self.assertTrue((out / "comparisons" / "move_file" / "index.html").is_file())

    def test_cli_exit_codes(self):
        corpus = Path(__file__).resolve().parents[1] / "corpus" / "smoke"
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(3, main(["run", str(corpus), "--retriever", "missing", "--out", temporary]))
            self.assertEqual(2, main(["validate", str(Path(temporary) / "absent")]))
            with patch("evidencebench.cli.compare", return_value={"recall_at_1_delta": -.2,
                                                          "gate": {"passed": False}}):
                self.assertEqual(1, main(["compare", "base", "mutant", "--out", temporary]))

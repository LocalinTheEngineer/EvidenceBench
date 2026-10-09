import hashlib
import tempfile
import unittest
from pathlib import Path

from evidencebench.chunking import chunks_for_corpus
from evidencebench.corpus import load_corpus
from evidencebench.mutations import mutate


SMOKE = Path(__file__).resolve().parents[1] / "corpus" / "smoke"


def tree_hash(root):
    sha = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            sha.update(path.relative_to(root).as_posix().encode())
            sha.update(path.read_bytes())
    return sha.hexdigest()


class MutationTests(unittest.TestCase):
    def test_three_mutations_preserve_labels_and_source(self):
        original = tree_hash(SMOKE)
        _, base_symbols, _ = load_corpus(SMOKE)
        with tempfile.TemporaryDirectory() as temporary:
            for kind in ("move_file", "prefix_comments", "add_distractor"):
                out = Path(temporary) / kind
                mutate(SMOKE, kind, 42, out)
                manifest, symbols, _ = load_corpus(out)
                self.assertEqual({s.canonical_id for s in base_symbols}, {s.canonical_id for s in symbols})
                self.assertEqual(6, len(base_symbols))
                chunks = chunks_for_corpus(out, manifest, symbols)
                if kind == "move_file":
                    self.assertTrue(all("/moved/" in s.path for s in symbols))
                if kind == "prefix_comments":
                    self.assertEqual(base_symbols[0].start_line + 3, symbols[0].start_line)
                if kind == "add_distractor":
                    self.assertEqual(9, len(chunks))
                    self.assertTrue(any(chunk.canonical_id is None for chunk in chunks))
            self.assertEqual(original, tree_hash(SMOKE))

    def test_same_seed_byte_identical(self):
        with tempfile.TemporaryDirectory() as temporary:
            a, b = Path(temporary) / "a", Path(temporary) / "b"
            mutate(SMOKE, "add_distractor", 7, a)
            mutate(SMOKE, "add_distractor", 7, b)
            self.assertEqual(tree_hash(a), tree_hash(b))

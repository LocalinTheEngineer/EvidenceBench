import unittest
from pathlib import Path

from evidencebench.adapters.bm25 import BM25Retriever, tokenize
from evidencebench.chunking import chunks_for_corpus
from evidencebench.corpus import load_corpus
from evidencebench.models import Chunk


SMOKE = Path(__file__).resolve().parents[1] / "corpus" / "smoke"


class RetrievalTests(unittest.TestCase):
    def test_ast_chunk_and_search(self):
        manifest, symbols, _ = load_corpus(SMOKE)
        chunks = chunks_for_corpus(SMOKE, manifest, symbols)
        self.assertEqual(6, len(chunks))
        retriever = BM25Retriever()
        retriever.index(chunks)
        hits = retriever.search("validate_token expires_at", 3)
        self.assertEqual("auth.validate_token", hits[0].canonical_id)

    def test_identifier_parts(self):
        self.assertEqual(["validate_token", "validate", "token", "httpserver", "http", "server"], tokenize("validate_token HTTPServer"))

    def test_tie_and_oversized_k(self):
        chunks = [Chunk(id, None, f"{id}.py", 1, 1, "needle", "hash", "base") for id in ("b", "a")]
        retriever = BM25Retriever()
        retriever.index(chunks)
        self.assertEqual(["a", "b"], [hit.chunk_id for hit in retriever.search("needle", 5)])

    def test_duplicate_rejected(self):
        chunk = Chunk("a", None, "a.py", 1, 1, "needle", "hash", "base")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            BM25Retriever().index([chunk, chunk])

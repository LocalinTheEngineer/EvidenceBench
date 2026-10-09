"""Dependency-free BM25 with deterministic ranking."""
from __future__ import annotations

import math
import re
from collections import Counter

from evidencebench.models import Chunk, RankedChunk

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+")
CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize(value: str) -> list[str]:
    tokens = []
    for match in IDENTIFIER.finditer(value):
        raw = match.group()
        full = raw.lower()
        tokens.append(full)
        for part in raw.split("_"):
            for piece in CAMEL.split(part):
                piece = piece.lower()
                if piece and piece != full:
                    tokens.append(piece)
    return tokens


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: list[Chunk] = []
        self.documents: list[Counter[str]] = []
        self.idf: dict[str, float] = {}
        self.avgdl = 0.0

    def index(self, chunks: list[Chunk]) -> None:
        ids = [chunk.chunk_id for chunk in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate chunk_id")
        self.chunks = list(chunks)
        self.documents = [Counter(tokenize(chunk.path + " " + chunk.chunk_id + " " + chunk.content)) for chunk in chunks]
        n = len(chunks)
        self.avgdl = sum(sum(doc.values()) for doc in self.documents) / n if n else 0.0
        df = Counter(token for doc in self.documents for token in doc)
        self.idf = {token: math.log(1 + (n - count + 0.5) / (count + 0.5)) for token, count in df.items()}

    def search(self, query: str, k: int) -> list[RankedChunk]:
        if k < 1:
            raise ValueError("k must be positive")
        terms = set(tokenize(query))
        scored = []
        for chunk, doc in zip(self.chunks, self.documents):
            length = sum(doc.values())
            score = 0.0
            for term in terms:
                tf = doc.get(term, 0)
                if tf:
                    score += self.idf[term] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * length / self.avgdl))
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: (-pair[0], pair[1].chunk_id))
        return [RankedChunk(
            chunk_id=chunk.chunk_id, canonical_id=chunk.canonical_id, path=chunk.path,
            start_line=chunk.start_line, end_line=chunk.end_line, score=score,
            content_hash=chunk.content_hash, variant_id=chunk.variant_id,
        ) for score, chunk in scored[:k]]

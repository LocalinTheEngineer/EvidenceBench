"""Small, explicit data records shared by the evaluator."""
from dataclasses import dataclass


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Symbol:
    canonical_id: str
    path: str
    symbol: str
    start_line: int
    end_line: int
    content_hash: str


@dataclass(frozen=True)
class Question:
    question_id: str
    repo_id: str
    split: str
    text: str
    answerable: bool
    relevant_symbols: tuple[str, ...]
    review_status: str
    rationale: str
    reviewer: str | None = None


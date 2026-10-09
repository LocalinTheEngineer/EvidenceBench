"""Retrieval metrics over unique canonical symbols."""
from __future__ import annotations

from .models import Question, RankedChunk

K_VALUES = (1, 3, 5)


def ranked_symbols(hits: list[RankedChunk]) -> list[str | None]:
    seen = set()
    ranked = []
    for hit in hits:
        key = hit.canonical_id or hit.chunk_id
        if key not in seen:
            seen.add(key)
            ranked.append(hit.canonical_id)
    return ranked


def score_question(question: Question, hits: list[RankedChunk]) -> dict:
    ranked = ranked_symbols(hits)
    relevant = set(question.relevant_symbols)
    if not question.answerable:
        return {"question_id": question.question_id, "answerable": False,
                "ranked_results": len(ranked), "first_relevant_rank": None,
                "failure_category": None}
    first = next((i for i, symbol in enumerate(ranked, 1) if symbol in relevant), None)
    recalls = {f"recall@{k}": len(relevant.intersection(ranked[:k])) / len(relevant) for k in K_VALUES}
    hits_at = {f"hit_rate@{k}": float(bool(relevant.intersection(ranked[:k]))) for k in K_VALUES}
    if first == 1:
        category = "hit"
    elif ranked and ranked[0] is None:
        category = "distractor_first"
    elif first:
        category = "ranked_behind_other_symbol"
    else:
        category = "missing_relevant"
    return {"question_id": question.question_id, "answerable": True,
            "first_relevant_rank": first, "recall": recalls, "hit_rate": hits_at,
            "mrr": 1 / first if first else 0.0, "failure_category": category}


def aggregate(questions: list[Question], rows: list[dict]) -> dict | None:
    answerable = [row for row in rows if row["answerable"]]
    if not answerable:
        return None
    return {
        "answerable_count": len(answerable),
        "unanswerable_count": len(rows) - len(answerable),
        "macro_recall": {f"@{k}": sum(row["recall"][f"recall@{k}"] for row in answerable) / len(answerable) for k in K_VALUES},
        "hit_rate": {f"@{k}": sum(row["hit_rate"][f"hit_rate@{k}"] for row in answerable) / len(answerable) for k in K_VALUES},
        "mrr": sum(row["mrr"] for row in answerable) / len(answerable),
    }

# ADR 0002: Offline retrieval evaluation instead of LLM-as-judge

Status: accepted.

The core uses Python AST and a small, deterministic BM25 implementation. It measures retrieval coverage and citation validity without an API key, downloaded model, or answer generation. This keeps runs inspectable and lets a change in source location be isolated from answer model behavior.

An alternative was to score generated answers with another model. That would add cost, nondeterminism, and a second quality question before the retrieval baseline was known. The limitation is deliberate: EvidenceBench cannot report hallucination or refusal rates. An optional adapter may later compare a real retriever with the same corpus contract.

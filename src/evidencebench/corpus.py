"""Versioned corpus loading with source and label validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from .models import Question, SCHEMA_VERSION, Symbol

MAX_SOURCE_BYTES = 1_000_000


class CorpusError(ValueError):
    pass


def safe_source(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise CorpusError(f"unsafe source path: {relative}")
    full = root / relative
    if not full.resolve().is_relative_to(root.resolve()):
        raise CorpusError(f"source escapes corpus: {relative}")
    if not full.is_file() or full.stat().st_size > MAX_SOURCE_BYTES:
        raise CorpusError(f"missing or oversized source: {relative}")
    return full


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CorpusError(f"invalid JSON: {path}") from exc


def load_corpus(root: Path) -> tuple[dict, list[Symbol], list[Question]]:
    root = root.resolve()
    manifest = read_json(safe_source(root, "manifest.json"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise CorpusError("unsupported manifest schema_version")
    variant_id = manifest.get("variant_id")
    if not isinstance(variant_id, str) or not variant_id:
        raise CorpusError("missing variant_id")
    symbols = []
    ids = set()
    for item in manifest.get("symbols", []):
        symbol = Symbol(**item)
        if symbol.canonical_id in ids:
            raise CorpusError(f"duplicate canonical_id: {symbol.canonical_id}")
        ids.add(symbol.canonical_id)
        source = safe_source(root, symbol.path).read_text(encoding="utf-8")
        lines = source.splitlines(keepends=True)
        if not (1 <= symbol.start_line <= symbol.end_line <= len(lines)):
            raise CorpusError(f"invalid span: {symbol.canonical_id}")
        excerpt = "".join(lines[symbol.start_line - 1:symbol.end_line])
        if hashlib.sha256(excerpt.encode()).hexdigest() != symbol.content_hash:
            raise CorpusError(f"content hash mismatch: {symbol.canonical_id}")
        symbols.append(symbol)
    questions = []
    qids = set()
    split_by_repo = {}
    for line_number, line in enumerate(safe_source(root, "questions.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
            if item.pop("schema_version", None) != SCHEMA_VERSION:
                raise CorpusError(f"unsupported question schema at line {line_number}")
            item["relevant_symbols"] = tuple(item["relevant_symbols"])
            question = Question(**item)
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise CorpusError(f"invalid question at line {line_number}") from exc
        if question.question_id in qids or not question.question_id:
            raise CorpusError(f"duplicate/empty question_id: {question.question_id}")
        qids.add(question.question_id)
        if question.split not in {"dev", "test"} or question.review_status not in {"draft", "reviewed"}:
            raise CorpusError(f"invalid split/review status: {question.question_id}")
        if question.review_status == "reviewed" and not question.reviewer:
            raise CorpusError(f"reviewed label lacks reviewer: {question.question_id}")
        if question.answerable != bool(question.relevant_symbols):
            raise CorpusError(f"answerability/labels mismatch: {question.question_id}")
        if any(label not in ids for label in question.relevant_symbols):
            raise CorpusError(f"unknown relevant symbol: {question.question_id}")
        if not any(symbol.path.startswith(f"repos/{question.repo_id}/") for symbol in symbols):
            raise CorpusError(f"unknown repo_id: {question.question_id}")
        repo = question.repo_id
        split_by_repo.setdefault(repo, set()).add(question.split)
        questions.append(question)
    if any(len(splits) > 1 for splits in split_by_repo.values()):
        raise CorpusError("repo appears in both dev and test splits")
    if not questions or not symbols:
        raise CorpusError("empty corpus")
    return manifest, symbols, questions

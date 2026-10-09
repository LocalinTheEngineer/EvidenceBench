"""AST chunks anchored to immutable canonical symbols."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from .corpus import CorpusError, safe_source
from .models import Chunk, Symbol


def chunks_for_corpus(root: Path, manifest: dict, symbols: list[Symbol]) -> list[Chunk]:
    by_path: dict[str, list[Symbol]] = {}
    for symbol in symbols:
        by_path.setdefault(symbol.path, []).append(symbol)
    chunks: list[Chunk] = []
    source_paths = set(by_path)
    for full in (root / "repos").rglob("*.py"):
        relative = full.relative_to(root).as_posix()
        safe_source(root, relative)
        source_paths.add(relative)
    for path in sorted(source_paths):
        source = safe_source(root, path).read_text(encoding="utf-8")
        lines = source.splitlines(keepends=True)
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            raise CorpusError(f"Python syntax error in {path}: {exc}") from exc
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        mapped = set()
        for node in nodes:
            matches = [s for s in by_path.get(path, []) if s.symbol == node.name]
            if len(matches) > 1:
                raise CorpusError(f"ambiguous symbol {node.name} in {path}")
            symbol = matches[0] if matches else None
            if symbol:
                mapped.add(symbol.canonical_id)
                if (symbol.start_line, symbol.end_line) != (node.lineno, node.end_lineno):
                    raise CorpusError(f"stale manifest span: {symbol.canonical_id}")
            excerpt = "".join(lines[node.lineno - 1:node.end_lineno])
            digest = hashlib.sha256(excerpt.encode()).hexdigest()
            chunks.append(Chunk(
                chunk_id=f"{path}:{node.name}:{node.lineno}",
                canonical_id=symbol.canonical_id if symbol else None,
                path=path,
                start_line=node.lineno,
                end_line=node.end_lineno,
                content=excerpt,
                content_hash=digest,
                variant_id=manifest["variant_id"],
            ))
        if mapped != {s.canonical_id for s in by_path.get(path, [])}:
            raise CorpusError(f"manifest symbol missing in AST: {path}")
        if not nodes:
            chunks.append(Chunk(
                chunk_id=f"{path}:module:1", canonical_id=None, path=path,
                start_line=1, end_line=len(lines), content=source,
                content_hash=hashlib.sha256(source.encode()).hexdigest(),
                variant_id=manifest["variant_id"],
            ))
    return chunks

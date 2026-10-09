"""Deterministic, source-preserving fixture mutations."""
from __future__ import annotations

import ast
import hashlib
import json
import random
import runpy
from pathlib import Path

from .corpus import CorpusError, load_corpus, safe_source

KINDS = ("move_file", "prefix_comments", "add_distractor")


def _check_bundled_fixture_behavior(out: Path, mapping: dict[str, str]) -> None:
    """Execute only the three fixtures shipped with this package, never user corpora."""
    auth = runpy.run_path(str(out / mapping["repos/tiny_auth/auth.py"]))
    token = auth["issue_token"]("cem", 10)
    if not auth["validate_token"](token, 9) or auth["validate_token"](token, 10):
        raise CorpusError("fixture behavior changed: validate_token")
    worker = runpy.run_path(str(out / mapping["repos/job_worker/worker.py"]))
    if worker["retry_job"]({}, 2, 2) != "dead_letter" or worker["claim_job"](["one"]) != "one":
        raise CorpusError("fixture behavior changed: worker")
    config = runpy.run_path(str(out / mapping["repos/config_loader/config.py"]))
    if config["load_config"]({"x": 1}, {"x": 2}) != {"x": 2}:
        raise CorpusError("fixture behavior changed: load_config")
    try:
        config["require_key"]({}, "x")
    except KeyError:
        pass
    else:
        raise CorpusError("fixture behavior changed: require_key")


def mutate(corpus: Path, kind: str, seed: int, out: Path) -> dict:
    if kind not in KINDS:
        raise CorpusError(f"unknown mutation: {kind}")
    corpus = corpus.resolve()
    out = out.resolve()
    if out == corpus or out.is_relative_to(corpus) or corpus.is_relative_to(out):
        raise CorpusError("output must be separate from input corpus")
    if out.exists():
        raise CorpusError("output directory already exists")
    manifest, symbols, _ = load_corpus(corpus)
    files = {}
    for full in (corpus / "repos").rglob("*.py"):
        relative = full.relative_to(corpus).as_posix()
        files[relative] = safe_source(corpus, relative).read_text(encoding="utf-8")
    if not files:
        raise CorpusError("no Python source files")
    mapping = {path: path for path in files}
    if kind == "move_file":
        mapping = {path: str(Path(path).parent / "moved" / Path(path).name).replace("\\", "/") for path in files}
    if kind == "prefix_comments":
        files = {path: "# EvidenceBench line shift 1\n# EvidenceBench line shift 2\n# EvidenceBench line shift 3\n" + source for path, source in files.items()}
    if kind == "add_distractor":
        rng = random.Random(seed)
        for repo in sorted({path.split("/")[1] for path in files}):
            marker = rng.randrange(1_000_000)
            files[f"repos/{repo}/distractor.py"] = (
                f'"""Unrelated lexical distractor {marker}."""\n\n'
                "def validate_token_retry_config(expires_at, attempts, overrides):\n"
                "    # token expiry retry limit config overrides; documentation only\n"
                "    return (expires_at, attempts, overrides)\n"
            )
    written = {mapping.get(path, path): source for path, source in files.items()}
    new_symbols = []
    for symbol in symbols:
        path = mapping[symbol.path]
        source = written[path]
        nodes = [node for node in ast.parse(source, filename=path).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol.symbol]
        if len(nodes) != 1:
            raise CorpusError(f"symbol changed by mutation: {symbol.canonical_id}")
        node = nodes[0]
        excerpt = "".join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
        new_symbols.append({"canonical_id": symbol.canonical_id, "path": path,
                            "symbol": symbol.symbol, "start_line": node.lineno,
                            "end_line": node.end_lineno,
                            "content_hash": hashlib.sha256(excerpt.encode()).hexdigest()})
    for path, source in written.items():
        ast.parse(source, filename=path)
    out.mkdir(parents=True)
    for path, source in sorted(written.items()):
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8", newline="\n")
    (out / "questions.jsonl").write_bytes((corpus / "questions.jsonl").read_bytes())
    new_manifest = {"schema_version": 1, "variant_id": f"{kind}-{seed}",
                    "parent_variant_id": manifest["variant_id"], "symbols": new_symbols}
    (out / "manifest.json").write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    load_corpus(out)
    bundled = Path(__file__).resolve().parents[2] / "corpus" / "smoke"
    if corpus == bundled.resolve():
        _check_bundled_fixture_behavior(out, mapping)
    return new_manifest

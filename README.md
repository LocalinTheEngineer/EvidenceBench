# EvidenceBench

EvidenceBench is an offline Python CLI for measuring code retrieval and citation changes after source mutations. It searches authored Python fixtures with BM25; it does not generate answers or call an LLM. All included labels are **draft**, so the example scores are synthetic and unreviewed.

## Install

Python 3.11+ is required. The runtime has no third-party dependencies, API keys, database, or model download. Build isolation installs the setuptools version pinned in `pyproject.toml`.

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/evidencebench validate corpus/smoke
.venv/Scripts/python -m unittest discover -s tests
```

On macOS/Linux use `.venv/bin/` instead of `.venv/Scripts/`. The lock file is a single editable local project entry because the runtime dependency graph is empty; the build backend is pinned separately.

## 90-second demo

```sh
.venv/Scripts/evidencebench demo --out reports/demo
```

Open `reports/demo/comparisons/move_file/index.html`. The `base/run.json` file shows actual BM25 ranks. The move variant has a new path for the same canonical symbol. `citations.json` shows an old citation path failing the structural check and a new path passing. The shift and distractor comparisons are also included.

Individual commands:

```sh
evidencebench validate corpus/smoke
evidencebench mutate corpus/smoke --kind prefix_comments --seed 42 --out variants/shift
evidencebench run corpus/smoke --retriever bm25 --split dev --out runs/base
evidencebench run variants/shift --retriever bm25 --split dev --out runs/shift
evidencebench compare runs/base runs/shift --out reports/comparison
evidencebench run corpus/evaluation --split test --out runs/evaluation-test
evidencebench run corpus/evaluation --split test --include-draft --out runs/exploratory-test
evidencebench citations examples/citations.jsonl --corpus corpus/smoke --out reports/citations.json
```

Without `--include-draft`, evaluation aggregates are `null` because no questions have been reviewed. `demo` explicitly scores the authored smoke corpus and labels it `synthetic smoke`. Draft evaluation scores are labeled `unreviewed exploratory`. A configured gate requires reviewed evaluation labels, a minimum reviewed question count, and an allowed Recall@1 drop:

```sh
evidencebench compare runs/base runs/shift --out reports/gate --max-drop 0.05 --min-reviewed 20
```

The above gate command rejects these draft example runs. Exit codes: 0 valid run, 1 failed configured gate, 2 invalid input/schema, 3 unavailable adapter.

## Data and design

`corpus/smoke` contains three small authored repositories. `corpus/evaluation` contains a 45-question draft scaffold split by repository into dev and test. Neither is a real-world benchmark. Canonical symbols identify concepts independently of path and line location; each variant manifest maps these IDs to current paths, inclusive 1-based spans, and content hashes. Source files are never mutated in place. A separate index is built per fixture repository and variant.

Recall@k averages per-question coverage of all relevant symbols; HitRate@k counts questions with at least one hit. MRR uses the first relevant unique symbol. Unanswerable questions report ranked results and count, not hallucination/refusal success. Citation checks report structure, exact excerpt content after newline normalization, gold span overlap, and span precision separately. A large cited span can overlap the gold while having low precision; overlap is not semantic proof.

`docs/dataset-card.md` describes the source, label status, and limitations. `docs/learning.md` gives exercises for each stage. Two design records in `docs/adr/` explain the central tradeoffs. `STATUS.md` lists remaining work.

## Scope and limitations

Only Python AST chunking and a deterministic BM25 adapter are included. The RepoLensAI adapter remains optional and unavailable: its current API depends on an indexed RepoLens/Qdrant environment and cannot be exercised by this standalone offline corpus. The CLI returns exit 3 for any unavailable adapter. No embedding, hybrid, model speed, or answer quality claim is made. Local timings in run JSON are evaluator/index/search timings with one repeat and no warmup; they are diagnostic, not a benchmark latency result.

The project is MIT licensed. Contributing guidance is in `CONTRIBUTING.md`.

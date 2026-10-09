# Dataset card

## Source and license

The three Python fixture repositories (`tiny_auth`, `job_worker`, `config_loader`) and all questions were authored for EvidenceBench under MIT. No third-party source files or questions are copied into the corpus.

## Labels and splits

The smoke corpus has seven authored questions and fixed expected symbols for deterministic tests. The evaluation scaffold has 45 AI-authored questions, all marked `review_status=draft`; there is no human-reviewed result. `tiny_auth` and `job_worker` are dev; `config_loader` is test. No fixture repository appears in both splits. The questions include answerable and intentionally unanswerable cases. A reviewer must verify each question, source span, answerability, rationale, and duplicate meaning before marking it reviewed.

## Variants

`move_file` moves self-contained fixture files, `prefix_comments` shifts lines, and `add_distractor` creates a lexically similar unrelated Python function. These are paired changes to the same questions, not independent additional samples. v1 does not model deleted APIs, extraction, renaming, or large real codebases.

## Limitations

The corpus is tiny, synthetic, Python-only, and lexically simple. It cannot support claims about real repository retrieval, answer correctness, hallucination, production latency, or statistical significance. Draft scores require explicit `--include-draft` and are exploratory only.

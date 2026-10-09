# Learning path

## 1. Corpus schema and canonical mapping

- Problem: a moved function changes its path but not its meaning.
- Decision: store `canonical_id` and a per-variant path/span/hash mapping.
- Alternative: use the file path as the label.
- Failure example: `auth.validate_token` moves and a path-only scorer calls it missing.
- Try: move the function in a copy and update its manifest mapping.
- Check: why is path not identity?

## 2. AST chunks and BM25

- Problem: line windows can split a function and identifiers have multiple spellings.
- Decision: chunk top-level Python functions/classes and tokenize snake_case/camelCase consistently.
- Alternative: fixed 20-line chunks and raw whitespace splitting.
- Failure example: `validate_token` does not match `validate token` without normalization.
- Try: add a CamelCase fixture symbol and inspect its tokens.
- Check: why does `chunk_id` break score ties?

## 3. Retrieval metrics

- Problem: finding one of two relevant symbols is not full coverage.
- Decision: calculate Recall@k, HitRate@k, and MRR separately over unique canonical symbols.
- Alternative: call every hit a recall success.
- Failure example: one of two relevant symbols at rank 1 means Recall@1=0.5, HitRate@1=1.
- Try: calculate that case by hand before running `test_metrics.py`.
- Check: what is MRR when the first relevant symbol is rank 3?

## 4. Mutations

- Problem: source changes need paired labels at new locations.
- Decision: create a separate output tree and rebuild the manifest from AST locations.
- Alternative: edit fixture files in place and keep old spans.
- Failure example: comments shift a function while an old citation still points at its old line.
- Try: run `prefix_comments` with seed 42 and inspect the manifest.
- Check: why must the mapping be regenerated?

## 5. Citations

- Problem: an existing file and line span may still cite irrelevant code.
- Decision: report structural, excerpt, and relevance checks separately.
- Alternative: accept any citation to an existing file.
- Failure example: a span covering the whole file overlaps gold but has low span precision.
- Try: cite a single comment line after a shift and inspect the result.
- Check: can structural validity imply semantic correctness?

## 6. Comparison and reports

- Problem: two runs with different questions cannot be compared fairly.
- Decision: require matching label/config hashes and compare each question as a pair.
- Alternative: subtract aggregate scores without checking inputs.
- Failure example: a changed question set appears to improve Recall@1.
- Try: change one question in a copy and confirm compare rejects it.
- Check: why are mutations not independent samples?

## 7. Offline demo and CI

- Problem: a result should be reproducible without paid services.
- Decision: package a one-command smoke workflow and run tests in CI.
- Alternative: require a hosted model and database for the first demo.
- Failure example: missing API credentials block a retrieval baseline.
- Try: run `evidencebench demo --out reports/demo` after a clean install.
- Check: what does GitHub Actions verify that a local run cannot?

## 8. Draft evaluation scaffold

- Problem: generated labels can look authoritative before a person checks them.
- Decision: keep every evaluation question draft and hide its aggregate by default.
- Alternative: mark AI-generated labels reviewed automatically.
- Failure example: a mistaken gold symbol becomes a misleading benchmark success.
- Try: review one question against the fixture and write a clear rationale.
- Check: what evidence is needed before setting `review_status=reviewed`?

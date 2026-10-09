# Contributing

Use Python 3.11 or newer. Install with `python -m pip install -r requirements.lock`, then run `python -m unittest discover -s tests -v` and `ruff check src tests` if Ruff is installed.

Keep source fixture changes small and update each manifest span and SHA-256 content hash. Treat generated question labels as `draft`. To mark a label `reviewed`, a human reviewer must inspect the source, record their name and rationale, and check that the question has one unambiguous intended meaning. Keep equivalent questions from the same fixture repository in one split. Add tests for boundary cases and keep reports free of absolute local paths.

Open an issue with a minimal corpus, expected canonical symbol, actual ranked results, and CLI command when reporting a retrieval regression.

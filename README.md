# EvidenceBench

EvidenceBench measures how code retrieval and citations change when a small source repository is mutated. The current corpus is synthetic and all labels are draft.

## First working slice

Python 3.11+ is required. From a clean checkout:

```sh
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/evidencebench validate corpus/smoke
.venv/Scripts/python -m unittest discover -s tests
```

On macOS/Linux use `.venv/bin/` instead of `.venv/Scripts/`.

The project has no runtime dependencies or model download. The pinned build backend is recorded in `pyproject.toml`. The current slice validates canonical symbol mappings and authored fixture labels; retrieval and mutation follow in separate commits.

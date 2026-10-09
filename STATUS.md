# Status

The standalone MVP is implemented: authored fixtures, versioned labels, AST chunks, BM25, retrieval metrics, three source mutations, citation checks, paired JSON/HTML comparison, opt-in gate, and offline demo. Every bundled corpus label remains draft.

Remaining work:

- Human review of the 45-question evaluation scaffold; no reviewed aggregate is available yet.
- Optional RepoLensAI adapter and an end-to-end run against its Qdrant-backed index. The current standalone CLI rejects it with exit 3.
- Broader real-repository and multilingual evaluation are v2 work.

The CI workflow is provided; local tests and demo have been run separately from GitHub Actions status.

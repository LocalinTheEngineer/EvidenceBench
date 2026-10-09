# ADR 0001: Canonical symbols instead of paths as ground truth

Status: accepted.

The same function can move or shift lines without changing its meaning. Ground truth therefore uses an immutable canonical ID such as `auth.validate_token`. Each variant manifest maps that ID to a relative path, inclusive 1-based AST span, and content hash. Retrieval scoring compares IDs while citation checks compare the variant's current path and span.

An alternative was to label only paths and lines. That would falsely treat a valid move as a lost concept and cannot separate retrieval failure from a stale citation. The tradeoff is that v1 cannot automatically preserve IDs through arbitrary refactors or function extraction; those require explicit mapping and review.

"""Command line entry point."""
import argparse
import sys
from pathlib import Path

from .corpus import CorpusError, load_corpus
from .runner import run
from .mutations import KINDS, mutate
from .citations import validate_citations
from .compare import compare


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evidencebench")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate corpus labels and manifest")
    validate.add_argument("corpus", type=Path)
    execute = commands.add_parser("run", help="index and evaluate one corpus variant")
    execute.add_argument("corpus", type=Path)
    execute.add_argument("--retriever", default="bm25")
    execute.add_argument("--split", choices=("dev", "test"), default="dev")
    execute.add_argument("--include-draft", action="store_true")
    execute.add_argument("--out", type=Path, required=True)
    mutation = commands.add_parser("mutate", help="create a deterministic corpus variant")
    mutation.add_argument("corpus", type=Path)
    mutation.add_argument("--kind", choices=KINDS, required=True)
    mutation.add_argument("--seed", type=int, default=42)
    mutation.add_argument("--out", type=Path, required=True)
    citations = commands.add_parser("citations", help="validate citation spans")
    citations.add_argument("input", type=Path)
    citations.add_argument("--corpus", type=Path, required=True)
    citations.add_argument("--out", type=Path, required=True)
    comparison = commands.add_parser("compare", help="compare paired base and mutant runs")
    comparison.add_argument("base", type=Path)
    comparison.add_argument("mutant", type=Path)
    comparison.add_argument("--out", type=Path, required=True)
    comparison.add_argument("--max-drop", type=float)
    comparison.add_argument("--min-reviewed", type=int, default=10)
    comparison.add_argument("--allowed-invalid-citations", type=int, default=0)
    comparison.add_argument("--citations-report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            result = run(args.corpus, args.out, args.split, args.include_draft,
                         retriever_name=args.retriever)
            print(f"{result['score_label']}: {result['question_count']} questions; summary={result['summary']}")
            return 0
        if args.command == "mutate":
            result = mutate(args.corpus, args.kind, args.seed, args.out)
            print(f"created {result['variant_id']} at {args.out}")
            return 0
        if args.command == "citations":
            result = validate_citations(args.input, args.corpus, args.out)
            print(f"checked {result['citation_count']} citations; {result['structural_invalid_count']} structurally invalid")
            return 0
        if args.command == "compare":
            result = compare(args.base, args.mutant, args.out, args.max_drop,
                             args.min_reviewed, args.allowed_invalid_citations,
                             args.citations_report)
            print(f"comparison: recall@1 delta={result['recall_at_1_delta']}; gate={result['gate']}")
            return 1 if result["gate"] is not None and not result["gate"]["passed"] else 0
        manifest, symbols, questions = load_corpus(args.corpus)
    except (CorpusError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"valid {manifest['variant_id']}: {len(symbols)} symbols, {len(questions)} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

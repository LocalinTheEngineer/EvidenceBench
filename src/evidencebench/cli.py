"""Command line entry point."""
import argparse
import sys
from pathlib import Path

from .corpus import CorpusError, load_corpus
from .runner import run
from .mutations import KINDS, mutate


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
        manifest, symbols, questions = load_corpus(args.corpus)
    except (CorpusError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"valid {manifest['variant_id']}: {len(symbols)} symbols, {len(questions)} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

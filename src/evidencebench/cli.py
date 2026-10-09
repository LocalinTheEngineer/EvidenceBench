"""Command line entry point."""
import argparse
import sys
from pathlib import Path

from .corpus import CorpusError, load_corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evidencebench")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate corpus labels and manifest")
    validate.add_argument("corpus", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest, symbols, questions = load_corpus(args.corpus)
    except (CorpusError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"valid {manifest['variant_id']}: {len(symbols)} symbols, {len(questions)} questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

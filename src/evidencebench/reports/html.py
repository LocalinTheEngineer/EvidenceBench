"""Escaped standalone comparison HTML."""
from __future__ import annotations

from html import escape


def render_comparison(report: dict) -> str:
    rows = []
    for row in report["rows"]:
        cells = [row["question_id"], row["text"], str(row["base_rank"]),
                 str(row["mutant_rank"]), row["failure_category"] or ""]
        rows.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>")
    label = escape(report["score_label"])
    return ("<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            "<title>EvidenceBench comparison</title>"
            "<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}"
            "table{border-collapse:collapse;width:100%}td,th{padding:.5rem;border:1px solid #bbb}"
            "th{text-align:left}</style>"
            f"<h1>EvidenceBench comparison</h1><p>{label}</p>"
            "<table><thead><tr><th>Question</th><th>Text</th><th>Base rank</th>"
            "<th>Mutant rank</th><th>Category</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table></html>\n")

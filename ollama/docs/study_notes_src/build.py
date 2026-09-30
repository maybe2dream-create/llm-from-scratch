#!/usr/bin/env python3
"""Build ollama/docs/llm_security_study_notes.pdf from report.html + diagrams/*.mmd.

Steps:
  1. Render every diagrams/*.mmd to .svg with @mermaid-js/mermaid-cli (via npx).
  2. Embed each SVG as a base64 data URI into report.html's {{IMG_*}} placeholders,
     writing report_final.html.
  3. Print report_final.html to PDF with a local Chrome via print.js (puppeteer-core).

Requirements (one-time): `npm install puppeteer-core --no-save` in this folder.
Run from anywhere: `python3 build.py`.
"""
from __future__ import annotations

import base64
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIAGRAMS = HERE / "diagrams"
OUT_PDF = HERE.parent / "llm_security_study_notes.pdf"

# (mmd stem, placeholder token in report.html)
DIAGRAM_MAP = [
    ("direct_injection", "IMG_DIRECT"),
    ("indirect_injection", "IMG_INDIRECT"),
    ("persona", "IMG_PERSONA"),
    ("escalation", "IMG_ESCALATION"),
    ("encoding", "IMG_ENCODING"),
    ("credential_pii", "IMG_CREDENTIAL"),
    ("multitenant_rag", "IMG_MULTITENANT"),
    ("memory_poisoning", "IMG_MEMORY"),
    ("prefilter_postfilter", "IMG_PREFILTER"),
    ("role_spoofing", "IMG_ROLESPOOF"),
    ("missing_metadata", "IMG_MISSINGMETA"),
    ("vector_db_prefilter", "IMG_VECTORDB"),
]


def render_diagrams() -> None:
    for stem, _ in DIAGRAM_MAP:
        mmd = DIAGRAMS / f"{stem}.mmd"
        svg = DIAGRAMS / f"{stem}.svg"
        print(f"[mermaid] {mmd.name} -> {svg.name}")
        subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "-i", str(mmd), "-o", str(svg), "-b", "white", "-s", "2"],
            check=True,
        )


def embed_images() -> None:
    html = (HERE / "report.html").read_text(encoding="utf-8")
    for stem, key in DIAGRAM_MAP:
        svg_bytes = (DIAGRAMS / f"{stem}.svg").read_bytes()
        data_uri = "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode("ascii")
        placeholder = "{{" + key + "}}"
        if placeholder not in html:
            raise SystemExit(f"placeholder missing from report.html: {placeholder}")
        html = html.replace(placeholder, data_uri)
    (HERE / "report_final.html").write_text(html, encoding="utf-8")
    print("[embed] wrote report_final.html")


def print_pdf() -> None:
    print(f"[pdf] rendering -> {OUT_PDF}")
    subprocess.run(["node", str(HERE / "print.js"), str(OUT_PDF)], check=True, cwd=str(HERE))


if __name__ == "__main__":
    if "--skip-diagrams" not in sys.argv:
        render_diagrams()
    embed_images()
    print_pdf()

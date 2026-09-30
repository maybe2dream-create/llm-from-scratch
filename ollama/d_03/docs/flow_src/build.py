#!/usr/bin/env python3
"""Build ollama/d_03/docs/방어_코드_흐름도.pdf from report.html + diagrams/*.mmd.

Same pipeline as ollama/docs/study_notes_src/build.py: render mermaid -> embed
as base64 into report.html -> print to PDF with a local Chrome via puppeteer-core.

Reuses the puppeteer-core install from ollama/docs/study_notes_src/node_modules
(set NODE_PATH) instead of installing it again here.
"""
from __future__ import annotations

import base64
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DIAGRAMS = HERE / "diagrams"
OUT_PDF = HERE.parent / "방어_코드_흐름도.pdf"
SHARED_NODE_MODULES = HERE.parent.parent.parent / "docs" / "study_notes_src" / "node_modules"

DIAGRAM_MAP = [
    ("credential_pii_secure", "IMG_CREDENTIAL"),
    ("multitenant_rag_secure", "IMG_MULTITENANT"),
    ("memory_poisoning_secure", "IMG_MEMORY"),
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
    env = os.environ.copy()
    if SHARED_NODE_MODULES.exists():
        env["NODE_PATH"] = str(SHARED_NODE_MODULES)
    subprocess.run(["node", str(HERE / "print.js"), str(OUT_PDF)], check=True, cwd=str(HERE), env=env)


if __name__ == "__main__":
    if "--skip-diagrams" not in sys.argv:
        render_diagrams()
    embed_images()
    print_pdf()

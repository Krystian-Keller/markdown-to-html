#########

# FEITO POR KRYSTIAN KELLER E MAURO MOURA

########

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .builder.standard_html_builder import StandardHtmlBuilder
from .director.diretor import Diretor


def infer_output_path(input_path: Path) -> Path:
    """Deriva o nome do .html a partir do arquivo de entrada."""
    name = input_path.name
    lower = name.lower()
    if lower.endswith(".md"):
        stem = name[:-3]
    elif lower.endswith(".markdown"):
        stem = name[: -len(".markdown")]
    else:
        stem = input_path.stem  # fallback
    return input_path.with_name(f"{stem}.html")


def build_from_file(input_path: Path, mode: str = "full") -> str:
    """
    Executa o pipeline Director + Builder e retorna o HTML como string.
    mode: "full" -> página completa | "body" -> apenas o corpo
    """
    builder = StandardHtmlBuilder()
    diretor = Diretor(builder)  # usa render_inline por padrão
    diretor.parse_file(str(input_path))  # Diretor lê em UTF-8 atualmente

    if mode == "body":
        return builder.get_body()
    return builder.get_full_page()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="markdown-to-html",
        description="Convert a Markdown file to HTML using Builder pattern.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Markdown input file (.md / .markdown)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output HTML file path (defaults to same name with .html)",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--body",
        action="store_true",
        help="Output only the HTML body (no <html>/<head> wrapper).",
    )
    mode.add_argument(
        "--full",
        action="store_true",
        help="Output a complete HTML page (default).",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    parser.add_argument(
        "--output-encoding",
        default="utf-8",
        help="Encoding used to write the output file (default: utf-8).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    input_path: Path = args.input
    if not input_path.exists() or not input_path.is_file():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path: Path = args.output or infer_output_path(input_path)
    if output_path.exists() and not args.force:
        print(
            f"error: output file already exists: {output_path} "
            f"(use --force to overwrite)",
            file=sys.stderr,
        )
        return 1

    mode = "body" if args.body else "full"  # --full é o padrão
    try:
        html = build_from_file(input_path, mode=mode)
    except Exception as e:
        print(f"error: failed to convert '{input_path}': {e}", file=sys.stderr)
        return 1

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding=args.output_encoding)
    except Exception as e:
        print(f"error: failed to write '{output_path}': {e}", file=sys.stderr)
        return 1

    print(f"OK: saved {mode} HTML to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

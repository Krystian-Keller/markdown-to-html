import os
from pathlib import Path
import pytest
from markdown_to_html.builder.standard_html_builder import StandardHtmlBuilder
from markdown_to_html.director.diretor import Diretor

ROOT = Path(__file__).parent
GOLDEN_DIR = ROOT / "golden"
GOLDEN_DIR.mkdir(exist_ok=True)

def _normalize(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def _golden_path(name: str) -> Path:
    return GOLDEN_DIR / name

def _load_golden(name: str) -> str:
    return _normalize(_golden_path(name).read_text(encoding="utf-8"))

def _write_golden(name: str, content: str) -> None:
    _golden_path(name).write_text(content, encoding="utf-8")

@pytest.mark.parametrize(
    "md_text,golden_name",
    [
        (
            # Cenário 1: blocos mistos + inline, com H1 e H2
            "# Roadmap\n"
            "Intro **bold**.\n"
            "\n"
            "- A\n"
            "- B\n"
            "\n"
            "## Next\n"
            "*Italics* here.\n",
            "mixed_blocks_full.html",
        ),
        (
            # Cenário 2: sem H1 (usa fallback "Document"), lista e inline
            "Paragraph one\n"
            "- x\n"
            "- y\n"
            "\n"
            "Another *para*\n",
            "fallback_title_full.html",
        ),
    ],
)
def test_more_full_page_snapshots(md_text, golden_name):
    builder = StandardHtmlBuilder()
    diretor = Diretor(builder)  # usa render_inline padrão

    diretor.parse_text(md_text)
    html = _normalize(builder.get_full_page())

    golden = _golden_path(golden_name)
    update = os.getenv("UPDATE_GOLDEN") == "1"

    if not golden.exists() or update:
        _write_golden(golden_name, html)
        assert html.strip() != ""
    else:
        expected = _load_golden(golden_name)
        assert html == expected

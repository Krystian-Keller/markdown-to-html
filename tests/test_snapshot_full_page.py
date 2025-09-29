import os
from pathlib import Path

import pytest
from builder.standard_html_builder import StandardHtmlBuilder
from director.diretor import Diretor

ROOT = Path(__file__).parent
GOLDEN_DIR = ROOT / "golden"
GOLDEN_DIR.mkdir(exist_ok=True)

def _normalize(s: str) -> str:
    # Normaliza quebras de linha para evitar diferenças por SO
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
            # cobre: título via H1, parágrafo, lista, inline **bold**, *italic*, ***both***
            "# My Doc\n"
            "Intro paragraph with **bold**, *italic*, and ***both***.\n"
            "- item A\n"
            "- item B\n"
            "\n"
            "Closing paragraph.\n",
            "full_page_basic.html",
        ),
    ],
)
def test_full_page_snapshot(md_text, golden_name, monkeypatch):
    # Arrange
    builder = StandardHtmlBuilder()
    diretor = Diretor(builder)  # usa render_inline padrão

    # Act
    diretor.parse_text(md_text)
    html = builder.get_full_page()
    html = _normalize(html)

    golden_exists = _golden_path(golden_name).exists()
    update = os.getenv("UPDATE_GOLDEN") == "1"

    # Assert / Snapshot
    if not golden_exists or update:
        # Atualiza/gera snapshot
        _write_golden(golden_name, html)
        # Verificação mínima para não passar batido por um snapshot vazio
        assert html.strip() != ""
    else:
        expected = _load_golden(golden_name)
        assert html == expected

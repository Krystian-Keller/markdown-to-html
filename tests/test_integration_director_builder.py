import pytest
from builder.standard_html_builder import StandardHtmlBuilder
from director.diretor import Diretor

# 1) E2E simples: heading + parágrafo
def test_integration_heading_and_paragraph():
    b = StandardHtmlBuilder()
    d = Diretor(b)  # usa render_inline padrão
    d.parse_text("# Title\nParagraph\n")

    html = b.get_full_page()
    assert "<title>Title</title>" in html        # título vem do primeiro H1
    assert "<h1>Title</h1>\n" in html
    assert "<p>Paragraph</p>\n" in html

# 2) Lista fecha corretamente e preserva ordem
def test_integration_list_and_paragraph():
    b = StandardHtmlBuilder()
    d = Diretor(b)
    d.parse_text("- a\n- b\n\nafter\n")

    body = b.get_body()
    assert body == "<ul>\n<li>a</li>\n<li>b</li>\n</ul>\n<p>after</p>\n"

# 3) Inline formatting (***, **, *)
def test_integration_inline_bold_italic():
    b = StandardHtmlBuilder()
    d = Diretor(b)
    d.parse_text("**bold** and *it* and ***both***\n")

    body = b.get_body()
    assert "<p><strong>bold</strong> and <em>it</em> and <strong><em>both</em></strong></p>\n" in body

# 4) Título explícito vs H1 (explícito deve vencer)
def test_integration_explicit_title_overrides_first_h1():
    b = StandardHtmlBuilder()
    b.start_document("Explicit")  # simula uso direto — mas vamos via Director:
    # Melhor: usar um Director que passe title=None e rely no H1. Então:
    b = StandardHtmlBuilder()
    d = Diretor(b)
    d.parse_text("# First\n")
    html1 = b.get_full_page()
    assert "<title>First</title>" in html1

    # Agora com título explícito: chamamos start_document manualmente?
    # Mais limpo: simular via Builder diretamente:
    b2 = StandardHtmlBuilder()
    b2.start_document("Explicit")
    b2.add_heading("First", 1)
    b2.end_document()
    html2 = b2.get_full_page()
    assert "<title>Explicit</title>" in html2

# 5) Arquivo real (tmp_path) – smoke test de parse_file
def test_integration_parse_file(tmp_path):
    md = tmp_path / "sample.md"
    md.write_text("# A\n- x\n- y\nZ\n", encoding="utf-8")

    b = StandardHtmlBuilder()
    d = Diretor(b)
    d.parse_file(str(md))

    body = b.get_body()
    assert "<h1>A</h1>\n" in body
    assert "<ul>\n<li>x</li>\n<li>y</li>\n</ul>\n" in body
    assert "<p>Z</p>\n" in body

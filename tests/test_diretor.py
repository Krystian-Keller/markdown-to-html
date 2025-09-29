import pytest
from director.diretor import Diretor
from utils.inline import render_inline


# ---------------------------
# Stubs / Fixtures
# ---------------------------

class DummyBuilder:
    def __init__(self):
        self.calls = []
        self.fragments = []

    def start_document(self, title=None):
        self.calls.append(("start_document", title))

    def end_document(self):
        self.calls.append(("end_document",))

    def start_list(self):
        self.calls.append(("start_list",))

    def add_list_item(self, text):
        self.calls.append(("add_list_item", text))

    def end_list(self):
        self.calls.append(("end_list",))

    def add_heading(self, text, level=1):
        self.calls.append(("add_heading", text, level))

    def add_paragraph(self, text):
        self.calls.append(("add_paragraph", text))
        
    def last_call(self):
        return self.calls[-1] if self.calls else None
    
class TestDiretor:
    
    #---------------------------
    # Test for constructor
    #---------------------------
    
    def test_constructor_sets_builder_and_defaults(self):
        builder = DummyBuilder()
        diretor = Diretor(builder)

        # builder é guardado
        assert diretor.builder is builder

        # inline_renderer padrão é o render_inline
        assert diretor.inline_renderer is render_inline
        assert callable(diretor.inline_renderer)

        # estado inicial da lista
        assert diretor.in_list is False
    
    def test_constructor_accepts_custom_inline_renderer(self):
        builder = DummyBuilder()

        def custom_renderer(s: str) -> str:
            return s.upper()

        diretor = Diretor(builder, inline_renderer=custom_renderer)

        assert diretor.inline_renderer is custom_renderer
        assert diretor.inline_renderer("ok") == "OK"


    # ---------------------------
    # parse_file
    # ---------------------------

    def test_parse_file_reads_and_delegates_to_parse_text(self, monkeypatch, tmp_path):
        builder = DummyBuilder()
        diretor = Diretor(builder)

        content = "A\nB\n"
        p = tmp_path / "exemplo.md"
        p.write_text(content, encoding="utf-8")

        captured = {}

        def fake_parse_text(text):
            captured["text"] = text

        monkeypatch.setattr(diretor, "parse_text", fake_parse_text)

        diretor.parse_file(str(p))

        assert captured["text"] == content


    def test_parse_file_end_to_end(self, tmp_path):
        """Smoke test: garante que parse_file integra com o ciclo do documento."""
        builder = DummyBuilder()
        diretor = Diretor(builder)

        content = "## Subtitulo\nTexto\n"
        p = tmp_path / "exemplo.md"
        p.write_text(content, encoding="utf-8")

        diretor.parse_file(str(p))

        assert builder.calls == [
            ("start_document", None),
            ("add_heading", "Subtitulo", 2),
            ("add_paragraph", "Texto"),
            ("end_document",),
        ]

# ---------------------------
# parse_text
# ---------------------------

def test_parse_text_delegates_to_parse_lines(monkeypatch):
    builder = DummyBuilder()
    diretor = Diretor(builder)

    captured = {}

    def fake_parse_lines(lines):
        captured["lines"] = list(lines)

    monkeypatch.setattr(diretor, "parse_lines", fake_parse_lines)

    text = "linha A\nlinha B\n"
    diretor.parse_text(text)

    assert captured["lines"] == ["linha A", "linha B"]


def test_parse_text_runs_document_lifecycle_with_empty_input():
    builder = DummyBuilder()
    diretor = Diretor(builder)

    diretor.parse_text("")  # sem linhas

    # Deve abrir e encerrar o documento mesmo sem conteúdo
    assert builder.calls == [
        ("start_document", None),
        ("end_document",),
    ]


def test_parse_text_processes_basic_blocks_heading_list_paragraph():
    builder = DummyBuilder()
    diretor = Diretor(builder)

    md = "# Titulo\n- item 1\n- item 2\nParagrafo\n"
    diretor.parse_text(md)

    # Ciclo abre/fecha documento
    assert builder.calls[0] == ("start_document", None)
    assert builder.calls[-1] == ("end_document",)

    # Sequência central esperada (sem se apegar a todos os detalhes)
    middle = builder.calls[1:-1]
    assert middle == [
        ("add_heading", "Titulo", 1),
        ("start_list",),
        ("add_list_item", "item 1"),
        ("add_list_item", "item 2"),
        ("end_list",),
        ("add_paragraph", "Paragrafo"),
    ]


class TestDiretorParseLines:
    def test_parse_lines_empty_input_opens_and_ends(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines([])

        assert builder.calls == [
            ("start_document", None),
            ("end_document",),
        ]

    def test_parse_lines_heading_then_paragraph(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["# Titulo", "Texto"])

        assert builder.calls == [
            ("start_document", None),
            ("add_heading", "Titulo", 1),
            ("add_paragraph", "Texto"),
            ("end_document",),
        ]

    def test_parse_lines_list_opens_adds_and_closes_at_end(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["- a", "- b"])

        assert builder.calls == [
            ("start_document", None),
            ("start_list",),
            ("add_list_item", "a"),
            ("add_list_item", "b"),
            ("end_list",),
            ("end_document",),
        ]

    def test_parse_lines_list_closes_on_blank_line_then_paragraph(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["- item", "", "Depois"])

        assert builder.calls == [
            ("start_document", None),
            ("start_list",),
            ("add_list_item", "item"),
            ("end_list",),                 # fechou na linha em branco
            ("add_paragraph", "Depois"),
            ("end_document",),
        ]

    def test_parse_lines_list_closes_when_heading_appears(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["- x", "## Secao"])

        assert builder.calls == [
            ("start_document", None),
            ("start_list",),
            ("add_list_item", "x"),
            ("end_list",),                 # fechou antes do heading
            ("add_heading", "Secao", 2),
            ("end_document",),
        ]

    def test_parse_lines_allows_leading_indentation_for_markers(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["   - item", "   # Titulo"])

        assert builder.calls == [
            ("start_document", None),
            ("start_list",),
            ("add_list_item", "item"),
            ("end_list",),
            ("add_heading", "Titulo", 1),
            ("end_document",),
        ]

    def test_parse_lines_whitespace_only_line_treated_as_blank(self):
        builder = DummyBuilder()
        diretor = Diretor(builder, inline_renderer=lambda s: s)

        diretor.parse_lines(["- a", "   \t  ", "b"])

        assert builder.calls == [
            ("start_document", None),
            ("start_list",),
            ("add_list_item", "a"),
            ("end_list",),                 # linha só com espaços/tabs fecha lista
            ("add_paragraph", "b"),
            ("end_document",),
        ]

    def test_parse_lines_uses_inline_renderer(self):
        builder = DummyBuilder()
        # renderer simples para evidenciar uso
        diretor = Diretor(builder, inline_renderer=lambda s: f"[{s}]")

        diretor.parse_lines(["# Titulo", "- item", "texto"])

        assert builder.calls == [
            ("start_document", None),
            ("add_heading", "[Titulo]", 1),
            ("start_list",),
            ("add_list_item", "[item]"),
            ("end_list",),
            ("add_paragraph", "[texto]"),
            ("end_document",),
        ]

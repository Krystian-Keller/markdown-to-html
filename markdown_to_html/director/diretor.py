import re
from typing import Iterable, Callable, Optional
from ..utils.inline import render_inline


class Diretor:
    """
    Orquestra a construção do HTML a partir de linhas Markdown,
    chamando os métodos do Builder na ordem correta.

    """

    # Regex pré-compilados para desempenho e legibilidade
    _RE_HEADING = re.compile(r'^(#{1,6})\s+(.*)$')    # "# Título", "## Sub"
    _RE_LIST    = re.compile(r'^[-*]\s+(.*)$')        # "- item" ou "* item"

    def __init__(
        self,
        builder,
        inline_renderer: Optional[Callable[[str], str]] = None,
    ):
        """
        Args:
            builder: instância do Builder (ex.: StandardHtmlBuilder)
            inline_renderer: função de renderização inline (ex.: **…**, *…*).
                             Se None, usa identidade (retorna o texto sem alterações).
        """
        self.builder = builder
        self.inline_renderer = inline_renderer or render_inline
        self.in_list = False  # controla se <ul> está aberta

    # ------------- API pública -------------

    def parse_file(self, path_arquivo: str) -> None:
        """I/O fino: lê arquivo e delega para parse_text()."""
        with open(path_arquivo, encoding="utf-8") as f:
            self.parse_text(f.read())

    def parse_text(self, text: str) -> None:
        """Recebe todo o conteúdo como string e delega para parse_lines()."""
        self.parse_lines(text.splitlines())

    def parse_lines(self, lines: Iterable[str]) -> None:
        """
        Núcleo da orquestração (sem I/O).
        - Abre o documento
        - Varre linhas (heading > lista > parágrafo)
        - Fecha estruturas no fim
        - Encerra o documento
        """
        self._start_document()

        for raw_line in lines:
            # remove somente o \n final para preservar espaços à esquerda quando necessário
            line = raw_line.rstrip("\n")

            # linha “efetivamente” vazia?
            if not line.strip():
                self._close_list_if_open()
                continue

            # tolera indentação simples para a análise
            view = line.lstrip()

            # 1) Heading?
            m = self._RE_HEADING.match(view)
            if m:
                self._handle_heading(m)
                continue

            # 2) Item de lista?
            m = self._RE_LIST.match(view)
            if m:
                self._handle_list_item(m)
                continue

            # 3) Caso contrário, é parágrafo (linha única - MVP)
            self._handle_paragraph_line(view)

        # fim das linhas → fecha estruturas remanescentes e encerra documento
        self._close_list_if_open()
        self._end_document()

    # ------------- Helpers privados -------------

    def _start_document(self) -> None:
        self.builder.start_document(title=None)

    def _end_document(self) -> None:
        self.builder.end_document()

    def _close_list_if_open(self) -> None:
        if self.in_list:
            self.builder.end_list()
            self.in_list = False

    def _handle_heading(self, match: re.Match) -> None:
        # Fechar lista antes de heading garante HTML válido
        self._close_list_if_open()

        hashes = match.group(1)
        level = len(hashes)
        text = match.group(2).strip()

        text = self.inline_renderer(text)
        self.builder.add_heading(text, level)

    def _handle_list_item(self, match: re.Match) -> None:
        text = match.group(1).strip()
        text = self.inline_renderer(text)

        if not self.in_list:
            self.builder.start_list()
            self.in_list = True

        self.builder.add_list_item(text)

    def _handle_paragraph_line(self, line: str) -> None:
        # Fechar lista antes de parágrafo garante HTML válido
        self._close_list_if_open()

        text = self.inline_renderer(line.strip())
        self.builder.add_paragraph(text)

    # ------------- Compat (opcional) -------------

    def construir(self, path_arquivo: str) -> None:

        self.parse_file(path_arquivo)

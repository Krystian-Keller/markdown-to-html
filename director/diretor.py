import re

class Diretor:
    def __init__(self, builder):
        self.builder = builder
        self.patterns = [
            (re.compile(r'^(#{1,6})\s+(.*)$'), self._build_heading),   # títulos
            (re.compile(r'^[-*]\s+(.*)$'), self._build_list_item),    # listas
            (re.compile(r'^(?!#|[-*])(.+)$'), self._build_paragraph), # parágrafos
        ]
        self.in_list = False  # controle para start/end list

    def construir(self, path_arquivo):
        with open(path_arquivo, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue

                for pattern, action in self.patterns:
                    match = pattern.match(line)
                    if match:
                        action(match)
                        break

        # se terminou ainda dentro de lista, fecha
        if self.in_list:
            self.builder.end_list()
            self.in_list = False

    # ===== Métodos auxiliares =====
    def _build_heading(self, match):
        nivel = len(match.group(1))
        texto = match.group(2).strip()
        self.builder.build_heading(texto, nivel)

    def _build_list_item(self, match):
        texto = match.group(1).strip()
        if not self.in_list:
            self.builder.start_list()
            self.in_list = True
        self.builder.build_list_item(texto)

    def _build_paragraph(self, match):
        if self.in_list:
            self.builder.end_list()
            self.in_list = False
        texto = match.group(1).strip()
        self.builder.build_paragraph(texto)
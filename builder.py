class HtmlBuilder:
    def __init__(self):
        self.html = []
        self.html.append("<html>")
        self.html.append("  <body>")

    def build_heading(self, texto, nivel):
        self.html.append(f"    <h{nivel}>{texto}</h{nivel}>")

    def build_paragraph(self, texto):
        self.html.append(f"    <p>{texto}</p>")

    def start_list(self):
        self.html.append("    <ul>")

    def build_list_item(self, texto):
        self.html.append(f"      <li>{texto}</li>")

    def end_list(self):
        self.html.append("    </ul>")

    def get_result(self):
        self.html.append("  </body>")
        self.html.append("</html>")
        return "\n".join(self.html)
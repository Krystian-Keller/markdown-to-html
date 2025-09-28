from builder.html_builder import HTMLBuilder

class StandardHtmlBuilder(HTMLBuilder):
    """
    Concrete implementation of HtmlBuilder.

    This builder accumulates HTML fragments step by step to construct
    a complete HTML document from parsed Markdown content.

    Responsibilities:
    - Manage internal state of the document (started/ended, open lists, etc.).
    - Collect body fragments as headings, paragraphs, and lists are added.
    - Handle inline formatting (bold, italic, bold+italic).
    - Provide methods to retrieve either the body-only or the full HTML page
      (with <!DOCTYPE html>, <html>, <head>, <title>, and <body>).

    Notes:
    - `start_document()` must be called before adding content.
    - `end_document()` finalizes the building process.
    - `get_body()` returns only the body fragments.
    - `get_full_page()` wraps the body in a complete HTML page.
    """
    
    def start_document(self, title: str = None):
        
        self._doc_started = True
        self._doc_ended = False
        self._fragments = []
        self._list_open = False
        self._explicit_title = title
        self._first_h1_title = None
        
        return super().start_document(title)
    

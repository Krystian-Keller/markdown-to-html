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
    
  def start_document(self, title: str = None) -> None:
    self._doc_started = True
    self._doc_ended = False
    self._fragments = []
    self._list_open = False
    self._explicit_title = title
    self._first_h1_title = None
    
    
  def end_document(self) -> None:
    """
    Finalize the current document.

    Responsibilities:
    - Close any still-open structures (e.g., an <ul> list).
    - Seal the builder so no further content can be added.
    - Does NOT return HTML nor write files; use get_body()/get_full_page() for output.

    Rules:
    - Must be called only after start_document(); otherwise raises RuntimeError.
    - Not idempotent: calling it twice raises RuntimeError.
    - After ending, any add_* or start_*/end_* content methods must raise RuntimeError.

    Raises:
    - RuntimeError: if called before start_document() or if the document was already ended.
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    # Close any open <ul> to ensure valid HTML
    if self._list_open:
        self._fragments.append("</ul>\n")
        self._list_open = False

    # Seal the document
    self._doc_ended = True
    
  def add_heading(self, text: str, level: int = 1) -> None:
    """
    Add a heading element (<h1> to <h6>) to the document.

    Responsibilities:
    - Insert an HTML heading at the requested level.
    - Capture the first <h1> as a fallback <title> if none was explicitly provided.

    Args:
    - text (str): The heading text.
    - level (int): The heading level (1-6). Defaults to 1.

    Raises:
    - RuntimeError: if called before start_document() or after end_document().
    - ValueError: if level is not between 1 and 6.
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    if not (1 <= level <= 6):
        raise ValueError("heading level must be between 1 and 6")

    if level == 1 and self._first_h1_title is None and self._explicit_title is None:
        self._first_h1_title = text

    if self._list_open:
        self._fragments.append("</ul>\n")
        self._list_open = False

    self._fragments.append(f"<h{level}>{text}</h{level}>\n")
  
  def start_list(self) -> None:
    """
    Open an unordered list (<ul>) block.

    Responsibilities:
    - Push "<ul>\n" into the fragments buffer.
    - Mark the internal state as list-open.

    Rules:
    - Must be called after start_document() and before end_document().
    - Raises RuntimeError if called before a document starts or after it ends.
    - Raises RuntimeError if a list is already open (nested lists not supported yet).

    Raises:
    - RuntimeError: "document not started" | "document already ended" | "list already open"
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    if getattr(self, "_list_open", False):
        raise RuntimeError("list already open")

    self._fragments.append("<ul>\n")
    self._list_open = True
  
  def add_list_item(self, text: str) -> None:
    """
    Add an item (<li>) to the currently open unordered list.

    Responsibilities:
    - Append "<li>{text}</li>\n" to the fragments buffer.
    - Require that a <ul> has been opened with start_list().

    Args:
    - text (str): The list item content. Can be empty, resulting in <li></li>.

    Rules:
    - Must be called after start_document() and before end_document().
    - Raises RuntimeError if called before a document starts or after it ends.
    - Raises RuntimeError if no list is currently open.

    Raises:
    - RuntimeError: "document not started" | "document already ended" | "no open list to add item"
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    if not getattr(self, "_list_open", False):
        raise RuntimeError("no open list to add item")

    self._fragments.append(f"<li>{text}</li>\n")
    
  def end_list(self) -> None:
    """
    Close the currently open unordered list (<ul>).

    Responsibilities:
    - Append "</ul>\n" to the fragments buffer.
    - Mark the internal state as list-closed.

    Rules:
    - Must be called after start_document() and before end_document().
    - Raises RuntimeError if called before a document starts or after it ends.
    - Raises RuntimeError if no list is currently open (non-idempotent).

    Raises:
    - RuntimeError: "document not started" | "document already ended" | "no open list to end"
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    if not getattr(self, "_list_open", False):
        raise RuntimeError("no open list to end")

    self._fragments.append("</ul>\n")
    self._list_open = False
    
  def add_paragraph(self, text: str) -> None:
    """
    Add a paragraph (<p>...</p>) to the document.

    Responsibilities:
    - Append "<p>{text}</p>\n" to the fragments buffer.
    - If a <ul> is open, close it before adding the paragraph (valid HTML flow).

    Args:
    - text (str): The paragraph content. Can be empty, resulting in <p></p>.

    Rules:
    - Must be called after start_document() and before end_document().
    - Raises RuntimeError if called before a document starts or after it ends.
    - If a list is open, it is automatically closed before adding the paragraph.

    Raises:
    - RuntimeError: "document not started" | "document already ended"
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    if getattr(self, "_doc_ended", False):
        raise RuntimeError("document already ended")

    if getattr(self, "_list_open", False):
        self._fragments.append("</ul>\n")
        self._list_open = False

    self._fragments.append(f"<p>{text}</p>\n")
  
  def get_body(self) -> str:
    """
    Return the accumulated HTML body as a single string.

    Responsibilities:
    - Join the internal fragments buffer into a single string.
    - Provide a read-only view of the body content (no side effects).

    Rules:
    - Must be called after start_document(); otherwise raises RuntimeError.
    - May be called after end_document() (read-only).
    - Does NOT auto-close structures (e.g., open <ul>); it reflects current state.

    Returns:
    - str: The concatenated HTML body.
    """
    if not getattr(self, "_doc_started", False):
        raise RuntimeError("document not started")

    # No mutation here: purely read-only
    return "".join(self._fragments)

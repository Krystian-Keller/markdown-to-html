import re

def render_inline(text: str) -> str:
    """
    Convert basic Markdown inline markers to HTML.
    Supports:
      - ***text*** -> <strong><em>text</em></strong>
      - **text**   -> <strong>text</strong>
      - *text*     -> <em>text</em>
    Escapes HTML special chars (&, <, >) in the user text while preserving generated tags.
    Allows literal asterisks with backslash: \* -> *

    Notes:
    - Precedence: *** ... *** first, then ** ... **, then * ... *.
    - Non-greedy to allow multiple spans in the same line.
    - Does not handle code spans/backticks; if needed, add that later and
      skip inline formatting inside them.
    """
    if not text:
        return ""

    # 1) Protect escaped asterisks so they aren't treated as markers
    AST = "\x01AST\x02"
    s = re.sub(r"\\\*", AST, text)

    # 2) Placeholders for tags to avoid escaping them later
    TR_OPEN, TR_CLOSE = "\x01TRI_OPEN\x02", "\x01TRI_CLOSE\x02"
    DB_OPEN, DB_CLOSE = "\x01B_OPEN\x02",  "\x01B_CLOSE\x02"
    SG_OPEN, SG_CLOSE = "\x01I_OPEN\x02",  "\x01I_CLOSE\x02"

    # 3) Insert placeholders by precedence: *** → ** → *
    #    Non-greedy (.+?) so multiple segments work on a single line.
    #    We don't escape content yet; we will escape once after placeholders are in place.
    s = re.sub(r"\*\*\*(.+?)\*\*\*", rf"{TR_OPEN}\1{TR_CLOSE}", s)
    s = re.sub(r"\*\*(.+?)\*\*",     rf"{DB_OPEN}\1{DB_CLOSE}", s)
    s = re.sub(r"\*(.+?)\*",         rf"{SG_OPEN}\1{SG_CLOSE}", s)

    # 4) Escape HTML special chars in the remaining text (not the placeholders)
    def _html_escape(u: str) -> str:
        # order matters: escape & first
        u = u.replace("&", "&amp;")
        u = u.replace("<", "&lt;").replace(">", "&gt;")
        return u

    s = _html_escape(s)

    # 5) Replace placeholders with real tags
    s = (s
         .replace(TR_OPEN, "<strong><em>")
         .replace(TR_CLOSE, "</em></strong>")
         .replace(DB_OPEN, "<strong>")
         .replace(DB_CLOSE, "</strong>")
         .replace(SG_OPEN, "<em>")
         .replace(SG_CLOSE, "</em>")
    )

    # 6) Restore escaped asterisks as literal '*'
    s = s.replace(AST, "*")

    return s
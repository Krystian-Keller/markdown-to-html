# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from builder.standard_html_builder import StandardHtmlBuilder

class TestStandardHTMLBuilder:
    
    StandardHtmlBuilder.__abstractmethods__ = frozenset()
    
    #---------------------------
    # Test for start_document()
    #---------------------------
    
    def test_start_document(self):
        builder = StandardHtmlBuilder()    
        
        result = builder.start_document('Test Title')
        
        assert builder._doc_started is True
        assert builder._doc_ended is False
        assert builder._fragments == []
        assert builder._list_open is False
        assert builder._explicit_title == 'Test Title'
        assert builder._first_h1_title is None
        
    #---------------------------
    # Test for end_document()
    #---------------------------
    
    def test_end_document_basic(self):
        builder = StandardHtmlBuilder()
        builder.start_document('Test Title')
        
        builder.end_document()
        
        assert builder._doc_ended is True
        assert builder._list_open is False
        
    def test_end_document_without_start(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.end_document()
        
    def test_end_document_twice(self):
        builder = StandardHtmlBuilder()
        builder.start_document('Test Title')
        builder.end_document()
        
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.end_document()
    
    def test_end_document_closes_open_list(self):
        builder = StandardHtmlBuilder()
        builder.start_document('Test Title')
        
        builder._list_open = True
        builder._fragments.append("<ul>")
        builder.end_document()
        
        assert builder._list_open is False
        assert builder._fragments[-1] == "</ul>\n" or "</ul>\n" in "".join(builder._fragments)
        
    def test_end_document_after_reset_state(self):
        builder = StandardHtmlBuilder()
        builder.start_document('Test Title A')
        builder._fragments.append("<h1>Title A</h1>")
        builder.end_document()
        
        builder.start_document('Test Title B')
        
        assert builder._doc_started is True
        assert builder._doc_ended is False
        assert builder._fragments == []
        assert builder._list_open is False
        assert builder._explicit_title == 'Test Title B'
        assert builder._first_h1_title is None
        
    
    #---------------------------
    # Test for add_heading()
    #---------------------------
    
    def test_add_heading_h1_default_level(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("Main Title")  # default level = 1

        assert builder._fragments[-1] == "<h1>Main Title</h1>\n"

    def test_add_heading_h2_and_h3(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("Section", level=2)
        builder.add_heading("Subsection", level=3)

        html = "".join(builder._fragments)
        assert "<h2>Section</h2>" in html
        assert "<h3>Subsection</h3>" in html

    def test_add_heading_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.add_heading("Main Title", level=1)

    def test_add_heading_after_end_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.end_document()
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.add_heading("Main Title", level=1)

    def test_add_heading_invalid_level_low(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        with pytest.raises(ValueError, match="heading level must be between 1 and 6"):
            builder.add_heading("Main Title", level=0)

    def test_add_heading_invalid_level_high(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        with pytest.raises(ValueError, match="heading level must be between 1 and 6"):
            builder.add_heading("Section", level=7)

    def test_add_heading_closes_open_list(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        # simula lista aberta: Hardcode
        builder._list_open = True
        builder._fragments.append("<ul>")
        builder._fragments.append("<li>item</li>")

        builder.add_heading("Next Section", level=2)

        html = "".join(builder._fragments)
        # deve ter fechado a lista antes do <h2>
        assert "</ul>\n<h2>Next Section</h2>" in html
        assert builder._list_open is False

    def test_first_h1_sets_title_when_no_explicit_title(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("First H1", level=1)

        assert builder._first_h1_title == "First H1"

    def test_first_h1_not_used_if_explicit_title_exists(self):
        builder = StandardHtmlBuilder()
        builder.start_document("Main Title")
        builder.add_heading("First H1", level=1)

        assert builder._explicit_title == "Main Title"
        assert builder._first_h1_title is None

    def test_first_h1_captured_only_once(self):
        builder = StandardHtmlBuilder()
        builder.start_document() 
        builder.add_heading("First", level=1)
        builder.add_heading("Second", level=1)

        assert builder._first_h1_title == "First"  # não deve sobrescrever
        html = "".join(builder._fragments)
        assert "<h1>First</h1>" in html and "<h1>Second</h1>" in html

    def test_add_multiple_headings_order_is_preserved(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("A", 1)
        builder.add_heading("B", 2)
        builder.add_heading("C", 3)

        assert builder._fragments == [
            "<h1>A</h1>\n",
            "<h2>B</h2>\n",
            "<h3>C</h3>\n",
        ]
        
    #---------------------------
    # Test for start_list()
    #---------------------------
    
    def test_start_list_opens_ul(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.start_list()

        assert builder._list_open is True
        assert builder._fragments[-1] == "<ul>\n"
        assert builder._doc_started is True
        assert builder._doc_ended is False

    def test_start_list_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.start_list()

    def test_start_list_after_end_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.end_document()
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.start_list()

    def test_start_list_twice_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.start_list()
        with pytest.raises(RuntimeError, match="list already open"):
            builder.start_list()

    def test_start_list_then_heading_closes_list(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.start_list()
        # simulate at least one item to make it realistic ### HARDCODED
        builder._fragments.append("<li>item</li>\n")

        builder.add_heading("Next Section", level=2)

        html = "".join(builder._fragments)
        assert "</ul>\n<h2>Next Section</h2>\n" in html
        assert builder._list_open is False

    def test_start_list_does_not_create_li_automatically(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.start_list()

        # Deve haver apenas a abertura do <ul>, nenhum <li> automático
        assert builder._fragments[-1] == "<ul>\n"
        assert not any("<li>" in frag for frag in builder._fragments)

    #---------------------------
    # Test for add_list_item()
    #---------------------------
    
    def test_add_list_item_appends_li(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()

        builder.add_list_item("Item A")

        assert builder._list_open is True
        assert builder._fragments[-1] == "<li>Item A</li>\n"

    def test_add_list_item_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.add_list_item("X")

    def test_add_list_item_after_end_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.end_document()
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.add_list_item("X")

    def test_add_list_item_without_open_list_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        with pytest.raises(RuntimeError, match="no open list to add item"):
            builder.add_list_item("X")

    def test_add_list_item_multiple_items_preserve_order(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()

        builder.add_list_item("A")
        builder.add_list_item("B")

        assert builder._fragments[-2:] == ["<li>A</li>\n", "<li>B</li>\n"]

    def test_add_list_item_allows_empty_text(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()

        builder.add_list_item("")

        assert builder._fragments[-1] == "<li></li>\n"

    #---------------------------
    # Test for end_list()
    #---------------------------

    def test_end_list_closes_ul(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()

        builder.end_list()

        assert builder._list_open is False
        assert builder._fragments[-1] == "</ul>\n"

    def test_end_list_with_items(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.add_list_item("A")
        builder.add_list_item("B")

        builder.end_list()

        html = "".join(builder._fragments)
        assert "<ul>\n<li>A</li>\n<li>B</li>\n</ul>\n" in html
        assert builder._list_open is False

    def test_end_list_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.end_list()

    def test_end_list_after_end_document_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.end_document()
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.end_list()

    def test_end_list_without_open_list_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        with pytest.raises(RuntimeError, match="no open list to end"):
            builder.end_list()

    def test_end_list_twice_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.end_list()

        with pytest.raises(RuntimeError, match="no open list to end"):
            builder.end_list()

    def test_after_end_list_other_blocks_do_not_reclose(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.add_list_item("x")
        builder.end_list()

        # Agora adicionar um heading não deve tentar fechar lista de novo
        builder.add_heading("Next Topic", level=2)
        html = "".join(builder._fragments)
        assert html.count("</ul>") == 1
        assert "</ul>\n<h2>Next Topic</h2>\n" in html
    
    #---------------------------
    # Test for add_paragraph()
    #---------------------------

    def test_add_paragraph_basic(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.add_paragraph("Hello World")

        assert builder._fragments[-1] == "<p>Hello World</p>\n"

    def test_add_paragraph_multiple_preserve_order(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.add_paragraph("First")
        builder.add_paragraph("Second")

        assert builder._fragments[-2:] == ["<p>First</p>\n", "<p>Second</p>\n"]

    def test_add_paragraph_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.add_paragraph("X")

    def test_add_paragraph_after_end_raises(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.end_document()
        with pytest.raises(RuntimeError, match="document already ended"):
            builder.add_paragraph("X")

    def test_add_paragraph_closes_open_list(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.add_list_item("A")

        builder.add_paragraph("After list")

        html = "".join(builder._fragments)
        assert "</ul>\n<p>After list</p>\n" in html
        assert builder._list_open is False

    def test_add_paragraph_allows_empty_text(self):
        builder = StandardHtmlBuilder()
        builder.start_document()

        builder.add_paragraph("")

        assert builder._fragments[-1] == "<p></p>\n"
    
    #---------------------------
    # Test for get_body()
    #---------------------------

    def test_get_body_basic(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("A", level=1)

        body = builder.get_body()

        assert body == "<h1>A</h1>\n"

    def test_get_body_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.get_body()

    def test_get_body_after_end_document_returns_content(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_paragraph("x")
        builder.end_document()

        body = builder.get_body()

        assert body == "<p>x</p>\n"

    def test_get_body_is_read_only_does_not_close_open_list(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.add_list_item("item")

        # Snapshot dos fragments antes
        before = "".join(builder._fragments)

        body = builder.get_body()

        # Não deve fechar a lista nem alterar fragments
        assert builder._list_open is True
        assert body == before
        assert "".join(builder._fragments) == before

    def test_get_body_preserves_order(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("A", 1)
        builder.add_paragraph("B")
        builder.start_list()
        builder.add_list_item("C")
        builder.end_list()

        body = builder.get_body()

        assert body == "<h1>A</h1>\n<p>B</p>\n<ul>\n<li>C</li>\n</ul>\n"
    
    #---------------------------
    # Test for get_full_page()
    #---------------------------

    def test_get_full_page_basic_structure(self):
        builder = StandardHtmlBuilder()
        builder.start_document("My Title")
        builder.add_paragraph("Hello")

        html = builder.get_full_page()

        assert html.startswith("<!DOCTYPE html>")
        assert "<html>" in html and "</html>" in html
        assert "<head>" in html and "</head>" in html
        assert '<meta charset="utf-8">' in html
        assert "<body>" in html and "</body>" in html
        assert "<p>Hello</p>\n" in html
        assert "<title>My Title</title>" in html

    def test_get_full_page_title_from_first_h1_when_no_explicit_title(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_heading("First H1", level=1)
        builder.add_paragraph("Content")

        html = builder.get_full_page()

        assert "<title>First H1</title>" in html
        assert "<h1>First H1</h1>\n" in html
        assert "<p>Content</p>\n" in html

    def test_get_full_page_fallback_title_when_no_title_and_no_h1(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.add_paragraph("Only content")

        html = builder.get_full_page()

        assert "<title>Document</title>" in html
        assert "<p>Only content</p>\n" in html

    def test_get_full_page_before_start_raises(self):
        builder = StandardHtmlBuilder()
        with pytest.raises(RuntimeError, match="document not started"):
            builder.get_full_page()

    def test_get_full_page_after_end_document_is_allowed(self):
        builder = StandardHtmlBuilder()
        builder.start_document("Done")
        builder.add_paragraph("x")
        builder.end_document()

        html = builder.get_full_page()

        assert "<title>Done</title>" in html
        assert "<p>x</p>\n" in html

    def test_get_full_page_does_not_mutate_state(self):
        builder = StandardHtmlBuilder()
        builder.start_document()
        builder.start_list()
        builder.add_list_item("A")

        # Snapshot of state before
        list_open_before = builder._list_open
        fragments_before = "".join(builder._fragments)

        html = builder.get_full_page()

        # State must be unchanged
        assert builder._list_open is list_open_before
        assert "".join(builder._fragments) == fragments_before

        # Body content must be embedded as-is
        assert "<ul>\n<li>A</li>\n" in html  # list still open inside body snapshot

    def test_get_full_page_preserves_body_order(self):
        builder = StandardHtmlBuilder()
        builder.start_document("Order")
        builder.add_heading("A", 1)
        builder.add_paragraph("B")
        builder.start_list()
        builder.add_list_item("C")
        builder.end_list()

        html = builder.get_full_page()

        body_seq = "<h1>A</h1>\n<p>B</p>\n<ul>\n<li>C</li>\n</ul>\n"
        assert body_seq in html
        assert "<title>Order</title>" in html

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
        assert builder._fragments[-1] == "</ul>" or "</ul>" in "".join(builder._fragments)
        
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

        
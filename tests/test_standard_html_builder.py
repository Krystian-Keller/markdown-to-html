# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from builder.standard_html_builder import StandardHtmlBuilder

class TestStandardHTMLBuilder:
    
    StandardHtmlBuilder.__abstractmethods__ = frozenset()
    
    def test_start_document(self):
        builder = StandardHtmlBuilder()    
        
        result = builder.start_document('Test Title')
        
        assert builder._doc_started is True
        assert builder._doc_ended is False
        assert builder._fragments == []
        assert builder._list_open is False
        assert builder._explicit_title == 'Test Title'
        assert builder._first_h1_title is None
    
        
from abc import ABC, abstractmethod


class HTMLBuilder(ABC):
    
    @abstractmethod
    def start_document(self, title=None):
        pass
    
    @abstractmethod
    def end_document(self):
        pass
    
    @abstractmethod
    def add_heading(self, text, level):
        pass
    
    @abstractmethod
    def start_list(self):
        pass
    
    @abstractmethod
    def add_list_item(self, text):
        pass
    
    def end_list(self):
        pass
    
    def add_paragraph(self, text):
        pass
    
    def get_body(self):
        pass
    
    @abstractmethod
    def get_full_page(self):
        pass
    
    
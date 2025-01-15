from typing import Optional
import re
from html import escape
import tiktoken
import streamlit as st

class InputProcessor:
    """
    Handles processing, validation, and sanitization of user input.
    
    Attributes:
        encoding: The tokenizer encoding for token counting
        max_tokens: Maximum allowed tokens for input
    """
    
    def __init__(self, max_tokens: int = 4000):
        """
        Initialize the InputProcessor.
        
        Args:
            max_tokens (int): Maximum number of tokens allowed in input
        """
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = max_tokens
        
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input by removing harmful characters and HTML.
        
        Args:
            text (str): Raw user input
            
        Returns:
            str: Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        text = escape(text)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        text = ' '.join(text.split())
        return text
    
    def validate_length(self, text: str) -> bool:
        """
        Check if input is within acceptable token limits.
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if length is acceptable
        """
        num_tokens = len(self.encoding.encode(text))
        return num_tokens < self.max_tokens
    
    def validate_content(self, text: str) -> bool:
        """
        Check if input contains actual content.
        
        Args:
            text (str): Text to validate
            
        Returns:
            bool: True if content is valid
        """
        return len(text.strip()) > 0 and not text.isspace()
    
    def process_input(self, text: str) -> Optional[str]:
        """
        Process and validate user input.
        
        Args:
            text (str): Raw user input
            
        Returns:
            Optional[str]: Processed text or None if invalid
        """
        try:
            if not self.validate_content(text):
                st.error("Please enter a valid question.")
                return None
                
            cleaned_text = self.sanitize_input(text)
            
            if not self.validate_length(cleaned_text):
                st.error("Input is too long. Please shorten your question.")
                return None
                
            return cleaned_text
            
        except Exception as e:
            st.error(f"Error processing input: {str(e)}")
            return None 
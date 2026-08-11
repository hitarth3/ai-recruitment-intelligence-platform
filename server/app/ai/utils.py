"""
AI Module Utilities.
Provides JSON response cleaning, markdown formatting, and safe text extraction.
"""

import re
import json
from app.utils.logger import logger


def clean_markdown_text(text: str) -> str:
    """
    Cleans up confusing LaTeX formatting, escaped symbols, and redundant symbols.
    Ensures clear, readable markdown text.
    """
    if not text:
        return ""
    
    # Strip raw LaTeX arrow and math syntax
    cleaned = re.sub(r'\\rightarrow|\\to|\$\\rightarrow\$', '→', text)
    cleaned = re.sub(r'\$([^\$]+)\$', r'\1', cleaned)  # Strip inline LaTeX math dollars
    cleaned = cleaned.replace('\r\n', '\n')
    
    return cleaned.strip()


def parse_json_from_ai_response(response_text: str) -> dict:
    """
    Extracts and parses JSON object from AI text response even if wrapped in ```json ... ``` code blocks.
    """
    if not response_text:
        return {}
    
    try:
        # Check for ```json ... ``` code block
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if match:
            json_str = match.group(1)
        else:
            json_str = response_text
        
        return json.loads(json_str.strip())
    except Exception as e:
        logger.warning(f"Failed to parse JSON from AI response: {e}")
        return {}

"""
Logo Generator Module

This module provides functionality to create text watermarks for PDF documents.
It no longer generates image watermarks, instead focusing on text-based watermarks
that are applied directly in the HTML/CSS.
"""

def get_text_watermark():
    """
    Returns the text to be used as a watermark.
    
    Returns:
        str: The text watermark string
    """
    return "CurrentAdda"

def get_watermark_css():
    """
    Returns the CSS for styling the text watermark.
    
    Returns:
        str: CSS styling for the text watermark
    """
    return """
    .text-watermark {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-size: 6rem;
        color: rgba(37, 99, 235, 0.06);
        font-weight: 800;
        white-space: nowrap;
        z-index: -1;
        pointer-events: none;
    }
    """

def get_watermark_html():
    """
    Returns the HTML for the text watermark.
    
    Returns:
        str: HTML for the text watermark
    """
    return f'<div class="text-watermark">{get_text_watermark()}</div>' 
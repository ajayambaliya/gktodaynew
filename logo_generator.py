"""
Logo Generator Module

This module provides functionality to create text watermarks for PDF documents.
It no longer generates image watermarks, instead focusing on text-based watermarks
that are applied directly in the HTML/CSS.
"""
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

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

def generate_logo(output_dir=None, filename=None):
    """
    For backward compatibility - creates a transparent PNG with the CurrentAdda text.
    
    Args:
        output_dir (str, optional): Directory to save the logo. Defaults to current directory.
        filename (str, optional): Filename for the logo. Defaults to currentadda_logo.png.
    
    Returns:
        str: Path to the generated logo file
    """
    # Set defaults
    if output_dir is None:
        output_dir = os.getcwd()
    
    if filename is None:
        filename = "currentadda_logo.png"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a transparent image
    width, height = 500, 200
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        font_size = 48
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fall back to default font if arial is not available
            font = ImageFont.load_default()
            
        text = "CurrentAdda"
        
        # Handle different versions of PIL/Pillow
        try:
            # For newer Pillow versions
            if hasattr(font, "getbbox"):
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            # For older Pillow versions
            else:
                text_width, text_height = draw.textsize(text, font=font)
        except:
            # Fallback if both methods fail
            text_width, text_height = width // 2, height // 2
            
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        # Add text to the image with a blue color
        draw.text(position, text, fill=(59, 130, 246, 128), font=font)
    except Exception as e:
        print(f"Warning: Could not add text to logo: {str(e)}")
    
    # Save the image
    output_path = os.path.join(output_dir, filename)
    image.save(output_path)
    
    print(f"Logo generated at: {output_path}")
    return output_path 
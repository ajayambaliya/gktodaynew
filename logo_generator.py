from PIL import Image, ImageDraw, ImageFont
import os

def generate_logo(output_path, size=(300, 300), bg_color=(37, 99, 235), text_color=(255, 255, 255)):
    """
    Generate a simple logo for CurrentAdda
    
    Args:
        output_path: Path to save the logo
        size: Size of the logo image (width, height)
        bg_color: Background color in RGB
        text_color: Text color in RGB
        
    Returns:
        Path to the generated logo
    """
    # Create a new image with a solid background
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        # Try to load a bold font if available
        font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'Arial.ttf')
        if os.path.exists(font_path):
            font_large = ImageFont.truetype(font_path, size=int(size[0] * 0.2))
            font_small = ImageFont.truetype(font_path, size=int(size[0] * 0.1))
        else:
            # Fall back to default
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw the logo text
    text = "CA"
    text_width, text_height = draw.textsize(text, font=font_large) if hasattr(draw, 'textsize') else (size[0] * 0.4, size[1] * 0.4)
    
    # Position text in center
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2
    
    # Draw text
    draw.text((x, y), text, font=font_large, fill=text_color)
    
    # Draw a circle around the text
    padding = size[0] * 0.1
    circle_x = size[0] / 2
    circle_y = size[1] / 2
    circle_radius = min(size[0], size[1]) / 2 - padding
    
    # Draw circle
    draw.ellipse(
        (circle_x - circle_radius, circle_y - circle_radius, 
         circle_x + circle_radius, circle_y + circle_radius),
        outline=text_color, width=3
    )
    
    # Add "CurrentAdda" text at the bottom
    bottom_text = "CurrentAdda"
    bottom_width, bottom_height = draw.textsize(bottom_text, font=font_small) if hasattr(draw, 'textsize') else (size[0] * 0.8, size[1] * 0.1)
    bottom_x = (size[0] - bottom_width) / 2
    bottom_y = size[1] - bottom_height - padding
    
    draw.text((bottom_x, bottom_y), bottom_text, font=font_small, fill=text_color)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the image
    img.save(output_path)
    print(f"Logo saved to {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Generate logo
    output_path = os.path.join("templates", "currentadda_logo.png")
    generate_logo(output_path) 
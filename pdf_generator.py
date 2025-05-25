from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
from config import TEMPLATE_DIR, PDF_OUTPUT_DIR
import sys
import shutil

def create_modern_pdf(articles, titles, output_filename=None):
    """
    Generate a modern PDF from the given articles using Jinja2 templates and WeasyPrint.
    Falls back to HTML export if WeasyPrint is not available.
    
    Args:
        articles: List of article dictionaries with content
        titles: List of article titles for the cover page
        output_filename: Optional filename for the PDF
    
    Returns:
        Path to the generated PDF or HTML file
    """
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('pdf_template.html')
    
    # Generate filename if not provided
    if not output_filename:
        date_str = datetime.now().strftime('%d-%m-%Y')
        output_filename = f"{date_str}_Current_Affairs"
    
    # Ensure output directory exists
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    
    # Copy QR code to output directory
    qr_src = os.path.join(TEMPLATE_DIR, "telegram_qr.png")
    qr_dst = os.path.join(PDF_OUTPUT_DIR, "telegram_qr.png")
    if os.path.exists(qr_src):
        shutil.copy2(qr_src, qr_dst)
    
    # Copy logo to output directory
    logo_src = os.path.join(TEMPLATE_DIR, "currentadda_logo.png")
    logo_dst = os.path.join(PDF_OUTPUT_DIR, "currentadda_logo.png")
    if os.path.exists(logo_src):
        shutil.copy2(logo_src, logo_dst)
    
    # Create CSS directory if it doesn't exist
    css_dir = os.path.join(TEMPLATE_DIR, 'css')
    css_output_dir = os.path.join(PDF_OUTPUT_DIR, 'css')
    os.makedirs(css_output_dir, exist_ok=True)
    
    # Copy CSS files to output directory
    if os.path.exists(css_dir):
        for css_file in ['base.css', 'components.css', 'layout.css', 'pdf.css']:
            src = os.path.join(css_dir, css_file)
            if os.path.exists(src):
                dst = os.path.join(css_output_dir, css_file)
                shutil.copy2(src, dst)
    
    # Prepare context data for the template with absolute paths
    current_date = datetime.now().strftime('%d %B %Y')
    context = {
        'date': current_date,
        'current_year': datetime.now().year,
        'articles': articles,
        'titles': titles,
        'logo_path': os.path.abspath(logo_dst).replace('\\', '/'),
        'qr_path': os.path.abspath(qr_dst).replace('\\', '/')
    }
    
    # Render HTML
    html_content = template.render(**context)
    
    try:
        # Try to import WeasyPrint and generate PDF
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Temporary HTML file with absolute paths
        temp_html_path = os.path.join(PDF_OUTPUT_DIR, f"temp_{output_filename}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Get CSS files with absolute paths
        css_files = [
            os.path.join(css_output_dir, 'base.css'),
            os.path.join(css_output_dir, 'components.css'),
            os.path.join(css_output_dir, 'layout.css'),
            os.path.join(css_output_dir, 'pdf.css')
        ]
        
        # Load CSS files
        css_list = [CSS(filename, font_config=font_config) for filename in css_files if os.path.exists(filename)]
        
        # Generate PDF
        pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.pdf")
        HTML(filename=temp_html_path).write_pdf(pdf_path, stylesheets=css_list, font_config=font_config)
        
        # Clean up temporary file
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        print(f"Modern PDF created: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"WeasyPrint error: {str(e)}")
        print("Falling back to HTML export...")
        
        # Save as HTML instead
        html_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML file created: {html_path}")
        return html_path 
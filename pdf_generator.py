from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
from config import TEMPLATE_DIR, PDF_OUTPUT_DIR
import sys

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
    
    # Prepare context data for the template
    current_date = datetime.now().strftime('%d %B %Y')
    context = {
        'date': current_date,
        'current_year': datetime.now().year,
        'articles': articles,
        'titles': titles
    }
    
    # Render HTML
    html_content = template.render(**context)
    
    # Generate filename if not provided
    if not output_filename:
        date_str = datetime.now().strftime('%d-%m-%Y')
        output_filename = f"{date_str}_Current_Affairs"
    
    # Ensure output directory exists
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    
    try:
        # Try to import WeasyPrint and generate PDF
        from weasyprint import HTML, CSS
        pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.pdf")
        HTML(string=html_content).write_pdf(pdf_path)
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
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
from config import TEMPLATE_DIR, PDF_OUTPUT_DIR
import sys
import shutil
from logo_generator import get_text_watermark
import re

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
    
    # Copy FontAwesome if available
    fa_src = os.path.join(TEMPLATE_DIR, "fontawesome.min.css")
    fa_dst = os.path.join(PDF_OUTPUT_DIR, "fontawesome.min.css")
    if os.path.exists(fa_src):
        shutil.copy2(fa_src, fa_dst)
    
    # Copy FontAwesome webfonts if available
    webfonts_src = os.path.join(TEMPLATE_DIR, "webfonts")
    webfonts_dst = os.path.join(PDF_OUTPUT_DIR, "webfonts")
    if os.path.exists(webfonts_src):
        if os.path.exists(webfonts_dst):
            shutil.rmtree(webfonts_dst)
        shutil.copytree(webfonts_src, webfonts_dst)
    
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
    
    # Process articles to remove duplicate navigation content
    processed_articles = []
    for article in articles:
        # Create a copy of the article to avoid modifying the original
        processed_article = article.copy()
        
        # Filter out navigation content blocks (Home, Current Affairs Today, etc.)
        if 'content' in processed_article:
            filtered_content = []
            for block in processed_article['content']:
                # Skip navigation items that match the title or standard navigation text
                if block.get('type') == 'paragraph' and block.get('text'):
                    text = block.get('text', '').strip()
                    
                    # Skip breadcrumb navigation
                    if text.startswith('•Home') or text.startswith('•Current Affairs Today'):
                        continue
                        
                    # Skip if it's just the title repeated
                    if text == f"•{processed_article.get('english_title')}" or \
                       text == f"•{processed_article.get('gujarati_title')}":
                        continue
                    
                    # Skip post meta information
                    if re.search(r'•\s*\d+\s*\w+\s*\d{4}', text) or \
                       'Current Affairs Today - Current Affairs -' in text:
                        continue
                
                filtered_content.append(block)
            processed_article['content'] = filtered_content
        
        processed_articles.append(processed_article)
    
    # Count total pages for page numbering
    total_pages = len(processed_articles) + 1  # +1 for cover page
    
    # Prepare context data for the template with absolute paths
    current_date = datetime.now().strftime('%d %B %Y')
    context = {
        'date': current_date,
        'current_year': datetime.now().year,
        'articles': processed_articles,
        'titles': titles,
        'qr_path': os.path.abspath(qr_dst).replace('\\', '/'),
        'watermark_text': get_text_watermark(),
        'total_pages': total_pages
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
        
        # Add FontAwesome CSS if available
        if os.path.exists(fa_dst):
            css_files.append(fa_dst)
        
        # Load CSS files
        css_list = [CSS(filename, font_config=font_config) for filename in css_files if os.path.exists(filename)]
        
        # Add Google Fonts CSS for Gujarati text
        gujarati_fonts_css = CSS(string="""
            @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Gujarati:wght@400;500;600;700&family=Hind+Vadodara:wght@400;500;600;700&display=swap');
            
            .gujarati-text, .gujarati-title, .gujarati-heading {
                font-family: 'Noto Serif Gujarati', 'Hind Vadodara', serif;
            }
        """, font_config=font_config)
        css_list.append(gujarati_fonts_css)
        
        # Add FontAwesome CSS if file doesn't exist
        if not os.path.exists(fa_dst):
            fontawesome_css = CSS(string="""
                @font-face {
                    font-family: 'FontAwesome';
                    src: url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/webfonts/fa-solid-900.woff2') format('woff2');
                    font-weight: 900;
                    font-style: normal;
                }
                
                .fa {
                    font-family: 'FontAwesome';
                    font-weight: 900;
                }
                
                .fa-telegram:before { content: "\\f2c6"; }
                .fa-check:before { content: "\\f00c"; }
                .fa-clock:before { content: "\\f017"; }
                .fa-language:before { content: "\\f1ab"; }
                .fa-file-pdf:before { content: "\\f1c1"; }
            """, font_config=font_config)
            css_list.append(fontawesome_css)
        
        # Add page counter CSS
        page_counter_css = CSS(string=f"""
            @page {{
                @bottom-right {{
                    content: "Page " counter(page) " of {total_pages}";
                }}
            }}
        """)
        css_list.append(page_counter_css)
        
        # Generate PDF with proper page counter
        pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.pdf")
        HTML(filename=temp_html_path).write_pdf(
            pdf_path, 
            stylesheets=css_list, 
            font_config=font_config,
            presentational_hints=True
        )
        
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
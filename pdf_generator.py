from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime
from config import TEMPLATE_DIR, PDF_OUTPUT_DIR
import sys
import shutil
import re
from logo_generator import get_text_watermark

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
    
    # Process articles to remove duplicate navigation content and post meta
    processed_articles = []
    for article in articles:
        # Create a copy of the article to avoid modifying the original
        processed_article = article.copy()
        
        # Filter out navigation content blocks and post meta
        if 'content' in processed_article:
            filtered_content = []
            for block in processed_article['content']:
                # Skip blocks we want to filter
                if should_filter_block(block, processed_article):
                    continue
                filtered_content.append(block)
            processed_article['content'] = filtered_content
        
        processed_articles.append(processed_article)
    
    # Estimate total pages for pagination
    # A rough estimate based on content size
    total_pages = estimate_total_pages(processed_articles)
    
    # Add 1 extra page if we need a continuation page for many articles
    if len(titles) > 14:
        total_pages += 1
    
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
    
    # Save HTML file for debugging or fallback
    html_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Define PDF path
    pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{output_filename}.pdf")
    
    # DIRECT FIX: Check for the problematic byte 0xAB in the file
    try:
        print("Checking for problematic bytes before PDF generation...")
        with open(html_path, 'rb') as f:
            content = f.read()
            
        # Check if file starts with the problematic byte
        if content.startswith(b'\xab'):
            print("Found problematic byte 0xAB at start of file, removing it...")
            with open(html_path, 'wb') as f:
                f.write(content[1:])
        
        # Check for any 0xAB bytes anywhere in the file
        if b'\xab' in content:
            print(f"Found {content.count(b'\xab')} instances of problematic byte 0xAB in file, cleaning...")
            content = content.replace(b'\xab', b'')
            with open(html_path, 'wb') as f:
                f.write(content)
                
        # Ensure the file starts with proper doctype
        if not content.startswith(b'<!DOCTYPE html>') and not content.startswith(b'<html'):
            print("File doesn't start with proper HTML doctype, fixing...")
            with open(html_path, 'wb') as f:
                f.write(b'<!DOCTYPE html>\n' + content)
                
        print("File preparation complete, proceeding with PDF generation...")
    except Exception as e:
        print(f"Error during file preparation: {str(e)}")
    
    try:
        # Try to import WeasyPrint and generate PDF
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Configure fonts
        font_config = FontConfiguration()
        
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
        
        # Try a completely different approach: use subprocess to call wkhtmltopdf
        try:
            print("Attempting PDF generation using wkhtmltopdf...")
            import subprocess
            
            # Check if wkhtmltopdf is installed
            try:
                subprocess.run(['wkhtmltopdf', '--version'], check=True, capture_output=True)
                wkhtmltopdf_available = True
            except (subprocess.SubprocessError, FileNotFoundError):
                print("wkhtmltopdf not available, installing...")
                # Try to install wkhtmltopdf
                try:
                    subprocess.run(['apt-get', 'update'], check=True)
                    subprocess.run(['apt-get', 'install', '-y', 'wkhtmltopdf'], check=True)
                    wkhtmltopdf_available = True
                except subprocess.SubprocessError:
                    print("Failed to install wkhtmltopdf")
                    wkhtmltopdf_available = False
            
            if wkhtmltopdf_available:
                # Generate PDF using wkhtmltopdf
                cmd = ['wkhtmltopdf', '--encoding', 'utf-8', html_path, pdf_path]
                result = subprocess.run(cmd, check=True, capture_output=True)
                
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
                    print(f"PDF successfully generated using wkhtmltopdf: {pdf_path}")
                    return pdf_path
                else:
                    print("wkhtmltopdf did not produce a valid PDF, falling back to WeasyPrint")
        except Exception as wk_error:
            print(f"wkhtmltopdf approach failed: {str(wk_error)}")
        
        # Try direct string-based rendering instead of file-based
        print("Attempting direct HTML string rendering...")
        try:
            # Read the HTML file directly to avoid encoding issues
            with open(html_path, 'rb') as f:
                html_bytes = f.read()
                
            # Try to decode with different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    html_content = html_bytes.decode(encoding)
                    print(f"Successfully decoded HTML with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all decodings fail, use a brute force approach
                print("All decodings failed, using brute force approach")
                html_content = html_bytes.decode('utf-8', errors='replace')
            
            # Generate PDF with proper page counter using string-based approach
            document = HTML(string=html_content, base_url=os.path.dirname(html_path)).render(stylesheets=css_list, font_config=font_config)
            
            # Get actual page count
            actual_pages = len(document.pages)
            
            # Update context with actual page count
            context['total_pages'] = actual_pages
            
            # Re-render HTML with accurate page count
            html_content = template.render(**context)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate final PDF with string-based approach
            document = HTML(string=html_content, base_url=os.path.dirname(html_path)).render(stylesheets=css_list, font_config=font_config)
            document.write_pdf(pdf_path)
                
            print(f"Modern PDF created using string-based approach: {pdf_path}")
            return pdf_path
        except Exception as string_error:
            print(f"String-based rendering failed: {str(string_error)}")
            print("Falling back to file-based rendering with encoding handling...")
            
            # Check for BOM in the HTML file
            with open(html_path, 'rb') as f:
                content = f.read()
                has_bom = content.startswith(b'\xef\xbb\xbf')
                if has_bom:
                    print("Warning: HTML file has BOM marker, removing it...")
                    with open(html_path, 'wb') as f_out:
                        f_out.write(content[3:])
                        
                # Check for any problematic bytes at the start
                if content.startswith(b'\xab'):
                    print("Found problematic byte 0xAB at start of file, cleaning...")
                    with open(html_path, 'wb') as f_out:
                        # Skip the problematic byte
                        f_out.write(content[1:])
                
                # Debug: print the first 20 bytes of the file
                print(f"First 20 bytes of HTML file: {content[:20]}")
            
            # Try with explicit file encoding
            document = HTML(filename=html_path, base_url=os.path.dirname(html_path), encoding='utf-8').render(stylesheets=css_list, font_config=font_config)
            
            # Get actual page count and regenerate with correct total
            actual_pages = len(document.pages)
            
            # Update context with actual page count
            context['total_pages'] = actual_pages
            
            # Re-render HTML with accurate page count
            html_content = template.render(**context)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Generate final PDF with explicit encoding
            document = HTML(filename=html_path, base_url=os.path.dirname(html_path), encoding='utf-8').render(stylesheets=css_list, font_config=font_config)
            document.write_pdf(pdf_path)
                
            print(f"Modern PDF created with file-based approach: {pdf_path}")
            return pdf_path
    except UnicodeDecodeError as ude:
        print(f"WeasyPrint encoding error: {str(ude)}")
        print("Trying with different encoding...")
        try:
            # Try with a different encoding
            document = HTML(filename=html_path, base_url=os.path.dirname(html_path), encoding='latin-1').render(stylesheets=css_list, font_config=font_config)
            document.write_pdf(pdf_path)
            print(f"PDF created with alternate encoding: {pdf_path}")
            return pdf_path
        except Exception as e2:
            print(f"Failed with alternate encoding: {str(e2)}")
            
            # Last resort: try to sanitize the HTML file
            try:
                print("Attempting to sanitize HTML file...")
                with open(html_path, 'rb') as f:
                    content = f.read()
                
                # Replace any problematic bytes
                sanitized = bytearray()
                for byte in content:
                    # Skip any non-ASCII control characters except common whitespace
                    if byte >= 32 or byte in (9, 10, 13):  # tab, newline, carriage return
                        sanitized.append(byte)
                
                # Write sanitized content
                with open(html_path, 'wb') as f:
                    f.write(sanitized)
                
                # Try one more time with sanitized content
                document = HTML(filename=html_path, base_url=os.path.dirname(html_path)).render(stylesheets=css_list, font_config=font_config)
                document.write_pdf(pdf_path)
                print(f"PDF created after sanitizing HTML: {pdf_path}")
                return pdf_path
            except Exception as e3:
                print(f"Failed after sanitizing HTML: {str(e3)}")
                
                # Absolute last resort: Try to use a completely different PDF generation approach
                try:
                    print("Attempting PDF generation using pdfkit...")
                    import pdfkit
                    
                    # Try to install wkhtmltopdf if not already installed
                    try:
                        import subprocess
                        subprocess.run(['apt-get', 'update'], check=True)
                        subprocess.run(['apt-get', 'install', '-y', 'wkhtmltopdf'], check=True)
                    except:
                        pass
                    
                    # Try to generate PDF using pdfkit
                    pdfkit.from_file(html_path, pdf_path)
                    
                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
                        print(f"PDF successfully generated using pdfkit: {pdf_path}")
                        return pdf_path
                except Exception as pk_error:
                    print(f"pdfkit approach failed: {str(pk_error)}")
                
                print("Falling back to HTML export...")
                return html_path
    except Exception as e:
        print(f"WeasyPrint error: {str(e)}")
        print("Falling back to HTML export...")
        
        # Return the HTML path as fallback
        print(f"HTML file created: {html_path}")
        return html_path

def should_filter_block(block, article):
    """
    Determine if a content block should be filtered out.
    
    Args:
        block: The content block to check
        article: The article containing the block
    
    Returns:
        bool: True if the block should be filtered out, False otherwise
    """
    if not block.get('type') == 'paragraph' or not block.get('text'):
        return False
    
    text = block.get('text', '').strip()
    
    # Filter navigation breadcrumbs
    if text.startswith('•Home') or text.startswith('•Current Affairs Today'):
        return True
    
    # Filter article title that appears in the navigation
    if text == f"•{article.get('english_title')}" or text == f"•{article.get('gujarati_title')}":
        return True
    
    # Filter post meta information
    if ('calendar' in text.lower() and 'folder' in text.lower()) or re.search(r'\d{1,2} [A-Za-z]+ \d{4}', text):
        return True
    
    # Filter post-meta div content
    if 'post-meta' in text.lower() or 'post-date' in text.lower() or 'post-categories' in text.lower():
        return True
    
    # Filter breadcrumb navigation
    if ('breadcrumb' in text.lower() or 'itemscope' in text.lower() or 'schema.org' in text.lower() or 
        'itemprop' in text.lower()):
        return True
    
    # Filter any content with fa icons typically used in metadata
    if 'fa fa-calendar' in text.lower() or 'fa fa-folder' in text.lower():
        return True
    
    return False

def estimate_total_pages(articles):
    """
    Estimate the total number of pages based on content.
    
    Args:
        articles: List of processed articles
    
    Returns:
        int: Estimated number of pages
    """
    # Start with 1 for the cover page
    estimated_pages = 1
    
    # Rough estimate: each article takes about 1-2 pages depending on content
    for article in articles:
        content_length = 0
        if 'content' in article:
            content_length = len(article['content'])
        
        # Basic heuristic: longer content = more pages
        if content_length <= 3:
            estimated_pages += 1
        elif content_length <= 8:
            estimated_pages += 2
        else:
            estimated_pages += 3
    
    # Add 1 for the channel promotion and footer
    estimated_pages += 1
    
    return estimated_pages 
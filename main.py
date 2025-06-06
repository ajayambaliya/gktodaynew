import asyncio
import os
from datetime import datetime
from config import BASE_URL, PAGE_COUNT, PDF_OUTPUT_DIR, TEMPLATE_DIR, MONGODB_DATABASE, MONGODB_COLLECTION
from scraper import fetch_article_urls, get_all_articles
from pdf_generator import create_modern_pdf
from telegram_sender import send_pdf_to_telegram
from qr_generator import generate_qr_code
from logo_generator import generate_logo
from db_utils import get_mongodb_connection

def extract_topics_from_articles(articles, max_topics=5):
    """
    Extract main topics from article titles for the Telegram caption.
    
    Args:
        articles: List of article dictionaries
        max_topics: Maximum number of topics to extract
        
    Returns:
        List of topic strings
    """
    topics = []
    
    # Extract English titles as topics
    for article in articles:
        if 'english_title' in article and article['english_title']:
            # Clean up the title - remove any special formatting
            topic = article['english_title'].strip()
            topics.append(topic)
            
            # Stop once we have enough topics
            if len(topics) >= max_topics:
                break
    
    return topics

async def main():
    """Main function to run the PDF generation and Telegram sending process."""
    try:
        print("Starting Current Affairs PDF generation...")
        
        # Check MongoDB connection
        client, collection = get_mongodb_connection()
        if client is None or collection is None:
            print(f"Warning: MongoDB connection failed. Make sure MONGODB_URI is set in .env file and points to a valid MongoDB instance.")
            print(f"MongoDB database: {MONGODB_DATABASE}, collection: {MONGODB_COLLECTION}")
            print("Proceeding without URL tracking.")
        else:
            print(f"MongoDB connection successful. Using database: {MONGODB_DATABASE}, collection: {MONGODB_COLLECTION}")
            client.close()
        
        # Fetch article URLs with the improved workflow
        print(f"Fetching and comparing article URLs from {BASE_URL} (up to {PAGE_COUNT} pages)...")
        urls = fetch_article_urls(BASE_URL, PAGE_COUNT)
        
        if not urls:
            print("No URLs found to process.")
            return
        
        print(f"Found {len(urls)} URLs to process.")
        
        # Scrape articles
        articles, titles = await get_all_articles(urls)
        
        if not articles:
            print("No articles scraped successfully.")
            return
        
        print(f"Successfully scraped {len(articles)} articles.")
        
        # Generate PDF filename with date
        date_str = datetime.now().strftime('%d-%m-%Y')
        output_filename = f"{date_str}_Current_Affairs"
        
        # Create PDF
        file_path = create_modern_pdf(articles, titles, output_filename)
        
        if not file_path:
            print("Failed to generate PDF.")
            return
        
        # Check if we have a PDF version (WeasyPrint might have returned HTML path as fallback)
        pdf_path = file_path
        if file_path.lower().endswith('.html'):
            possible_pdf = file_path.replace('.html', '.pdf')
            if os.path.exists(possible_pdf):
                print(f"Using PDF version instead of HTML: {possible_pdf}")
                pdf_path = possible_pdf
        
        # Verify PDF file is valid and not empty
        if pdf_path.lower().endswith('.pdf'):
            try:
                file_size = os.path.getsize(pdf_path)
                if file_size < 1000:  # Less than 1KB is suspicious for a PDF
                    print(f"Warning: PDF file is suspiciously small ({file_size} bytes), might be corrupted")
                    # Fall back to HTML if PDF seems invalid
                    html_path = file_path if file_path.lower().endswith('.html') else file_path.replace('.pdf', '.html')
                    if os.path.exists(html_path) and os.path.getsize(html_path) > 1000:
                        print(f"Falling back to HTML file: {html_path}")
                        pdf_path = html_path
                else:
                    print(f"PDF file verified: {file_size} bytes")
            except Exception as e:
                print(f"Error verifying PDF file: {str(e)}")
        
        print(f"File to be sent: {pdf_path}")
        
        # Send to Telegram
        success = await send_pdf_to_telegram(pdf_path, topics=titles)
        
        if success:
            print("PDF sent to Telegram successfully.")
        else:
            print("Failed to send PDF to Telegram.")
            
    except Exception as e:
        print(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 
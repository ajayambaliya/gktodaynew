import asyncio
import os
from datetime import datetime
from config import BASE_URL, PAGE_COUNT, PDF_OUTPUT_DIR, TEMPLATE_DIR
from scraper import fetch_article_urls, get_all_articles
from pdf_generator import create_modern_pdf
from telegram_sender import send_pdf_to_telegram
from qr_generator import generate_qr_code

async def main():
    """Main function to orchestrate the entire process."""
    try:
        print("Starting CurrentAdda PDF generation process...")
        
        # Create output directory if it doesn't exist
        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
        
        # Generate QR code for Telegram channel
        print("Generating Telegram QR code...")
        telegram_url = "https://t.me/CurrentAdda"
        qr_path = os.path.join(TEMPLATE_DIR, "telegram_qr.png")
        generate_qr_code(telegram_url, qr_path)
        
        # Step 1: Fetch article URLs
        print(f"Fetching article URLs from {BASE_URL}...")
        article_urls = fetch_article_urls(BASE_URL, PAGE_COUNT)
        print(f"Found {len(article_urls)} articles")
        
        if not article_urls:
            raise Exception("No article URLs found")
        
        # Step 2: Process articles
        print("Processing articles...")
        articles, titles = await get_all_articles(article_urls)
        
        if not articles:
            raise Exception("No article content could be processed")
        
        print(f"Successfully processed {len(articles)} articles")
        
        # Step 3: Generate PDF
        print("Generating PDF...")
        current_date = datetime.now().strftime('%d-%m-%Y')
        output_filename = f"{current_date}_Current_Affairs"
        output_path = create_modern_pdf(articles, titles, output_filename)
        
        # Step 4: Send to Telegram
        print("Sending output to Telegram...")
        caption = f"Current Affairs for {datetime.now().strftime('%d %B %Y')}\n\nFollow @CurrentAdda for daily updates!"
        success = await send_pdf_to_telegram(output_path, caption)
        
        if success:
            print("Process completed successfully!")
        else:
            print("Process completed but failed to send to Telegram")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 
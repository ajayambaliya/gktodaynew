import os
from telegram import Bot
import asyncio
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL

async def send_pdf_to_telegram(file_path, caption=None):
    """
    Send PDF or HTML file to Current Adda Telegram channel.
    
    Args:
        file_path: Path to the PDF or HTML file to send
        caption: Optional caption for the document
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get token from environment variable or config
        bot_token = TELEGRAM_BOT_TOKEN
        # Current Adda channel ID
        channel_id = TELEGRAM_CHANNEL
        
        if not bot_token:
            raise ValueError("Bot token is missing from environment variables")
        
        # Generate default caption if not provided
        if not caption:
            current_date = datetime.now().strftime('%d %B %Y')
            caption = f"Current Affairs for {current_date}\n\nFollow @CurrentAdda for daily updates!"
        
        # Initialize bot
        bot = Bot(token=bot_token)
        telegram_caption_limit = 1024
        
        # Check file type
        is_html = file_path.lower().endswith('.html')
        
        # Send file
        with open(file_path, 'rb') as file:
            if len(caption) > telegram_caption_limit:
                short_caption = caption[:telegram_caption_limit-3] + "..."
                await bot.send_document(
                    chat_id=channel_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=short_caption
                )
                await bot.send_message(chat_id=channel_id, text=caption)
            else:
                await bot.send_document(
                    chat_id=channel_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=caption
                )
        
        file_type = "HTML" if is_html else "PDF"
        print(f"{file_type} sent successfully to {channel_id}")
        return True
        
    except Exception as e:
        print(f"Error sending file to Telegram: {str(e)}")
        return False 
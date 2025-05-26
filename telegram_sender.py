import os
from telegram import Bot
import asyncio
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL

async def send_pdf_to_telegram(file_path, caption=None, topics=None):
    """
    Send PDF or HTML file to Current Adda Telegram channel with a beautifully formatted caption.
    If both PDF and HTML files exist with the same name, prioritize the PDF.
    
    Args:
        file_path: Path to the PDF or HTML file to send
        caption: Optional caption for the document
        topics: Optional list of topics covered in the document
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get token from environment variable or config
        bot_token = TELEGRAM_BOT_TOKEN
        if not bot_token:
            raise ValueError("Bot token is missing from environment variables")
        
        # Current Adda channel ID
        channel_id = TELEGRAM_CHANNEL
        
        # Check if we have a PDF version of the file
        pdf_path = file_path
        if file_path.lower().endswith('.html'):
            pdf_path = file_path.replace('.html', '.pdf')
            if os.path.exists(pdf_path):
                print(f"Found PDF version, using {pdf_path} instead of {file_path}")
                file_path = pdf_path
        
        # Ensure the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Check file size (Telegram limit is 50MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:
            print(f"Warning: File size ({file_size_mb:.2f} MB) exceeds Telegram's 50MB limit")
            
        # Telegram caption limit
        telegram_caption_limit = 1024
        
        # Format current date
        current_date = datetime.now().strftime('%d %B %Y')
        
        # Create a beautifully formatted caption with emojis
        if not caption:
            caption = format_telegram_caption(current_date, topics)
        
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Check file type
        is_html = file_path.lower().endswith('.html')
        file_type = "HTML" if is_html else "PDF"
        
        print(f"Sending {file_type} file: {file_path}")
        print(f"To channel: {channel_id}")
        
        # Send file
        with open(file_path, 'rb') as file:
            if len(caption) > telegram_caption_limit:
                # Create a shortened caption that fits the limit but keeps the important parts
                short_caption = create_shortened_caption(caption, telegram_caption_limit)
                
                await bot.send_document(
                    chat_id=channel_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=short_caption,
                    parse_mode="HTML"
                )
                
                # Send remaining content as a separate message if needed
                remaining = caption[len(short_caption):]
                if remaining.strip():
                    await bot.send_message(
                        chat_id=channel_id, 
                        text=remaining,
                        parse_mode="HTML"
                    )
            else:
                await bot.send_document(
                    chat_id=channel_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=caption,
                    parse_mode="HTML"
                )
        
        print(f"{file_type} sent successfully to {channel_id}")
        return True
        
    except Exception as e:
        print(f"Error sending file to Telegram: {str(e)}")
        return False

def format_telegram_caption(date, topics=None):
    """
    Create a beautifully formatted caption for Telegram with emojis and proper formatting.
    
    Args:
        date: The date string
        topics: Optional list of topics covered
        
    Returns:
        Formatted caption string
    """
    # Start with a header
    caption = f"<b>📚 CURRENT AFFAIRS</b> | <b>{date}</b>\n\n"
    
    # Add topics section if topics are provided
    if topics and len(topics) > 0:
        caption += "<b>🔍 TODAY'S HIGHLIGHTS:</b>\n"
        
        # Display first 5 topics
        max_topics_to_show = 5
        for i, topic in enumerate(topics[:max_topics_to_show], 1):
            caption += f"{i}. {topic}\n"
        
        # Add a note if there are more topics
        remaining_topics = len(topics) - max_topics_to_show
        if remaining_topics > 0:
            caption += f"\n<b>+ {remaining_topics} more articles in the PDF</b>\n"
        
        caption += "\n"
    
    # Add call to action
    caption += "<b>📲 JOIN OUR CHANNEL:</b>\n"
    caption += "• @CurrentAdda\n"
    caption += "• Daily Current Affairs updates\n"
    caption += "• Comprehensive coverage in Gujarati & English\n\n"
    
    caption += "#CurrentAffairs #DailyUpdate #UPSC #GPSC #talati"
    
    return caption

def create_shortened_caption(caption, limit):
    """
    Create a shortened version of the caption that fits within the Telegram limit
    but preserves the most important parts.
    
    Args:
        caption: The original caption
        limit: The character limit
        
    Returns:
        Shortened caption
    """
    # First, try to find the join channel section
    join_index = caption.find("<b>📲 JOIN OUR CHANNEL:</b>")
    
    if join_index > 0:
        # Keep the header and the join section
        header = caption[:caption.find("\n\n") + 2]  # Keep the header and first newline
        join_section = caption[join_index:]
        
        # Calculate remaining space
        remaining_space = limit - len(header) - len(join_section) - 3  # 3 for ellipsis
        
        if remaining_space > 50:  # Only if we have reasonable space
            middle_content = caption[len(header):join_index].strip()
            if len(middle_content) > remaining_space:
                middle_content = middle_content[:remaining_space] + "..."
            
            return header + middle_content + "\n\n" + join_section
    
    # Fallback: simple truncation with priority to the end (join section)
    if len(caption) > limit:
        # Preserve at least 200 chars from the end which should include the join info
        end_preserve = min(300, len(caption) // 3)
        available = limit - end_preserve - 3  # 3 for ellipsis
        
        if available > 100:  # Only if we have reasonable space at the beginning
            return caption[:available] + "...\n\n" + caption[-end_preserve:]
        else:
            # Just truncate from the beginning if we can't preserve both parts well
            return caption[:limit-3] + "..."
    
    return caption 
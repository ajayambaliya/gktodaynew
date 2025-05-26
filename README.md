# CurrentAdda PDF Generator

A Python application that automatically scrapes current affairs articles from GKToday, translates them to Gujarati, generates a beautiful PDF, and sends it to a Telegram channel.

## Features

- **Bilingual Content**: Articles are presented in both Gujarati and English
- **Modern PDF Design**: Professional magazine-style layout with responsive design
- **Automatic Scraping**: Fetches the latest articles from GKToday
- **MongoDB Integration**: Stores scraped URLs to avoid duplicates and ensure fresh content
- **Telegram Integration**: Automatically sends the PDF to a Telegram channel with a formatted caption
- **Responsive Highlights**: Cover page adapts based on the number of articles
- **Continuation Pages**: Handles large numbers of articles elegantly

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gktodayapp.git
   cd gktodayapp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```
   # Telegram Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHANNEL=@YourChannelName

   # MongoDB Configuration
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

4. Generate QR code for your Telegram channel:
   ```
   python qr_generator.py
   ```

## Usage

Run the main script to generate and send the PDF:

```
python main.py
```

## Configuration

Edit `config.py` to customize:

- Number of pages to scrape
- Base URL for scraping
- Output directories
- MongoDB database and collection names

## Dependencies

- WeasyPrint: PDF generation
- Jinja2: HTML templating
- BeautifulSoup4: Web scraping
- Python-Telegram-Bot: Telegram integration
- PyMongo: MongoDB integration
- Deep-Translator: Gujarati translation

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
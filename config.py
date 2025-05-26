import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (local development)
load_dotenv()

# Configuration settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = "@CurrentAdda"
BASE_URL = "https://www.gktoday.in/current-affairs/"
PAGE_COUNT = 3  # Number of pages to scrape

# PDF Generation settings
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
PDF_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Create output directory if it doesn't exist
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# MongoDB configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DATABASE = 'gktodayappnew'
MONGODB_COLLECTION = 'scraped_urls' 

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (local development)
load_dotenv()

# Configuration settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = "@gujtest1"
BASE_URL = "https://www.gktoday.in/current-affairs/"
PAGE_COUNT = 4  # Number of pages to scrape

# PDF Generation settings
PDF_OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"

# Create output directory if it doesn't exist
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True) 

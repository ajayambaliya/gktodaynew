import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists (local development)
load_dotenv()

# Configuration settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@CurrentAdda")
BASE_URL = "https://www.gktoday.in/current-affairs/"
PAGE_COUNT = 3  # Number of pages to scrape

# PDF Generation settings
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
PDF_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Create output directory if it doesn't exist
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# MongoDB configuration
# Try to get MongoDB URI from environment variables with multiple possible names
# GitHub Actions might use different environment variable names
MONGODB_URI = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI')

# Print debug info about environment variables (without exposing sensitive info)
print(f"Environment variables check:")
print(f"- MONGODB_URI is {'set' if os.environ.get('MONGODB_URI') else 'not set'}")
print(f"- MONGO_URI is {'set' if os.environ.get('MONGO_URI') else 'not set'}")

# Fixed database and collection names as per requirements
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'gktodayappnew')
MONGODB_COLLECTION = os.environ.get('MONGODB_COLLECTION', 'scraped_urls')

# Print the database and collection names
print(f"MongoDB configuration:")
print(f"- Database: {MONGODB_DATABASE}")
print(f"- Collection: {MONGODB_COLLECTION}")
print(f"- Connection URI: {'Available' if MONGODB_URI else 'Not available'}")

if not MONGODB_URI:
    print("WARNING: MongoDB URI environment variable not found. MongoDB features will not work.")
    print("Please set MONGODB_URI in your environment variables or .env file.")
    # Provide a fallback for development/testing
    MONGODB_URI = "mongodb://localhost:27017/"
    print(f"Using fallback MongoDB URI: {MONGODB_URI}")

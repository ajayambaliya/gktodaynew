import pymongo
from datetime import datetime
from config import MONGODB_URI, MONGODB_DATABASE, MONGODB_COLLECTION

def get_mongodb_connection():
    """
    Establish a connection to MongoDB and return the collection for scraped URLs.
    
    Returns:
        tuple: (client, collection) - MongoDB client and collection objects
    """
    try:
        # Check if MONGODB_URI is set
        if not MONGODB_URI:
            print("MongoDB URI is not set. Please set the MONGODB_URI environment variable.")
            return None, None
        
        # Connect to MongoDB using the URI from environment variables
        # Set serverSelectionTimeoutMS to reduce connection timeout
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Ping the server to verify connection
        client.admin.command('ping')
        
        db = client[MONGODB_DATABASE]
        collection = db[MONGODB_COLLECTION]
        
        # Create an index on the URL field for faster lookups
        collection.create_index([("url", pymongo.ASCENDING)], unique=True)
        
        print(f"Connected to MongoDB: {MONGODB_DATABASE}.{MONGODB_COLLECTION}")
        return client, collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return None, None

def save_scraped_url(collection, url):
    """
    Save a scraped URL to the MongoDB collection.
    
    Args:
        collection: MongoDB collection
        url: URL to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create document with URL and timestamp
        document = {
            "url": url,
            "scraped_at": datetime.now(),
        }
        
        # Insert or update the document (upsert)
        collection.update_one(
            {"url": url},
            {"$set": document},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving URL to MongoDB: {str(e)}")
        return False

def is_url_scraped(collection, url):
    """
    Check if a URL has already been scraped.
    
    Args:
        collection: MongoDB collection
        url: URL to check
        
    Returns:
        bool: True if URL has been scraped before, False otherwise
    """
    try:
        result = collection.find_one({"url": url})
        return result is not None
    except Exception as e:
        print(f"Error checking URL in MongoDB: {str(e)}")
        return False

def get_all_scraped_urls(collection):
    """
    Get all previously scraped URLs from the database.
    
    Args:
        collection: MongoDB collection
        
    Returns:
        set: Set of previously scraped URLs
    """
    try:
        cursor = collection.find({}, {"url": 1, "_id": 0})
        return {doc["url"] for doc in cursor}
    except Exception as e:
        print(f"Error retrieving URLs from MongoDB: {str(e)}")
        return set() 
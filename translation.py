from deep_translator import GoogleTranslator
import time
import random

def translate_to_gujarati(text):
    """
    Translate English text to Gujarati using deep_translator library.
    Includes retry mechanism and rate limiting to avoid API issues.
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    # Maximum retry attempts
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Add rate limiting with random delay to avoid hitting API limits
            delay = 1.0 + random.random()  # Random delay between 1.0 and 2.0 seconds
            time.sleep(delay)
            
            # Create a new translator instance for each request
            translator = GoogleTranslator(source='en', target='gu')
            
            # Break large text into chunks if needed (API limit is ~5000 chars)
            if len(text) > 4000:
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                translated_chunks = []
                for chunk in chunks:
                    time.sleep(delay)  # Add delay between chunks
                    translated_chunks.append(translator.translate(chunk))
                return ' '.join(translated_chunks)
            else:
                # Translate normal text
                return translator.translate(text)
            
        except Exception as e:
            retry_count += 1
            print(f"Translation error (attempt {retry_count}/{max_retries}): {str(e)}")
            time.sleep(2 * retry_count)  # Exponential backoff
    
    # If all retries fail, return original text
    print(f"Failed to translate after {max_retries} attempts: {text[:50]}...")
    return text 
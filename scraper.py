import requests
from bs4 import BeautifulSoup
import io
from PIL import Image
import os
from translation import translate_to_gujarati
import base64
from config import BASE_URL, PAGE_COUNT
import re
from db_utils import get_mongodb_connection, save_scraped_url, get_all_scraped_urls, is_url_scraped
import random

def fetch_article_urls(base_url, pages):
    """Fetch article URLs from multiple pages of GKToday current affairs."""
    all_urls = []
    
    # Step 1: First scrape all URLs from the website
    print(f"Step 1: Scraping URLs from {base_url} (up to {pages} pages)...")
    for page in range(1, pages + 1):
        try:
            page_url = base_url if page == 1 else f"{base_url}page/{page}/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(page_url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Find divs with class="post-data"
            post_data_divs = soup.find_all('div', class_='post-data')
            for div in post_data_divs:
                h3_tag = div.find('h3')
                if h3_tag:
                    link = h3_tag.find('a')
                    if link and link.get('href'):
                        article_url = link['href']
                        if article_url not in all_urls and should_include_url(article_url):
                            all_urls.append(article_url)
            
            # Method 2: Find divs with class="home-post-item"
            home_post_items = soup.find_all('div', class_='home-post-item')
            for div in home_post_items:
                h3_tag = div.find('h3')
                if h3_tag:
                    link = h3_tag.find('a')
                    if link and link.get('href'):
                        article_url = link['href']
                        if article_url not in all_urls and should_include_url(article_url):
                            all_urls.append(article_url)
            
            # Method 3: Look for all h3 elements with links that look like articles
            content_divs = soup.find_all('div')
            for div in content_divs:
                h3_elem = div.find('h3')
                if h3_elem:
                    a_elem = h3_elem.find('a')
                    if a_elem and a_elem.get('href'):
                        article_url = a_elem['href']
                        # Only include GKToday URLs that are likely to be articles
                        if ('gktoday.in' in article_url and 
                            not article_url.endswith('/') and 
                            '/page/' not in article_url and
                            article_url not in all_urls and
                            should_include_url(article_url)):
                            all_urls.append(article_url)
            
            print(f"Found {len(all_urls)} total URLs after scanning page {page}")
        except Exception as e:
            print(f"Error fetching URLs from page {page}: {str(e)}")
    
    print(f"Step 1 completed: Found {len(all_urls)} total URLs from website")
    
    # Step 2: Get all URLs from MongoDB
    print("Step 2: Getting previously scraped URLs from MongoDB...")
    client, collection = get_mongodb_connection()
    previously_scraped_urls = set()
    
    if client is None or collection is None:
        print("Failed to connect to MongoDB. Proceeding without URL filtering.")
    else:
        try:
            # Get previously scraped URLs from MongoDB
            previously_scraped_urls = get_all_scraped_urls(collection)
            print(f"Found {len(previously_scraped_urls)} previously scraped URLs in database")
        except Exception as e:
            print(f"Error retrieving scraped URLs: {str(e)}")
        finally:
            # Close MongoDB connection after getting the URLs
            if client is not None:
                client.close()
    
    # Step 3: Compare and find unique URLs
    print("Step 3: Comparing URLs to find unique ones...")
    unique_urls = []
    for url in all_urls:
        if url not in previously_scraped_urls:
            unique_urls.append(url)
    
    print(f"Found {len(unique_urls)} unique URLs not previously scraped")
    
    # If we have unique URLs, return them
    if unique_urls:
        print(f"Returning {len(unique_urls)} unique URLs for processing")
        return unique_urls
    else:
        print("No new articles found. Processing some existing articles.")
        # If no unique URLs, return a limited number of random existing ones
        random_urls = random.sample(all_urls, min(8, len(all_urls)))
        print(f"Returning {len(random_urls)} random existing URLs for processing")
        return random_urls

def should_include_url(url):
    """
    Check if a URL should be included in scraping.
    
    Args:
        url: The URL to check
    
    Returns:
        bool: True if the URL should be included, False otherwise
    """
    # Skip quiz URLs
    if 'quiz' in url.lower() or 'daily-current-affairs-quiz' in url.lower():
        return False
    
    # Skip category/tag pages
    if '/category/' in url or '/tag/' in url:
        return False
    
    # Skip archive pages
    if '/20' in url and url.endswith('/'):  # Year-based archives like /2023/
        return False
    
    # Skip specific URL patterns
    patterns_to_skip = [
        r'quiz',
        r'mcq',
        r'multiple-choice',
        r'practice-questions',
        r'mock-test',
    ]
    
    for pattern in patterns_to_skip:
        if re.search(pattern, url.lower()):
            return False
    
    return True

def download_and_convert_image(url):
    """Download and convert image to base64 for embedding in HTML."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.content
        if len(content) < 100:  # Check for invalid/small images
            print(f"Image at {url} is too small, likely invalid")
            return None
        
        # Convert image to PNG using Pillow
        img = Image.open(io.BytesIO(content))
        if img.mode in ('RGBA', 'P'):  # Convert transparency to white background
            img = img.convert('RGB')
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        # Convert to base64 for embedding in HTML
        img_str = base64.b64encode(output.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Failed to process image from {url}: {str(e)}")
        return None

async def scrape_and_get_content(url):
    """Scrape article content and process it for PDF generation."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main content area with the new structure
        main_content = soup.find('main', id='main', class_='site-main')
        if not main_content:
            # Fallback to the old structure if new one is not found
            main_content = soup.find('div', class_='inside_post column content_width')
            if not main_content:
                raise Exception("Main content element not found")
        
        heading = main_content.find('h1', id='list')
        if not heading:
            raise Exception("Heading not found")
        
        # Extract featured image with the new structure
        image_url = None
        featured_img = main_content.find('img', class_='post-featured-image')
        if featured_img and featured_img.get('src'):
            image_url = featured_img['src']
        else:
            # Fallback to old structure
            image_div = soup.find('div', class_='featured_image')
            if image_div:
                img_tag = image_div.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
        
        # Process image if found
        image_data = None
        if image_url:
            image_data = download_and_convert_image(image_url)
        
        content_list = []
        heading_text = heading.get_text().strip()
        translated_heading = translate_to_gujarati(heading_text)
        
        # Add the article header information
        article_info = {
            'gujarati_title': translated_heading,
            'english_title': heading_text,
            'image': image_data,
            'content': []
        }
        
        # Find and remove specific sections to exclude from scraping
        # 1. Remove ShareThis buttons
        share_buttons = main_content.find_all('div', class_='sharethis-inline-share-buttons')
        for div in share_buttons:
            div.decompose()
        
        # 2. Remove related articles section
        related_articles = main_content.find_all('div', class_='related-articles')
        for div in related_articles:
            div.decompose()
        
        # 3. Remove comments section
        comments_section = main_content.find(id='comments')
        if comments_section:
            comments_section.decompose()
        
        # Additional comment sections that might be present
        respond_section = main_content.find(id='respond')
        if respond_section:
            respond_section.decompose()
            
        # Remove post-meta sections
        post_meta_sections = main_content.find_all('div', class_='post-meta')
        for section in post_meta_sections:
            section.decompose()
            
        # Remove breadcrumb sections
        breadcrumb_sections = main_content.find_all('div', class_='breadcrumb')
        for section in breadcrumb_sections:
            section.decompose()
        
        # Process only the content elements (paragraphs, headings, lists)
        # Skip breadcrumb, post-meta, comments and other non-content elements
        content_elements = []
        for tag in main_content.find_all(['p', 'h2', 'h4', 'ul', 'ol']):
            # Skip elements inside unwanted sections
            should_skip = False
            
            # Check if parent or grandparent has any of these classes or IDs
            parent = tag.parent
            for _ in range(3):  # Check up to 3 levels up
                if not parent:
                    break
                
                # Skip if parent has any of these classes or IDs
                if parent.get('class'):
                    parent_classes = ' '.join(parent.get('class', []))
                    if any(cls in parent_classes for cls in [
                        'sharethis', 'related-articles', 'comments', 'comment-respond',
                        'post-meta', 'breadcrumb'
                    ]):
                        should_skip = True
                        break
                
                # Skip by ID
                parent_id = parent.get('id', '')
                if any(id_name in parent_id for id_name in ['comments', 'respond']):
                    should_skip = True
                    break
                
                parent = parent.parent
            
            if should_skip:
                continue
            
            content_elements.append(tag)
            
        numbered_list_counter = 1
        for tag in content_elements:
            text = tag.get_text().strip()
            if not text:
                continue
            
            # Skip post-meta and breadcrumb content that might be missed
            if ('post-date' in text.lower() or 'post-categories' in text.lower() or
                'breadcrumb' in text.lower() or 'itemscope' in text.lower() or
                'schema.org' in text.lower() or 'fa fa-calendar' in text.lower() or
                'fa fa-folder' in text.lower()):
                continue
            
            translated_text = translate_to_gujarati(text)
            
            if tag.name == 'p':
                article_info['content'].append({'type': 'paragraph', 'text': translated_text, 'is_gujarati': True})
                article_info['content'].append({'type': 'paragraph', 'text': text, 'is_gujarati': False})
            elif tag.name == 'h2':
                article_info['content'].append({'type': 'heading_2', 'text': translated_text, 'is_gujarati': True})
                article_info['content'].append({'type': 'heading_2', 'text': text, 'is_gujarati': False})
            elif tag.name == 'h4':
                article_info['content'].append({'type': 'heading_4', 'text': translated_text, 'is_gujarati': True})
                article_info['content'].append({'type': 'heading_4', 'text': text, 'is_gujarati': False})
            elif tag.name == 'ul':
                for li in tag.find_all('li'):
                    li_text = li.get_text().strip()
                    translated_li_text = translate_to_gujarati(li_text)
                    article_info['content'].append({'type': 'bullet_list', 'text': translated_li_text, 'is_gujarati': True})
                    article_info['content'].append({'type': 'bullet_list', 'text': li_text, 'is_gujarati': False})
            elif tag.name == 'ol':
                for li in tag.find_all('li'):
                    li_text = li.get_text().strip()
                    translated_li_text = translate_to_gujarati(li_text)
                    article_info['content'].append({'type': 'numbered_list', 'text': translated_li_text, 'number': numbered_list_counter, 'is_gujarati': True})
                    article_info['content'].append({'type': 'numbered_list', 'text': li_text, 'number': numbered_list_counter, 'is_gujarati': False})
                    numbered_list_counter += 1
        
        # Connect to MongoDB and save the URL as scraped
        client, collection = get_mongodb_connection()
        if client is not None and collection is not None:
            try:
                # Store URL to MongoDB after processing
                print(f"Saving URL to MongoDB: {url}")
                save_scraped_url(collection, url)
            except Exception as e:
                print(f"Error saving URL to MongoDB: {str(e)}")
            finally:
                client.close()
        
        return article_info
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

async def get_all_articles(urls, max_articles=None):
    """Process multiple articles and return their structured content."""
    articles = []
    titles = []
    
    # Process all URLs (no random selection)
    # If max_articles is specified, limit to that number
    urls_to_process = urls if not max_articles else urls[:max_articles]
    print(f"Processing {len(urls_to_process)} articles")
    
    for url in urls_to_process:
        print(f"Processing article: {url}")
        article_data = await scrape_and_get_content(url)
        if article_data:
            articles.append(article_data)
            titles.append(article_data['english_title'])
    
    return articles, titles 
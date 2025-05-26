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
from datetime import datetime

def fetch_article_urls(base_url, pages):
    """Fetch article URLs from multiple pages of GKToday current affairs."""
    all_urls = []
    start_time = datetime.now()
    
    # Step 1: First scrape all URLs from the website
    print(f"\n{'='*80}")
    print(f"STEP 1: SCRAPING URLS FROM WEBSITE ({start_time.strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    print(f"Source: {base_url}")
    print(f"Pages to scan: {pages}")
    
    for page in range(1, pages + 1):
        page_start = datetime.now()
        try:
            page_url = base_url if page == 1 else f"{base_url}page/{page}/"
            print(f"\nScanning page {page}/{pages}: {page_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(page_url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            page_urls = []
            
            # Method 1: Find divs with class="post-data"
            post_data_divs = soup.find_all('div', class_='post-data')
            for div in post_data_divs:
                h3_tag = div.find('h3')
                if h3_tag:
                    link = h3_tag.find('a')
                    if link and link.get('href'):
                        article_url = link['href']
                        if article_url not in all_urls and article_url not in page_urls and should_include_url(article_url):
                            page_urls.append(article_url)
            
            # Method 2: Find divs with class="home-post-item"
            home_post_items = soup.find_all('div', class_='home-post-item')
            for div in home_post_items:
                h3_tag = div.find('h3')
                if h3_tag:
                    link = h3_tag.find('a')
                    if link and link.get('href'):
                        article_url = link['href']
                        if article_url not in all_urls and article_url not in page_urls and should_include_url(article_url):
                            page_urls.append(article_url)
            
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
                            article_url not in page_urls and
                            should_include_url(article_url)):
                            page_urls.append(article_url)
            
            # Add all new URLs from this page to our master list
            all_urls.extend(page_urls)
            
            # Display progress for this page
            page_time = (datetime.now() - page_start).total_seconds()
            print(f"  ✓ Found {len(page_urls)} new URLs on page {page} ({page_time:.1f}s)")
            if page_urls:
                for i, url in enumerate(page_urls, 1):
                    print(f"    {i}. {url}")
            
        except Exception as e:
            print(f"  ✗ Error fetching URLs from page {page}: {str(e)}")
    
    # Display summary for Step 1
    step1_time = (datetime.now() - start_time).total_seconds()
    print(f"\nStep 1 Summary:")
    print(f"  • Total URLs found: {len(all_urls)}")
    print(f"  • Time taken: {step1_time:.1f} seconds")
    
    # Step 2: Get all URLs from MongoDB
    step2_start = datetime.now()
    print(f"\n{'='*80}")
    print(f"STEP 2: RETRIEVING SCRAPED URLS FROM MONGODB ({step2_start.strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    
    client, collection = get_mongodb_connection()
    previously_scraped_urls = set()
    
    if client is None or collection is None:
        print("  ✗ Failed to connect to MongoDB. Proceeding without URL filtering.")
    else:
        try:
            # Get previously scraped URLs from MongoDB
            previously_scraped_urls = get_all_scraped_urls(collection)
            print(f"  ✓ Successfully retrieved {len(previously_scraped_urls)} previously scraped URLs")
            
            # Display some sample URLs from MongoDB (up to 5)
            if previously_scraped_urls:
                sample_urls = list(previously_scraped_urls)[:5]
                print(f"  • Sample URLs from database:")
                for i, url in enumerate(sample_urls, 1):
                    print(f"    {i}. {url}")
                if len(previously_scraped_urls) > 5:
                    print(f"    ... and {len(previously_scraped_urls) - 5} more")
        except Exception as e:
            print(f"  ✗ Error retrieving scraped URLs: {str(e)}")
        finally:
            # Close MongoDB connection after getting the URLs
            if client is not None:
                client.close()
                print("  • MongoDB connection closed")
    
    # Display summary for Step 2
    step2_time = (datetime.now() - step2_start).total_seconds()
    print(f"\nStep 2 Summary:")
    print(f"  • URLs in MongoDB: {len(previously_scraped_urls)}")
    print(f"  • Time taken: {step2_time:.1f} seconds")
    
    # Step 3: Compare and find unique URLs
    step3_start = datetime.now()
    print(f"\n{'='*80}")
    print(f"STEP 3: COMPARING URLS TO FIND UNIQUE ONES ({step3_start.strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    
    unique_urls = []
    for url in all_urls:
        if url not in previously_scraped_urls:
            unique_urls.append(url)
    
    # Display results
    print(f"  • Total URLs found from website: {len(all_urls)}")
    print(f"  • URLs already in MongoDB: {len(previously_scraped_urls)}")
    print(f"  • Unique URLs for processing: {len(unique_urls)}")
    
    if unique_urls:
        print(f"\n  ✓ Found {len(unique_urls)} unique URLs to process:")
        for i, url in enumerate(unique_urls, 1):
            print(f"    {i}. {url}")
    else:
        print(f"\n  ✗ No new unique URLs found")
    
    # Display summary for Step 3
    step3_time = (datetime.now() - step3_start).total_seconds()
    print(f"\nStep 3 Summary:")
    print(f"  • Unique URLs identified: {len(unique_urls)}")
    print(f"  • Time taken: {step3_time:.1f} seconds")
    
    # Final decision
    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*80}")
    print(f"FINAL DECISION ({datetime.now().strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    
    # If we have unique URLs, return them
    if unique_urls:
        print(f"✓ Returning {len(unique_urls)} unique URLs for processing")
        print(f"• Total processing time: {total_time:.1f} seconds")
        return unique_urls
    else:
        print("✗ No new articles found. Processing 2 random existing articles instead.")
        # If no unique URLs, return exactly 2 random existing ones
        random_urls = random.sample(all_urls, min(2, len(all_urls)))
        print(f"✓ Randomly selected {len(random_urls)} existing URLs for processing:")
        for i, url in enumerate(random_urls, 1):
            print(f"  {i}. {url}")
        print(f"• Total processing time: {total_time:.1f} seconds")
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
    start_time = datetime.now()
    print(f"\n{'='*50}")
    print(f"PROCESSING ARTICLE: {url}")
    print(f"Started at: {start_time.strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    
    try:
        print("• Fetching article content...")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main content area with the new structure
        print("• Locating main content...")
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
        print("• Looking for featured image...")
        image_url = None
        featured_img = main_content.find('img', class_='post-featured-image')
        if featured_img and featured_img.get('src'):
            image_url = featured_img['src']
            print(f"  ✓ Found featured image: {image_url}")
        else:
            # Fallback to old structure
            image_div = soup.find('div', class_='featured_image')
            if image_div:
                img_tag = image_div.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
                    print(f"  ✓ Found featured image (fallback): {image_url}")
            else:
                print("  ✗ No featured image found")
        
        # Process image if found
        image_data = None
        if image_url:
            print("• Processing image...")
            image_data = download_and_convert_image(image_url)
            if image_data:
                print("  ✓ Image processed successfully")
            else:
                print("  ✗ Failed to process image")
        
        heading_text = heading.get_text().strip()
        print(f"• Article title: {heading_text}")
        
        print("• Translating title to Gujarati...")
        translated_heading = translate_to_gujarati(heading_text)
        print("  ✓ Translation complete")
        
        # Add the article header information
        article_info = {
            'gujarati_title': translated_heading,
            'english_title': heading_text,
            'image': image_data,
            'content': []
        }
        
        # Find and remove specific sections to exclude from scraping
        print("• Cleaning up article content...")
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
        print("• Extracting content elements...")
        content_elements = []
        
        # First try to find the article-content div which contains the main content
        article_content = main_content.find('div', class_='entry-content')
        if not article_content:
            article_content = main_content.find('div', class_='post-content')
        if not article_content:
            article_content = main_content
            
        # Find all content elements within the article content
        for tag in article_content.find_all(['p', 'h2', 'h4', 'ul', 'ol']):
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
                
            # Skip empty elements or those with very little content
            text = tag.get_text().strip()
            if not text or len(text) < 10:
                continue
                
            content_elements.append(tag)
        
        print(f"  ✓ Found {len(content_elements)} content elements")
        
        # If no content elements were found, try a more aggressive approach
        if len(content_elements) == 0:
            print("  ⚠️ No content elements found with standard approach, trying alternative methods...")
            
            # Method 1: Try to find any paragraphs directly in the main content
            all_paragraphs = main_content.find_all('p')
            if all_paragraphs:
                print(f"  • Found {len(all_paragraphs)} paragraphs with direct search")
                content_elements = [p for p in all_paragraphs if len(p.get_text().strip()) > 20]
                print(f"  • Added {len(content_elements)} meaningful paragraphs")
            
            # Method 2: If still no content, look for divs with substantial text
            if len(content_elements) == 0:
                print("  • Looking for divs with substantial text...")
                for div in main_content.find_all('div'):
                    if div.find_all(['p', 'h2', 'h4', 'ul', 'ol']):
                        # Skip if this div is likely a container
                        continue
                    
                    text = div.get_text().strip()
                    if len(text) > 100:  # Only divs with substantial text
                        content_elements.append(div)
                        print(f"  • Added div with {len(text)} characters of text")
        
        print(f"  ✓ Final content elements count: {len(content_elements)}")
        
        print("• Processing and translating content...")
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
                print(f"  • Added paragraph: {text[:50]}...")
            elif tag.name == 'h2':
                article_info['content'].append({'type': 'heading_2', 'text': translated_text, 'is_gujarati': True})
                article_info['content'].append({'type': 'heading_2', 'text': text, 'is_gujarati': False})
                print(f"  • Added heading: {text}")
            elif tag.name == 'h4':
                article_info['content'].append({'type': 'heading_4', 'text': translated_text, 'is_gujarati': True})
                article_info['content'].append({'type': 'heading_4', 'text': text, 'is_gujarati': False})
                print(f"  • Added subheading: {text}")
            elif tag.name == 'ul':
                for li in tag.find_all('li'):
                    li_text = li.get_text().strip()
                    translated_li_text = translate_to_gujarati(li_text)
                    article_info['content'].append({'type': 'bullet_list', 'text': translated_li_text, 'is_gujarati': True})
                    article_info['content'].append({'type': 'bullet_list', 'text': li_text, 'is_gujarati': False})
                    print(f"  • Added bullet point: {li_text[:50]}...")
            elif tag.name == 'ol':
                for li in tag.find_all('li'):
                    li_text = li.get_text().strip()
                    translated_li_text = translate_to_gujarati(li_text)
                    article_info['content'].append({'type': 'numbered_list', 'text': translated_li_text, 'number': numbered_list_counter, 'is_gujarati': True})
                    article_info['content'].append({'type': 'numbered_list', 'text': li_text, 'number': numbered_list_counter, 'is_gujarati': False})
                    print(f"  • Added numbered point {numbered_list_counter}: {li_text[:50]}...")
                    numbered_list_counter += 1
        
        print(f"  ✓ Processed {len(article_info['content'])} content blocks")
        
        # Debug: Check if content was actually extracted
        if len(article_info['content']) == 0:
            print("  ⚠️ WARNING: No content was extracted from this article!")
            print("  ⚠️ This may indicate a problem with the HTML structure or content selectors.")
            
            # Try a more aggressive approach to find content
            print("  • Attempting more aggressive content extraction...")
            all_paragraphs = main_content.find_all('p')
            if all_paragraphs:
                print(f"  • Found {len(all_paragraphs)} paragraphs with direct search")
                for p in all_paragraphs[:3]:  # Just add the first few paragraphs as a fallback
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Only meaningful paragraphs
                        translated_text = translate_to_gujarati(text)
                        article_info['content'].append({'type': 'paragraph', 'text': translated_text, 'is_gujarati': True})
                        article_info['content'].append({'type': 'paragraph', 'text': text, 'is_gujarati': False})
                        print(f"  • Added fallback paragraph: {text[:50]}...")

        # Connect to MongoDB and save the URL as scraped
        print("• Saving URL to MongoDB...")
        client, collection = get_mongodb_connection()
        if client is not None and collection is not None:
            try:
                # Store URL to MongoDB after processing
                save_scraped_url(collection, url)
                print(f"  ✓ Successfully saved URL to MongoDB: {url}")
            except Exception as e:
                print(f"  ✗ Error saving URL to MongoDB: {str(e)}")
            finally:
                client.close()
                print("  • MongoDB connection closed")
        else:
            print("  ✗ Failed to connect to MongoDB, URL not saved")
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"\nArticle processing completed in {processing_time:.1f} seconds")
        print(f"Finished at: {end_time.strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        
        return article_info
    except Exception as e:
        print(f"  ✗ Error scraping article: {str(e)}")
        print(f"{'='*50}")
        return None

async def get_all_articles(urls, max_articles=None):
    """Process multiple articles and return their structured content."""
    start_time = datetime.now()
    print(f"\n{'='*80}")
    print(f"STARTING ARTICLE PROCESSING ({start_time.strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    
    articles = []
    titles = []
    
    # Process all URLs (no random selection)
    # If max_articles is specified, limit to that number
    urls_to_process = urls if not max_articles else urls[:max_articles]
    print(f"Total URLs to process: {len(urls_to_process)}")
    
    for i, url in enumerate(urls_to_process, 1):
        print(f"\nProcessing article {i}/{len(urls_to_process)}: {url}")
        article_data = await scrape_and_get_content(url)
        if article_data:
            articles.append(article_data)
            titles.append(article_data['english_title'])
            print(f"✓ Article {i} processed successfully: {article_data['english_title']}")
        else:
            print(f"✗ Failed to process article {i}: {url}")
    
    # Calculate processing time
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*80}")
    print(f"ARTICLE PROCESSING COMPLETE ({end_time.strftime('%H:%M:%S')})")
    print(f"{'='*80}")
    print(f"• Total articles processed: {len(articles)} of {len(urls_to_process)}")
    print(f"• Success rate: {(len(articles)/len(urls_to_process)*100):.1f}%")
    print(f"• Total processing time: {total_time:.1f} seconds")
    print(f"• Average time per article: {(total_time/len(urls_to_process)):.1f} seconds")
    
    return articles, titles 
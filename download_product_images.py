#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Product Image Downloader Script

This script connects to the database, retrieves all product codes and names,
and downloads images for each product from various online sources.
"""

import os
import time
import random
import requests
import mysql.connector
from urllib.parse import quote_plus
from io import BytesIO
from PIL import Image, ImageDraw
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("image_download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ImageDownloader")

# Database connection settings - using the same as in app.py
DB_CONFIG = {
    'host': '127.0.0.1',
    'database': 'pfe1',
    'user': 'root',
    'password': ''
}

# Directory to save images
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'product_images')
os.makedirs(IMAGE_DIR, exist_ok=True)

# User agent for web requests - pretend to be a browser
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

# Various image search APIs and endpoints
SEARCH_ENGINES = [
    # Google Images (Custom Search JSON API)
    {
        'name': 'Google Images',
        'url': 'https://serpapi.com/search.json?engine=google_images&q={}&api_key=YOUR_API_KEY',
        'enabled': False,  # Requires API key
        'image_key_path': ['images_results', 0, 'original']
    },
    # Bing Image Search API
    {
        'name': 'Bing Images',
        'url': 'https://api.bing.microsoft.com/v7.0/images/search?q={}',
        'headers': {'Ocp-Apim-Subscription-Key': 'YOUR_API_KEY'},
        'enabled': False,  # Requires API key
        'image_key_path': ['value', 0, 'contentUrl']
    },
    # Pixabay API (free up to 5000 requests/hour)
    {
        'name': 'Pixabay',
        'url': 'https://pixabay.com/api/?key=YOUR_API_KEY&q={}&image_type=photo',
        'enabled': False,  # Requires API key
        'image_key_path': ['hits', 0, 'webformatURL']
    },
    # DuckDuckGo (Public API, no key needed, but less reliable)
    {
        'name': 'DuckDuckGo',
        'url': 'https://duckduckgo.com/',
        'params': {'q': '{}', 'iax': 'images', 'ia': 'images', 'format': 'json'},
        'enabled': True,
        'is_scraper': True
    }
]

def get_db_connection():
    """Establish a database connection using the config."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        logger.error(f"Database connection error: {err}")
        return None

def get_all_products():
    """Retrieve all product codes and names from the database."""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, libelle, code_a_barre 
            FROM produits 
            WHERE libelle IS NOT NULL 
            ORDER BY code
        """)
        
        products = [
            {'code': code, 'name': name, 'barcode': barcode} 
            for code, name, barcode in cursor.fetchall()
        ]
        
        conn.close()
        return products
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []

def download_image_from_url(url, product_code):
    """Download an image from a URL and save it with the product code as filename."""
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type:
                return False
            
            # Process the image
            img = Image.open(BytesIO(response.content))
            
            # Resize if necessary (maintain aspect ratio)
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Save the image
            filepath = os.path.join(IMAGE_DIR, f"{product_code}.jpg")
            img.convert('RGB').save(filepath, 'JPEG', quality=85)
            
            logger.info(f"Image downloaded and saved for product {product_code}")
            return True
        else:
            logger.warning(f"Failed to download image. Status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error downloading image for {product_code}: {e}")
        return False

def create_placeholder_image(product_code, product_name):
    """Create a placeholder image with product code and name."""
    try:
        width, height = 400, 300
        image = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        # Draw background elements
        draw.rectangle([(0, 0), (width, height)], outline=(200, 200, 200))
        
        # Add text (product code and name)
        # Note: We don't specify font as it may not be available on all systems
        product_code_pos = (width//2, height//3)
        product_name_pos = (width//2, height//2)
        unavailable_pos = (width//2, 2*height//3)
        
        # Simple approach to center text
        draw.text(product_code_pos, product_code, fill=(0, 0, 0))
        text_lines = [line for line in product_name.split() if line]
        
        # Try to fit the product name on multiple lines if needed
        if len(text_lines) > 3:
            y_offset = height//2 - 30
            for i, line in enumerate(text_lines[:3]):
                draw.text((width//2, y_offset + i*20), line, fill=(70, 70, 70))
            draw.text((width//2, y_offset + 3*20), "...", fill=(70, 70, 70))
        else:
            for i, line in enumerate(text_lines):
                draw.text((width//2, height//2 + i*20), line, fill=(70, 70, 70))
        
        draw.text(unavailable_pos, "Image non disponible", fill=(150, 150, 150))
        
        # Save the image
        filepath = os.path.join(IMAGE_DIR, f"{product_code}.jpg")
        image.save(filepath, 'JPEG', quality=85)
        
        logger.info(f"Placeholder created for product {product_code}")
        return True
    except Exception as e:
        logger.error(f"Error creating placeholder for {product_code}: {e}")
        return False

def search_and_download_image(product):
    """
    Search for a product image using the product name and code,
    download it if found, or create a placeholder if not.
    """
    product_code = product['code']
    product_name = product['name']
    barcode = product['barcode']
    
    # Check if image already exists
    image_path = os.path.join(IMAGE_DIR, f"{product_code}.jpg")
    if os.path.exists(image_path):
        logger.info(f"Image for {product_code} already exists, skipping.")
        return True
    
    logger.info(f"Searching image for {product_code}: {product_name}")
    
    # Try searching by product name
    search_query = product_name
    if barcode:
        # Add barcode to search query if available
        search_query = f"{product_name} {barcode}"
    
    # Check publicly available image sources (no API key required)
    # Using simple web scraping approach for demonstration
    try:
        # Example: Search for product images using Bing
        search_url = f"https://www.bing.com/images/search?q={quote_plus(search_query)}"
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Simple extraction of image links - not reliable for production
            # We're looking for image URLs in the response
            text = response.text.lower()
            start_marker = '"murl":"'
            end_marker = '"'
            
            image_urls = []
            start_pos = 0
            
            # Extract a few image URLs
            for _ in range(5):  # Try to find up to 5 images
                start_idx = text.find(start_marker, start_pos)
                if start_idx == -1:
                    break
                    
                start_idx += len(start_marker)
                end_idx = text.find(end_marker, start_idx)
                
                if end_idx != -1:
                    img_url = text[start_idx:end_idx]
                    if img_url.startswith('http') and (img_url.endswith('.jpg') or img_url.endswith('.jpeg') or img_url.endswith('.png')):
                        image_urls.append(img_url)
                    start_pos = end_idx
            
            # Try to download any of the found images
            for img_url in image_urls:
                if download_image_from_url(img_url, product_code):
                    return True
    
    except Exception as e:
        logger.warning(f"Error during image search: {e}")
    
    # If we couldn't find or download any image, create a placeholder
    return create_placeholder_image(product_code, product_name)

def main():
    """Main function to orchestrate the download process."""
    logger.info("Starting product image download process")
    
    # Get all products from database
    products = get_all_products()
    logger.info(f"Found {len(products)} products in database")
    
    if not products:
        logger.error("No products found or database connection failed!")
        return
    
    # Process each product
    success_count = 0
    for i, product in enumerate(products):
        logger.info(f"Processing {i+1}/{len(products)}: {product['code']} - {product['name']}")
        
        if search_and_download_image(product):
            success_count += 1
        
        # Be nice to servers, add small delay between requests
        time.sleep(1)
        
        # Show progress
        if (i+1) % 10 == 0 or (i+1) == len(products):
            logger.info(f"Progress: {i+1}/{len(products)} products processed ({success_count} images saved)")
    
    logger.info(f"Process complete. {success_count} out of {len(products)} images saved.")

if __name__ == "__main__":
    main()
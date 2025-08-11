import requests
from bs4 import BeautifulSoup
import csv
import os

# URL to scrape - now the homepage
url = "https://abmltd.co.ke/"

# File paths
html_file = "abmltd_homepage.html"
csv_file = "extracted_urls.csv"

# Step 1: Scrape the HTML and save it
def scrape_and_save_html():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        
        with open(html_file, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"HTML content successfully saved to {html_file}")
    except Exception as e:
        print(f"Error scraping HTML: {e}")

# Step 2: Read HTML and extract URLs from specific class
def extract_urls_to_csv():
    try:
        # Read the saved HTML file
        with open(html_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all elements with the specified class
        elements = soup.find_all(class_="nav-link-title cursor-pointer flex gap-2 items-center hover:text-primary")
        
        # Extract href attributes and ensure URLs are absolute
        base_url = "https://abmltd.co.ke"
        urls = []
        for element in elements:
            if element.has_attr('href'):
                href = element['href']
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = base_url + href
                urls.append(href)
        
        # Save to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Extracted URLs'])  # Header
            for url in urls:
                writer.writerow([url])
        
        print(f"Extracted {len(urls)} URLs and saved to {csv_file}")
        print("Sample URLs extracted:")
        for url in urls[:5]:  # Print first 5 URLs as sample
            print(f"- {url}")
    except Exception as e:
        print(f"Error extracting URLs: {e}")

# Main execution
if __name__ == "__main__":
    # Step 1: Scrape and save HTML
    scrape_and_save_html()
    
    # Step 2: Extract URLs and save to CSV
    if os.path.exists(html_file):
        extract_urls_to_csv()
    else:
        print(f"Cannot proceed - HTML file {html_file} not found")
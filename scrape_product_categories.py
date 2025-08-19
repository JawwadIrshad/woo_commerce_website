import requests
from bs4 import BeautifulSoup
import csv
import os

# URL to scrape
url = "https://abmltd.co.ke/" #pste your website url

# File paths
html_file = "abm_printers_page.html"
csv_file = "extracted2_urls.csv"

def scrape_and_save_html():
    try:
        # Send HTTP request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Save HTML to file
        with open(html_file, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"HTML successfully saved to {html_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return False
    return True

def extract_urls_from_html():
    try:
        # Read the saved HTML file
        with open(html_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all elements with the specified class
        target_elements = soup.find_all(class_="h-10 flex items-center px-4 gap-4 hover:text-primary")
        
        # Extract href attributes
        urls = []
        for element in target_elements:
            href = element.get('href')
            if href:
                # Make sure URL is absolute (add domain if relative)
                if not href.startswith(('http://', 'https://')):
                    href = f"https://abmltd.co.ke{href}" if href.startswith('/') else f"https://abmltd.co.ke/{href}"
                urls.append(href)
        
        # Save URLs to CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Extracted URLs'])  # Header
            writer.writerows([[url] for url in urls])
        
        print(f"Extracted {len(urls)} URLs and saved to {csv_file}")
        
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return False
    return True

def main():
    print("Starting scraping process...")
    
    # Step 1: Scrape and save HTML
    if not scrape_and_save_html():
        return
    
    # Step 2: Extract URLs and save to CSV
    if not extract_urls_from_html():
        return
    
    print("Process completed successfully!")

if __name__ == "__main__":

    main()

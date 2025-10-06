#product.py file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

# Configure Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Headless mode
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def read_urls_from_csv(filename='extracted2_urls.csv'):
    urls = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # skip empty rows
                urls.append(row[0].strip())
    return urls

def scrape_products(url):
    driver.get(url)
    time.sleep(3)  # Wait for page to load
    
    # Scroll to load products
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    products_data = []
    
    # Find all product containers
    products = driver.find_elements(By.XPATH, "//div[contains(@class, 'grid grid-cols-2')]/div[contains(@class, 'text-3')]")
    
    for product in products:
        try:
            name = product.find_element(By.XPATH, ".//p[contains(@class, 'w-full px-4')]").text
            price = product.find_element(By.XPATH, ".//div[contains(@class, 'font-semibold')]").text
            link = product.find_element(By.XPATH, ".//a[@href][1]").get_attribute('href')
            image = product.find_element(By.XPATH, ".//img[@alt]").get_attribute('src')
            
            products_data.append({
                'name': name,
                'price': price,
                'link': link,
                'image_url': image,
                'source_url': url
            })
        except Exception as e:
            print(f"Error scraping a product from {url}: {e}")
            continue
    
    return products_data

def save_to_csv(data, filename='products.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'price', 'link', 'image_url', 'source_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    try:
        print("Reading URLs from urls.csv...")
        urls = read_urls_from_csv()
        
        all_products = []
        for url in urls:
            print(f"Scraping {url}...")
            products = scrape_products(url)
            all_products.extend(products)
        
        print(f"Scraped total {len(all_products)} products.")
        save_to_csv(all_products)
        print("Data saved to products.csv")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


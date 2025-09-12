import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scrape_product(url):
    driver.get(url)
    time.sleep(3)  # Let page load fully

    product_data = {
        "url": url,
        "title": None,
        "price": None,
        "main_image": None,
        "all_images": [],
        "short_description": None,
        "full_description_html": None,
        "features": {}
    }

    try:
        # Main product title
        product_data["title"] = driver.find_element(By.XPATH, "//h1[contains(@class, 'font-bold')]").text.strip()
        print(f"✔ Title: {product_data['title']}")
    except Exception as e:
        print(f"❌ Error is getting in title: {e}")

    try:
        # Product price - EXACT MATCH for the element structure
        price_element = driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'text-5')]/div[contains(@class, 'flex flex-col')]/div[contains(@class, 'text-5') and contains(@class, 'lg:text-6') and contains(@class, 'font-semibold')]"
        )
        product_data["price"] = price_element.text.strip()
        print(f"✔ Price found: {product_data['price']}")
    except Exception as e:
        print(f"❌ Error getting price (exact match): {e}")
        try:
            # Fallback to simpler selector
            price_element = driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'text-5') and contains(@class, 'lg:text-6') and contains(@class, 'font-semibold')]"
            )
            product_data["price"] = price_element.text.strip()
            print(f"✔ Price found (simpler selector): {product_data['price']}")
        except Exception as e:
            print(f"❌ Error getting price (fallback method): {e}")

    # [Rest of your scraping code remains the same...]
    try:
        # Main product image
        main_img = driver.find_element(By.XPATH, "//div[contains(@class, 'w-full relative')]//img")
        product_data["main_image"] = main_img.get_attribute("src")
    except Exception as e:
        print(f"❌ Error getting main image: {e}")

    try:
        # All product images
        images = []
        if product_data["main_image"]:
            images.append(product_data["main_image"])
        thumbnails = driver.find_elements(By.XPATH, "//div[contains(@class, 'thumbs')]//img")
        for thumb in thumbnails:
            img_src = thumb.get_attribute("src")
            if img_src and img_src not in images:
                images.append(img_src)
        product_data["all_images"] = images
    except Exception as e:
        print(f"❌ Error getting all images: {e}")

    try:
        # Product features
        features = {}
        feature_items = driver.find_elements(
            By.XPATH,
            "//div[contains(@class, 'mt-4') and contains(@class, 'lg:text-5') and contains(@class, 'flex') and contains(@class, 'items-center')]"
        )
        for item in feature_items:
            try:
                key = item.find_element(By.XPATH, ".//span[contains(@class, 'w-200px')]").text.strip().replace(':', '').strip()
                value = item.find_element(By.XPATH, ".//*[not(contains(@class, 'w-200px'))]").text.strip()
                if key:
                    features[key] = value
            except:
                continue
        product_data["features"] = features
    except Exception as e:
        print(f"❌ Error getting features: {e}")

    try:
        # Full description
        desc_section = driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'mt-10') or contains(@class, 'lg:mt-16')]//p"
        )
        product_data["full_description_html"] = desc_section.get_attribute("innerHTML").strip()
        product_data["short_description"] = desc_section.text.strip()[:200]
    except Exception as e:
        print(f"❌ Error getting description: {e}")

    return product_data

# [Rest of your script remains the same...]
# Setup Selenium (Headless Mode)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

results = []
csv_file_path = "products.csv"  # Your CSV file path

# Read CSV and find product URLs
with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        for cell in row:
            if "https://abmltd.co.ke/products/" in cell:
                try:
                    product_data = scrape_product(cell)
                    results.append(product_data)
                    print(f"✅ Scraped: {cell}")
                except Exception as e:
                    print(f"❌ Error scraping {cell}: {e}")
                time.sleep(2)  # Be polite between requests

driver.quit()

# Save results to JSON
with open("scraped_products_full.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("🎯 Scraping has been complete. Data will saved to scraped_products_full.json file")


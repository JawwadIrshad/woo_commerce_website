import json
import requests
from urllib.parse import urlparse
import time

# WooCommerce API credentials
WC_CONSUMER_KEY = '' #paste your woo_commerce key
WC_CONSUMER_SECRET = ''  #paste your woo_commerce secret key

# WooCommerce endpoints
BASE_URL = 'https://abmltd.prowebkong.com/wp-json/wc/v3'
PRODUCTS_URL = f'{BASE_URL}/products'
CATEGORIES_URL = f'{BASE_URL}/products/categories'
ATTRIBUTES_URL = f'{BASE_URL}/products/attributes'


SOURCE_FILE = 'scraped_products_full.json'

# Category hierarchy
CATEGORY_HIERARCHY = {
    "printer": {
        "printer\\new printer": {
            "printer\\new printer\\new pantum printer": None,
            "printer\\new printer\\new kyocera printer": None
        },
        "printer\\refurbished printers": {
            "printer\\refurbished printers\\ricoh refurbished printer": None,
            "printer\\refurbished printers\\kyocera refurbished printer": None,
            "printer\\refurbished printers\\konica minolta refurbished printer": None
        }
    },
    "toners": {
        "toners\\original cartidges": None,
        "toners\\optimum cartidges": None,
        "toners\\optimage cartidges": None,
        "toners\\DT cartidges": None,
        "toners\\toner refills": None,
        "toners\\ink & toner master": None
    }
}

# List of attributes to create
ATTRIBUTES_TO_CREATE = [
    "Brand", "Model", "Type", "Function", "Adf", 
    "Duplex", "Resolution", "Condition", "Paper Size", 
    "Connectivity", "Print Speed"
]

def clean_price(price_str):
    """Convert price string to float"""
    if not price_str:
        return None
    try:
        numeric_part = ''.join(c for c in price_str if c.isdigit() or c == '.')
        return float(numeric_part)
    except:
        return None

def is_valid_image_url(url):
    """Validate image URL"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False
        return parsed.path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
    except:
        return False

def format_product_display(product_data):
    """Format product description HTML"""
    features = product_data.get('features', {})
    non_empty_features = {k: v for k, v in features.items() if v}
    
    description_html = f"<h2>{product_data.get('price', '')}</h2>"
    
    if non_empty_features:
        description_html += """
        <div class="product-attributes">
            <h3>Specifications</h3>
            <table>
        """
        for key, value in non_empty_features.items():
            description_html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
        description_html += "</table></div>"
    
    full_description = product_data.get('full_description_html', '')
    description_html += f"<hr><div class='product-description'>{full_description}</div>"
    
    return description_html

def create_category_hierarchy(parent_id=None, hierarchy=None, existing_categories=None):
    """Create category hierarchy recursively"""
    if hierarchy is None:
        hierarchy = CATEGORY_HIERARCHY
    if existing_categories is None:
        existing_categories = []
    
    created_categories = []
    for name, children in hierarchy.items():
        existing_category = next(
            (cat for cat in existing_categories if cat['name'].lower() == name.lower()), 
            None
        )
        
        if not existing_category:
            category_data = {"name": name, "parent": parent_id or 0}
            response = requests.post(
                CATEGORIES_URL,
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers={"Content-Type": "application/json"},
                json=category_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                existing_category = response.json()
                print(f"✅ Created the category: {name} (ID: {existing_category['id']})")
            elif response.status_code == 400 and "term_exists" in response.text:
                existing_id = response.json()["data"]["resource_id"]
                existing_category = {"id": existing_id, "name": name}
                print(f"ℹ️ Category already exists: {name} (ID: {existing_id})")
            else:
                print(f"❌ Failed to create category {name}: {response.status_code} - {response.text}")
                continue
        
        created_categories.append(existing_category)
        
        if children:
            child_categories = create_category_hierarchy(
                parent_id=existing_category['id'],
                hierarchy=children,
                existing_categories=existing_categories
            )
            created_categories.extend(child_categories)
    
    return created_categories

def create_attributes():
    """Create product attributes if they don't exist"""
    print("\n🔍 Checking/Creating the product attributes...")
    
    try:
        response = requests.get(
            ATTRIBUTES_URL,
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            params={'per_page': 100},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to the fetch attributes: {response.status_code} - {response.text}")
            return []
            
        existing_attributes = response.json()
        existing_slugs = [attr['slug'] for attr in existing_attributes]
        print(f"ℹ️ Found {len(existing_attributes)} existing attributes")
        
    except Exception as e:
        print(f"❌ Error fetching the attributes: {str(e)}")
        return []

    created_attributes = []
    for attr_name in ATTRIBUTES_TO_CREATE:
        slug = f"pa_{attr_name.lower().replace(' ', '-')}"
        
        if slug not in existing_slugs:
            print(f"🔄 Creating attribute: {attr_name}...")
            
            attribute_data = {
                "name": attr_name,
                "slug": slug,
                "type": "select",
                "order_by": "menu_order",
                "has_archives": False
            }
            
            try:
                create_response = requests.post(
                    ATTRIBUTES_URL,
                    auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                    headers={"Content-Type": "application/json"},
                    json=attribute_data,
                    timeout=30
                )
                
                if create_response.status_code in [200, 201]:
                    created_attr = create_response.json()
                    created_attributes.append(created_attr)
                    print(f"✅ Created attribute: {attr_name} (ID: {created_attr['id']})")
                else:
                    print(f"⚠️ Failed to create {attr_name}: {create_response.status_code} - {create_response.text}")
                    
            except Exception as e:
                print(f"❌ Error creating attribute {attr_name}: {str(e)}")
        else:
            print(f"⏩ Attribute already exists: {attr_name}")
    
    return existing_attributes + created_attributes

def determine_category(features, product_title, existing_categories):
    """Determine the appropriate category with improved matching"""
    brand = features.get('Brand', '').lower()
    condition = features.get('Condition', '').lower()
    product_type = features.get('Type', '').lower()
    title = product_title.lower()
    
    # Normalize variations
    normalized_title = title.replace('&', 'and').replace('cartidges', 'cartridges')
    
    # First check for DX models - these should be ink/toner products
    is_dx_model = 'dx' in normalized_title
    
    # Toner detection - prioritize ink products first
    toner_keywords = ['toner', 'cartridge', 'cartidges', 'ink']
    is_toner = (is_dx_model or 
               any(kw in product_type for kw in toner_keywords) or 
               any(kw in normalized_title for kw in toner_keywords))
    
    if is_toner:
        # DX models should go to ink & toner master
        if is_dx_model:
            leaf_name = "ink & toner master"
        # Then check for ink products
        elif ('ink' in normalized_title or 'ink' in product_type or
              'master' in normalized_title or 'master' in product_type):
            leaf_name = "ink & toner master"
        # Then check other toner types
        elif 'original' in normalized_title or 'original' in product_type:
            leaf_name = "original cartidges"
        elif 'optimum' in normalized_title or 'optimum' in product_type:
            leaf_name = "optimum cartidges"
        elif 'optimage' in normalized_title or 'optimage' in product_type:
            leaf_name = "optimage cartidges"
        elif 'dt' in normalized_title or 'dt' in product_type:
            leaf_name = "DT cartidges"
        elif 'refill' in normalized_title or 'refill' in product_type:
            leaf_name = "toner refills"
        else:
            leaf_name = "toners"
    else:
        # Printer categorization``
        if "refurbished" in condition:
            if "ricoh" in brand:
                leaf_name = "ricoh refurbished printer"
            elif "kyocera" in brand:
                leaf_name = "kyocera refurbished printer"
            elif "konica" in brand or "minolta" in brand:
                leaf_name = "konica minolta refurbished printer"
            else:
                leaf_name = "refurbished printers"
        else:
            if "pantum" in brand:
                leaf_name = "new pantum printer"
            elif "kyocera" in brand:
                leaf_name = "new kyocera printer"
            else:
                leaf_name = "new printer"
    
    # Find category by leaf name with flexible matching
    leaf_name = leaf_name.split('\\')[-1] if '\\' in leaf_name else leaf_name
    
    # Create a list of possible matches
    possible_matches = [
        leaf_name.lower(),
        leaf_name.lower().replace('&', 'and'),
        leaf_name.lower().replace('printer', 'printers'),
        leaf_name.lower().replace('cartidges', 'cartridges'),
        leaf_name.lower().replace('&', '&amp;')
    ]
    
    # Try all possible matches
    for match in possible_matches:
        category = next(
            (cat for cat in existing_categories 
             if any(match in cat_name.lower() for cat_name in [
                 cat.get('name', ''),
                 cat.get('name', '').replace('&', 'and'),
                 cat.get('name', '').replace('&amp;', 'and')
             ])),
            None
        )
        if category:
            break
    
    # Special handling for ink products - create category if needed
    if not category and ('ink' in leaf_name.lower() or 'ink' in normalized_title or is_dx_model):
        ink_category_name = "ink & toner master"
        print(f"🔄 Special handling for ink/DX product: {product_title}")
        
        # Try to find the ink category again with different variations
        category = next(
            (cat for cat in existing_categories 
             if any(name_part in cat.get('name', '').lower() 
                for name_part in ['ink', 'toner', 'master'])),
            None
        )
        
        if not category:
            print(f"🔄 Attempting to create missing ink category: {ink_category_name}")
            parent_id = next(
                (cat['id'] for cat in existing_categories 
                 if any(name_part in cat.get('name', '').lower() 
                    for name_part in ['toners', 'toner'])),
                0
            )
            try:
                response = requests.post(
                    CATEGORIES_URL,
                    auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                    json={
                        "name": ink_category_name,
                        "parent": parent_id
                    },
                    timeout=30
                )
                
                if response.status_code == 201:
                    category = response.json()
                    existing_categories.append(category)
                    print(f"✅ Created ink category: {ink_category_name} (ID: {category['id']})")
                elif response.status_code == 400 and "term_exists" in response.text:
                    existing_id = response.json()["data"]["resource_id"]
                    category = {"id": existing_id, "name": ink_category_name}
                    existing_categories.append(category)
                    print(f"ℹ️ Ink category already exists: {ink_category_name} (ID: {existing_id})")
                else:
                    print(f"❌ Failed to create ink category: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"❌ Error creating ink category: {str(e)}")
    
    if not category:
        print(f"⚠️ Category not found for: {leaf_name}")
        print(f"Available categories: {[cat.get('name', 'N/A') for cat in existing_categories]}")
    
    return category

def upload_product(product_data, existing_categories, existing_attributes):
    """Upload product with proper attributes"""
    try:
        product_name = product_data.get('title', '')
        if not product_name:
            print(f"⏭️ Skipping product: No name provided")
            return False
        
        # Prepare basic product data
        wc_product = {
            "name": product_name,
            "type": "simple",
            "status": "publish",
            "description": format_product_display(product_data),
            "regular_price": str(clean_price(product_data.get('price'))),
            "meta_data": [],
            "attributes": []
        }

        # Handle categories
        features = product_data.get('features', {})
        category = determine_category(features, product_name, existing_categories)
        
        if category:
            wc_product["categories"] = [{"id": category['id']}]
            print(f"ℹ️ Assigned category: {category['name']}")
        else:
            print("⚠️ No matching category is found")

        # Handle attributes
        for key, value in features.items():
            if key and value:
                # Add to metadata
                wc_product["meta_data"].append({
                    "key": key,
                    "value": value
                })
                
                # Add as product attribute if in our list
                if key in ATTRIBUTES_TO_CREATE:
                    matching_attr = next(
                        (attr for attr in existing_attributes if attr['name'].lower() == key.lower()),
                        None
                    )
                    
                    if matching_attr:
                        wc_product["attributes"].append({
                            "id": matching_attr['id'],
                            "name": key,
                            "position": 0,
                            "visible": True,
                            "variation": False,
                            "options": [str(value)]
                        })

        # Create product
        response = requests.post(
            PRODUCTS_URL,
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            headers={"Content-Type": "application/json"},
            json=wc_product,
            timeout=60
        )

        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create product '{product_name}': {response.status_code} - {response.text}")
            return False

        created_product = response.json()
        product_id = created_product['id']
        print(f"✅ Product '{product_name}' created successfully (ID: {product_id})")

        # Handle images
        valid_images = []
        main_image = product_data.get('main_image')
        if is_valid_image_url(main_image):
            valid_images.append({"src": main_image, "position": 0})
        
        for idx, img_url in enumerate(product_data.get('all_images', []), start=1):
            if img_url != main_image and is_valid_image_url(img_url):
                valid_images.append({"src": img_url, "position": idx})

        if valid_images:
            print(f"🖼️ Attempting to add {len(valid_images)} images...")
            update_response = requests.put(
                f"{PRODUCTS_URL}/{product_id}",
                auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
                headers={"Content-Type": "application/json"},
                json={"images": valid_images},
                timeout=60
            )
            
            if update_response.status_code in [200, 201]:
                print(f"  ✅ Images added successfully")
            else:
                print(f"  ⚠️ Could not add images: {update_response.status_code} - {update_response.text}")

        return True

    except Exception as e:
        print(f"❌ Error processing product '{product_name}': {str(e)}")
        return False
    
def process_products():
    """Main function to process products"""
    try:
        # Create attributes first
        existing_attributes = create_attributes()
        if not existing_attributes:
            print("⚠️ Warning: No attributes is available")
        
        # Load existing categories
        print("\n🔍 Fetching existing categories...")
        categories_response = requests.get(
            CATEGORIES_URL,
            auth=(WC_CONSUMER_KEY, WC_CONSUMER_SECRET),
            params={'per_page': 100},
            timeout=30
        )
        
        existing_categories = categories_response.json() if categories_response.status_code == 200 else []
        
        # Create category hierarchy
        print("\n🌳 Creating category hierarchy...")
        created_categories = create_category_hierarchy(existing_categories=existing_categories)
        existing_categories.extend(created_categories)
        print(f"ℹ️ Total categories available: {len(existing_categories)}")

        # Load product data
        print(f"\n📂 Loading products from {SOURCE_FILE}...")
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            products = json.load(f)

        # Process products
        print(f"\n🔄 Starting to process {len(products)} products...")
        success_count = 0
        
        for i, product in enumerate(products, start=1):
            print(f"\n--- Processing product {i}/{len(products)} ---")
            if upload_product(product, existing_categories, existing_attributes):
                success_count += 1
            time.sleep(2)  # Be gentle with the API

        print(f"\n✅ Finished processing. Successfully uploaded {success_count}/{len(products)} products")

    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")

if __name__ == "__main__":
    print("🛒 Starting WooCommerce Product Import")
    print("------------------------------------")
    process_products()
    print("\n✅ Import process completed")




# WooCommerce Website

This project automates product migration between e-commerce websites.

It scrapes product data (such as title, description, images, price, categories, and other details) from a source e-commerce website, imports the products into a WooCommerce store, and can then publish or transfer those products to another e-commerce website.

## Features

- Scrape products from an e-commerce website
- Import products into WooCommerce
- Transfer products to another e-commerce website
- Automate product migration workflow

## Clone the Repository

```bash
git clone https://github.com/JawwadIrshad/woo_commerce_website.git

cd woo_commerce_website
```

## Requirements

- Python 3.10+
- WooCommerce REST API credentials
- Required Python packages (see `requirements.txt`)

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Update the configuration file or environment variables with:

- WooCommerce URL
- Consumer Key
- Consumer Secret
- Source website credentials (if required)

## Run the Project

```bash
python main.py
```

## Project Workflow

1. Scrape products from the source e-commerce website.
2. Process and clean the product data.
3. Upload products to the WooCommerce store.
4. Publish or synchronize products with the destination e-commerce website.

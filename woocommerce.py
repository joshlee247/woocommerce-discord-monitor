import os
from urllib.parse import urljoin
from requests import get
from bs4 import BeautifulSoup
from typing import Dict, List


class WooCommerce:
    @staticmethod
    def format_url(url: str) -> str:
        """
        Remove URL query strings and ensure URL ends with a slash
        """
        url = url.split("?")[0]
        if not url.endswith("/"):
            url += "/"

        return url

    @staticmethod
    def get_collection(url: str) -> List[Dict[str, str]]:
        """
        Get products from a WooCommerce collection (category page)
        """
        url = WooCommerce.format_url(url)

        # Fetch the collection page
        response = get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all products in the collection
        products = []
        for product in soup.find_all('li', class_='product'):
            title = product.find('h4').text.strip()
            product_url = product.find('a', class_='woocommerce-loop-product__link')['href']
            price = product.find('span', class_='woocs_price_USD').text.strip()
            image = product.find('img', class_='wp-post-image')['src']

            products.append({
                "title": title,
                "url": product_url,
                "price": price,
                "image": image
            })

        return products

    @staticmethod
    def get_product(url: str) -> Dict[str, str]:
        """
        Get details of a specific product, including product ID, variant information, and size name
        """
        url = WooCommerce.format_url(url)

        # Fetch the product page
        response = get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product details
        title = soup.find('h1', class_='product_title').text.strip()
        price = soup.find('span', class_='woocs_price_USD').text.strip()
        image = soup.find('img', class_='wp-post-image')['src']
        description = soup.find('div', class_='woocommerce-product-details__short-description').text.strip()

        # Extract the product ID (WooCommerce typically embeds it in a hidden field or in the HTML)
        product_id = soup.find('input', {'name': 'product_id'})['value'] if soup.find('input',
                                                                                      {'name': 'product_id'}) else None
        # Attempt to extract the brand from the product metadata or header (adjust based on the HTML)
        # We search through meta tags or the page for the brand information
        brand = "Unknown Brand"  # Default if brand is not found
        brand_meta = soup.find('meta', {'property': 'og:site_name'})  # Example of meta tag
        if brand_meta:
            brand = brand_meta['content']
        else:
            # Try looking for the brand in other sections, like in a 'div' or product metadata section
            brand_element = soup.find('div', class_='brand')  # Modify this selector based on the HTML
            if brand_element:
                brand = brand_element.text.strip()

        # Get all variations if present (for products with size or other options)
        variants = []
        for variant in soup.find_all('div', class_='product-form-row'):
            # Extracting variant ID
            variant_id = variant.get('data-variation_id')  # Assuming WooCommerce uses 'data-variation_id'

            # Extract the size information from the <dd> inside <dl class="pa pa-pa_size">
            size_element = variant.find('dl', class_='pa pa-pa_size')
            size = size_element.find('dd').text.strip() if size_element else "Unknown size"

            # Extract price and stock status
            price = variant.find('span',
                                 class_='woocs_price_USD').text.strip()  # Assuming this class holds the price
            in_stock = 'in-stock' in variant.find('p', class_='stock').attrs['class'] if variant.find('p',
                                                                                                    class_='stock') else False

            variants.append({
                "id": variant_id,  # Variant ID
                "product_id": product_id,  # Product ID for each variant
                "title": size,  # Extracted size (e.g., "40g can")
                "price": price,
                "available": in_stock
            })

        return {
            "id": product_id,  # Include product ID
            "title": title,
            "brand": brand,
            "price": price,
            "url": url,
            "description": description,
            "type": "Matcha",
            "image": image,
            "variants": variants  # Return the variants with the size included
        }

    @staticmethod
    def get_search_results(url: str, query: str) -> List[Dict[str, str]]:
        """
        Get search results for a query on a WooCommerce store
        """
        url = WooCommerce.format_url(url)
        search_url = f"{url}products/?s={query}"

        # Fetch the search results page
        response = get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Parse products in search results
        products = []
        for product in soup.find_all('li', class_='product'):
            title = product.find('h4').text.strip()
            product_url = product.find('a', class_='woocommerce-loop-product__link')['href']
            price = product.find('span', class_='woocs_price_USD').text.strip()
            image = product.find('img', class_='wp-post-image')['src']

            products.append({
                "title": title,
                "url": product_url,
                "price": price,
                "image": image
            })

        return products

    @staticmethod
    def get_woocommerce_config(url: str) -> Dict[str, str]:
        """
        Get the WooCommerce configuration (like cart information)
        """
        try:
            # WooCommerce typically has this endpoint for cart information
            url = urljoin(url, "/cart/")
            response = get(url)
            return response.json()  # Placeholder, modify based on actual cart endpoint
        except:
            return None

    @staticmethod
    def is_collection(url: str) -> bool:
        """
        Check if the URL points to a valid WooCommerce collection (category)
        """
        try:
            products = WooCommerce.get_collection(url)
            return len(products) > 0
        except:
            return False

    @staticmethod
    def is_product(url: str) -> bool:
        """
        Check if the URL points to a valid WooCommerce product
        """
        try:
            product = WooCommerce.get_product(url)
            return product is not None
        except:
            return False

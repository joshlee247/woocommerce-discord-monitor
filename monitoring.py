from lightbulb import BotApp
from woocommerce import WooCommerce  # Ensure you have replaced Shopify with WooCommerce
from logging import info
from embed import generate_product_embed
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger('product_monitor')
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()  # For console output
file_handler = logging.FileHandler('product_monitor.log')  # For file output

# Set level for handlers
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)

# Create formatter and add to both handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def clean_price(price: str) -> float:
    """
    Remove non-numeric characters from the price and convert it to a float.
    Handles prices like "$12.99" or "USD 12.99".
    """
    return float(price.replace("$", "").replace("USD", "").replace(",", "").strip())


async def check_product(
    bot: BotApp, monitor: dict, product: dict, provider: str
) -> None:
    type = "new"
    announce = False

    for variant in product["variants"]:
        saved_variant = bot.d.variants.find_one(
            monitor_id=monitor["id"], product_id=variant["product_id"], variant_id=variant["id"]
        )

        if saved_variant is None:
            info(f"New variant detected: {variant['id']} - {variant['title']} ({product['title']})")
            bot.d.variants.insert(
                {
                    "monitor_id": monitor["id"],
                    "product_id": variant["product_id"],
                    "variant_id": variant["id"],
                    "title": variant["title"],
                    "brand": product["brand"],  # Include the brand for this variant
                    "available": variant["available"],
                    "price": variant["price"],
                    "created_at": datetime.now().timestamp(),
                    "updated_at": datetime.now().timestamp(),
                }
            )

            type = "new"
            announce = True
        else:
            # Compare availability and price, then log changes, now including brand info
            saved_price = clean_price(saved_variant["price"])
            current_price = clean_price(variant["price"])

            if bool(saved_variant["available"]) != bool(variant["available"]) or saved_price != current_price:
                logger.info(f"Changes detected for variant {variant['id']} - {variant['title']} ({product['title']})")
                bot.d.variants.update(
                    {
                        "monitor_id": monitor["id"],
                        "product_id": variant["product_id"],
                        "variant_id": variant["id"],
                        "title": variant["title"],
                        "brand": product["brand"],  # Ensure the brand is updated
                        "available": variant["available"],
                        "price": variant["price"],
                        "updated_at": datetime.now().timestamp(),
                    },
                    ["monitor_id", "product_id", "variant_id"],
                )

                type = "update"
                announce = True
            else:
                logger.info(f"No changes detected for variant {variant['id']} - {variant['title']} ({product['title']})")

    if announce:
        embed = generate_product_embed(monitor, product, type=type, provider=provider)
        await bot.rest.create_message(monitor["channel_id"], embed=embed)


async def monitor_product(bot: BotApp, monitor: dict) -> None:
    # Fetch product details from WooCommerce, including variants and product ID
    product = WooCommerce.get_product(monitor["url"])
    await check_product(bot, monitor, product, "product")


async def monitor_collection(bot: BotApp, monitor: dict) -> None:
    # Fetch collection details from WooCommerce
    products = WooCommerce.get_collection(monitor["url"])

    for product in products:
        await check_product(bot, monitor, product, "collection")


async def monitor_search(bot: BotApp, monitor: dict) -> None:
    # Fetch search results from WooCommerce
    results = WooCommerce.get_search_results(monitor["url"], monitor["query"])

    for product in results:
        product = WooCommerce.get_product(product["url"])
        await check_product(bot, monitor, product, "search")
from hikari import Embed, Color
from urllib.parse import urlparse, urljoin
from babel.numbers import format_currency


def generate_product_embed(
    monitor: dict, product: dict, type: str, provider: str
) -> Embed:
    url = urlparse(monitor["url"])

    embed = Embed(title=product["title"], url=f"{product['url']}/?currency=USD")
    embed.set_author(
        name=url.hostname,
        url=monitor["url"],
        icon='https://www.marukyu-koyamaen.co.jp/english/shop/wp-content/themes/motoan-shop-en/images/favicon.ico',
    )
    embed.set_image(product["image"])
    embed.add_field(name="Brand", value=product["brand"], inline=True)
    embed.add_field(name="Type", value=product["type"], inline=True)
    embed.add_field(
        name="Price",
        value=format_currency(product["price"].replace("$", ""), monitor["currency"], locale="en_US"),
        inline=True,
    )

    # Create links for each available variant
    variants = [
        f"[{variant['title']}](https://www.marukyu-koyamaen.co.jp/english/shop/cart/checkout/?add-to-cart={variant['id']}&quantity=1&currency=USD)"
        for variant in product["variants"]
        if variant["available"]
    ]

    embed.add_field(
        name="Available variants",
        value=", ".join(variants) if len(variants) > 0 else "None",
        inline=True,
    )

    if type == "new":
        embed.color = Color(0xF8FAFC)
        embed.set_footer(text="🆕 New product")
    elif type == "update":
        if variants:
            embed.color = Color(0x4ADE80)
            embed.set_footer(text="✅ In stock")
        else:
            embed.color = Color(0xF43F5E)
            embed.set_footer(text="❌ Out of stock")

    if provider == "collection":
        embed.set_footer(text=f"{embed.footer.text} | 📦 Collection monitoring")
    elif provider == "product":
        embed.set_footer(text=f"{embed.footer.text} | 📦 Product monitoring")
    elif provider == "search":
        embed.set_footer(text=f"{embed.footer.text} | 🔍 Search monitoring")

    return embed

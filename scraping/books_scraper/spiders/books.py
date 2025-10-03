import re
from urllib.parse import urljoin
import scrapy

RATING_MAP = {"Zero": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,  
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def parse(self, response):
        """
        Page d'accueil : on récupère toutes les catégories (sauf 'Books' racine).
        """
        for href in response.css("div.side_categories ul li ul li a::attr(href)").getall():
            url = urljoin(response.url, href)
            yield scrapy.Request(url, callback=self.parse_category)

    def parse_category(self, response):
        """
        Page de catégorie : suivre chaque livre + pagination.
        """
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            prod_url = urljoin(response.url, href)
            yield scrapy.Request(prod_url, callback=self.parse_book)

        next_rel = response.css("li.next a::attr(href)").get()
        if next_rel:
            next_url = urljoin(response.url, next_rel)
            yield scrapy.Request(next_url, callback=self.parse_category)

    def parse_book(self, response):
        """
        Fiche produit : extraction des champs propres.
        """
        title = response.css(".product_main h1::text").get()

        category = response.css("ul.breadcrumb li:nth-child(3) a::text").get()

        price_text = response.css("p.price_color::text").get() or ""
        price = price_text.strip()

        rating_class = response.css("p.star-rating::attr(class)").get("")  
        rating_word = next((c for c in rating_class.split() if c in RATING_MAP), "Zero")
        rating = RATING_MAP[rating_word]

        avail_texts = response.css("p.instock.availability::text").getall()
        avail_raw = " ".join(t.strip() for t in avail_texts if t.strip())
        m = re.search(r"(\d+)\s+available", avail_raw, flags=re.I)
        available_count = int(m.group(1)) if m else None
        availability = "In stock" if "in stock" in avail_raw.lower() else "Out of stock"

        upc = response.xpath("//th[normalize-space()='UPC']/following-sibling::td/text()").get()

        desc = response.css("#product_description ~ p::text").get(default="") or ""
        desc = desc.replace("\xa0", " ").replace("...more", "").strip()

        rel_img = response.css(".item.active img::attr(src)").get()
        image_url = urljoin(response.url, rel_img) if rel_img else None

        yield {
            "product_page_url": response.url,
            "title": title,
            "category": category,
            "price": price,
            "rating": rating,              
            "availability": availability,  
            "available_count": available_count,
            "upc": upc,
            "description": desc,
            "image_url": image_url,
        }
import scrapy

class BookItem(scrapy.Item):
    product_page_url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    availability = scrapy.Field()
    category = scrapy.Field()
    upc = scrapy.Field()
    description = scrapy.Field()
    image_url = scrapy.Field()
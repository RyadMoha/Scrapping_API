# Scrapy settings for books_scraper project
BOT_NAME = "books_scraper"
SPIDER_MODULES = ["books_scraper.spiders"]
NEWSPIDER_MODULE = "books_scraper.spiders"

# Pipelines
ITEM_PIPELINES = {
    'books_scraper.pipelines.CleanBookPipeline': 300,
}

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

FEED_EXPORT_ENCODING = "utf-8"

FEEDS = {
    'out_detail.csv': {
        'format': 'csv',
        'overwrite': True,
        'fields': [
            'product_page_url',
            'title',
            'category',
            'price',
            'rating',
            'availability',
            'available_count',
            'upc',
            'description',
            'image_url',
        ],
    },
}
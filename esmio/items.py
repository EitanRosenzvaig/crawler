import scrapy


class Item(scrapy.Item):
    created_at = scrapy.Field()
    url = scrapy.Field()
    brand = scrapy.Field()
    breadcrumb = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    code = scrapy.Field()
    price = scrapy.Field()
    sizes = scrapy.Field()
    color = scrapy.Field()
    other = scrapy.Field()
    image_urls = scrapy.Field()
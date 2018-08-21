import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from esmio.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize, sizes_normalize
from esmio.spiders.miocrawler import MioCrawler

class Mishka(MioCrawler):
    name = 'mishka'
    allowed_domains = ['www.mishka.com.ar']

    start_urls = ['https://www.mishka.com.ar/shop/zapatos.html']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        # This page has 1 product per variant of size and color
        links = sel.xpath('.//div[@class="product photo product-item-photo"]/a/@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)


    def parse_item(self, response):
        print("------------- New Item ----------------")
        self.browser.get(response.url)
        time.sleep(5)
        source = self.browser.page_source
        sel = Selector(text=source)
        item = Item()
        item['created_at'] = datetime.now()
        item['url'] = response.url
        item['brand'] = 'mishka'
        item['breadcrumb'] = []
        title = sel.xpath('.//span[@itemprop="name"]/text()').extract()
        item['title'] = html_text_normalize(title)
        item['description'] = html_text_normalize(sel.xpath('.//div[@class="product attribute description"]/div/text()') \
            .extract())
        item['code'] = sel.xpath('.//div[@itemprop="sku"]/text()').extract()[0]
        price = sel.xpath('.//span[contains(@id,"product-price")]/span/text()').extract()[0]
        item['price'] = price_normalize(price)
        sizes = sel.xpath('.//div[@class="swatch-attribute size"]/div[@class="swatch-attribute-options clearfix"]/div/text()') \
            .extract()
        item['sizes'] = sizes_normalize(sizes)
        img_urls_prefix = sel.xpath('.//img[contains(@src, "https://www.mishka.com.ar/media/catalog/product/cache/") and not(contains(@src, "thumb"))]/@src') \
            .extract()[0][:-5]
        thumbnails = len(sel.xpath('.//img[contains(@src, "thumb")]/@src').extract())
        img_urls = list()
        for thumb in range(thumbnails):
            img_url = img_urls_prefix + str(thumb) + '.jpg'
            img_urls.append(img_url)
        item['image_urls'] = img_urls
        yield item
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
from esmio.spiders.miocrawler import MioCrawler


class Converse(MioCrawler):
    name = 'converse'
    allowed_domains = ['www.converse.com.ar']

    start_urls = []
    # Disabled for now
    # start_urls = start_urls + ['http://www.converse.com.ar/productos/mujer/zapatillas-mujer/']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        SCROLL_PAUSE_TIME = 10

        # Get scroll height
        last_height = self.browser.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            nothing = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//div[@class="product-thumb"]/a/@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.browser.get(response.url)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'converse'
            item['breadcrumb'] = ['calzado', 'zapatilla', 'zapatilla urbana']
            item['title'] = sel.xpath('.//h1[@class="entry-title"]/text()').extract()[0]
            item['description'] = None
            item['code'] = sel.xpath('.//p[contains(text(),"SKU")]/text()').extract()[0]
            price = None
            item['sizes'] = None
            item['other'] = None
            item['image_urls'] = sel.xpath('.//div[@class="producto-image"]/img/@src').extract()
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
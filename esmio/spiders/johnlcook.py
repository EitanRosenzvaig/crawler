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


class JohnLCook(MioCrawler):
    name = 'johnlcook'
    allowed_domains = ['shop.johnlcook.com.ar']

    start_urls = ['http://shop.johnlcook.com.ar/cook/winter/sneakers.html']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        SCROLL_PAUSE_TIME = 5

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
        links = sel.xpath('.//a[@class="product-image"]/@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        print("------------- New Item ----------------")
        self.browser.get(response.url)
        source = self.browser.page_source
        sel = Selector(text=source)
        item = Item()
        item['created_at'] = datetime.now()
        item['url'] = response.url
        item['brand'] = 'johnlcook'
        item['breadcrumb'] = None
        item['title'] = sel.xpath('.//h2[@class="name"]/text()').extract()[0]
        item['description'] = sel.xpath('.//div[@id="descripcion"]/child::text()').extract()[-1]
        item['code'] = sel.xpath('.//h2[@class="name"]/following-sibling::p/text()').extract()[0][8:]
        item['price'] = sel.xpath('.//span[@class="price"]/text()').extract()[0]
        sizes = sel.xpath('.//ul[@id="ul-attribute257"]//li//div/@title').extract()
        availability = sel.xpath('.//ul[@id="ul-attribute257"]//li//div/@class').extract()
        available_sizes = list()
        for i in range(len(sizes)):
            if not str(availability[i]) == 'swatch disabledSwatch':
                available_sizes.append(str(sizes[i]))
        item['sizes'] = available_sizes
        item['other'] = None
        item['image_urls'] = sel.xpath('.//li[contains(@class,"moreview")]/child::node()/child::node()/@src').extract()
        yield item
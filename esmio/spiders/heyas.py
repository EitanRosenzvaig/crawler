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

from text_parser import price_normalize, html_text_normalize
from pdb import set_trace as bp
from esmio.spiders.miocrawler import MioCrawler

class Heyas(MioCrawler):
    name = 'heyas'
    allowed_domains = ['www.heyas.com.ar']

    start_urls = ['https://www.heyas.com.ar/shop-online.html?p=' + str(i) + '&tipo_producto=490' for i in range(1,12)]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="product-image"]/@href')
        for link in set(links):
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.browser.get(response.url)
            time.sleep(2)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'heyas'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//div[@class="product-main-info text-center"]//h2/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//div[@class="description"]//text()').extract())
            item['description'] = description
            item['code'] = sel.xpath('.//div[@class="sku"]/text()').extract()[0].replace('SKU# ','')
            price = sel.xpath('.//div[@class="product-main-info text-center"]//span[@class="price"]/text()').extract()
            if len(price) > 1:
                price = price[len(price) - 1]
            else:
                price = price[0]
            item['price'] = price_normalize(price)
            item['sizes'] = sel.xpath('.//div[@class="input-box"]//label[not(contains(@class,"no-stock"))]/text()').extract()
            item['image_urls'] = sel.xpath('.//div[@id="gallery_01"]//a/@data-zoom-image').extract()
            yield item
        else:
            print("-------------- OLD -------------")
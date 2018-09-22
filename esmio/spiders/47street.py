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
from esmio.spiders.miocrawler import MioCrawler

class CuarentiSieteStreet(MioCrawler):
    name = 'cuarentisietestreet'
    allowed_domains = ['47street.com.ar']

    start_urls = ['https://47street.com.ar/accesorios/calzado.html']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="product photo product-item-photo"]/@href')
        for link in links:
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
            item['brand'] = '47street'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//span[@class="base"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@itemprop="description"]/text()').extract())
            item['code'] = sel.xpath('.//div[@itemprop="sku"]/text()').extract()[0].replace('SKU# ', '')
            item['price'] = price_normalize(sel.xpath('.//span[@class="price"]/text()').extract()[0])
            sizes = sel.xpath('.//div[@class="swatch-option text"]/text()').extract()
            item['sizes'] = sizes
            item['image_urls'] = sel.xpath('.//div[@class="imagen"]/img/@src').extract()
            yield item
        else:
            print("-------------- OLD -------------")

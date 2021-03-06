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

class Viamo(MioCrawler):
    name = 'viamo'
    allowed_domains = ['www.viamo.com']

    start_urls = []
    start_urls = start_urls + ['https://www.viamo.com/botin']
    start_urls = start_urls + ['https://www.viamo.com/borcegos']
    start_urls = start_urls + ['https://www.viamo.com/botineta']
    start_urls = start_urls + ['https://www.viamo.com/botas']
    start_urls = start_urls + ['https://www.viamo.com/noche']
    start_urls = start_urls + ['https://www.viamo.com/zapatillas']
    start_urls = start_urls + ['https://www.viamo.com/zapatos']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="productImage thumbnail"]/@href')
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
            item['brand'] = 'viamo'
            item['breadcrumb'] = sel.xpath('.//ul[@class="breadcrumb"]/li//a/text()').extract()
            item['title'] = sel.xpath('.//div[contains(@class,"prodname")]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@class="productDescription"]/text()').extract())
            item['code'] = None
            item['price'] = price_normalize(sel.xpath('.//strong[@class="skuBestPrice"]/text()').extract()[0])
            sizes = sel.xpath('.//label[contains(@class,"dimension-Talle") and not(contains(@class,"unavailable"))]/text()').extract()
            item['sizes'] = sizes
            item['other'] = None
            item['image_urls'] = sel.xpath('.//a[contains(@title,"Zoom")]/@zoom').extract()
            yield item
        else:
            print("-------------- OLD -------------")
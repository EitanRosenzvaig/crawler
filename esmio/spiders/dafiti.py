import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import json

from esmio.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize
from esmio.spiders.miocrawler import MioCrawler

class Dafiti(MioCrawler):
    name = 'dafiti'
    allowed_domains = ['dafiti.com.ar']

    start_urls = ['https://www.dafiti.com.ar/femenino/calzado/?page=' \
        + str(i) for i in range(1,236)]


    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="itm-link"]/@href')
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
            item['brand'] = sel.xpath('.//div[@class="prd-details"]//h2[@itemprop="brand"]/text()').extract()[0]
            item['breadcrumb'] = [] # TODO
            item['title'] = sel.xpath('.//div[@class="prd-details"]//h1[@class="prd-title"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@id="productDetails"]//div[contains(@class,"prd-information")]/text()').extract())
            item['code'] = sel.xpath('.//div[@id="detailSku"]/@data-sku').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//span[@id="price_box"]/text()').extract()[0])
            jsonSizes = sel.xpath('.//div[@class="prd-details"]//ul[contains(@class,"shoe_size")]/li/@data-simple').extract()
            item['sizes'] = self.parseSize(jsonSizes)
            item['image_urls'] = sel.xpath('.//ul[@id="productMoreImagesList"]//li/@data-image-product').extract()
            yield item
        else:
            print("-------------- OLD -------------")

    def parseSize(self, jsonSize):
        print("TYPE: ")
        print(jsonSize)
        sizes = []
        for s in jsonSize:
            size = json.loads(s)
            if(int(size['stock']) > 0 and size['label']):
                sizes.append(size['label'])
        return sizes

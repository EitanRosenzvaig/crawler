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

class CarlaDanelli(MioCrawler):
    name = 'carladanelli'
    allowed_domains = ['www.carladanelli.com.ar']

    start_urls = ['http://www.carladanelli.com.ar/carla-danelli/calzado.html?p=' + str(i) for i in [1,2,3]]

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
            item['brand'] = 'carladanelli'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h2[@class="tituloproducto"]/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//p[@class="descri"]//text()').extract())
            item['description'] = description
            item['code'] = sel.xpath('.//p[@class="numart"]/text()').extract()[0]
            price = sel.xpath('.//span[@class="price"]//text()').extract()
            if len(price)>1:
                price = price[1]
            else:
                price = price[0]
            item['price'] = price_normalize(price)
            
            item['sizes'] = '' # TODO: They have the size per color 
            item['image_urls'] = sel.xpath('.//ul[@id="ul-moreviews"]/li/a/@href').extract()
            yield item
        else:
            print("-------------- OLD -------------")
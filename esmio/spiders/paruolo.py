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

class Paruolo(MioCrawler):
    name = 'paruolo'
    allowed_domains = ['www.paruolo.com.ar']

    start_urls = []
    start_urls = start_urls + ['https://www.paruolo.com.ar/flats.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/fessura-by-paruolo.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/mules.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/bases.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/boots.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/borcegos.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/texanas.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/stilettos.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/night.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/sneakers.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/ankle-boots.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]
    start_urls = start_urls + ['https://www.paruolo.com.ar/50.html?product_list_limit=32&p=' + str(i) for i in range(1,5)]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class = "product photo product-item-photo"]/@href')
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
            item['brand'] = 'paruolo'
            item['breadcrumb'] = [response.url.split('/')[-2]] # EJ: https://www.paruolo.com.ar/flats/z016230-west-rose.html
            item['title'] = sel.xpath('.//span[@class = "base"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//table[@class="data table additional-attributes"]//tr//text()').extract())
            item['code'] = sel.xpath('.//div[@class="product-view-sku"]/text()').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//span[@class="price"]/text()').extract()[0])
            sizes = sel.xpath('.//div[contains(@class,"swatch-option text")]/text()').extract()
            item['sizes'] = sizes
            item['image_urls'] = sel.xpath('.//div[@class="fotorama__stage__shaft fotorama__grab"]/div/@href').extract()
            yield item
        else:
            print("-------------- OLD -------------")
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

class ViaUno(MioCrawler):
    name = 'viauno'
    allowed_domains = ['www.viauno.com.ar']

    start_urls = ['https://www.viauno.com.ar/calzados.html?p=' + str(i) for i in [1,2]]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="product-image"]/@href')
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
            item['brand'] = 'viauno'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//div[@class="product-main-info text-center"]//h1/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@id="collapseOne"]/div/text()').extract())
            item['code'] = sel.xpath('.//span[@class="sku"]/text()').extract()[0].replace('SKU# ', '')
            price = sel.xpath('.//span[@class="special-price"]/span/text()').extract()[0]
            if price is None:
                price = sel.xpath('.//span[@class="price"]/text()').extract()[0]
            item['price'] = price_normalize(price)
            sizes = sel.xpath('.//div[@class="amconf-images-container switcher-field"]//label[not(contains(@class,"no-stock"))]/text()').extract()
            item['sizes'] = sizes
            item['image_urls'] = sel.xpath('.//div[@id="gallery_01"]//li/a/@data-image').extract()
            yield item
        else:
            print("-------------- OLD -------------")
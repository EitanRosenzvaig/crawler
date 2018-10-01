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

class Fotter(MioCrawler):
    name = 'fotter'
    allowed_domains = ['fotter.com.ar']

    start_urls = ['https://fotter.com.ar/zapatos/zapatos-mujeres.html?p=' \
        + str(i) for i in range(1,60)]


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
            item['brand'] = sel.xpath('.//a[@class="brand-link"]/@title').extract_first()
            item['breadcrumb'] = [] # TODO
            item['title'] = sel.xpath('.//h1[@id="product-name"]/text()').extract_first()
            item['description'] = html_text_normalize(sel.xpath('.//div[@id="product-short-description"]//text()').extract())
            item['code'] = sel.xpath('.//p[@id="sku"]/text()').extract_first().replace('SKU# ', '')
            item['price'] = self.getPrice(sel)
            item['sizes'] = sel.xpath('.//div[@class="input-box size"]//option[not(@value="nosize") and not(@value="") and not(@class="no-stock")]/text()').extract()
            item['image_urls'] = sel.xpath('.//div[@id="carousel-product-images"]//li/a/@data-image').extract()
            yield item
        else:
            print("-------------- OLD -------------")

    """
        Hay dos formas distintas en las que aparece el precio. Si tiene descuento
        o sino cambia la estructura del html.
    """
    def getPrice(self, sel):
        priceText = sel.xpath('.//div[@class="product-main-info"]//div[@class="price-box"]/p[@class="special-price"]/span[@class="price"]/text()').extract_first()
        if(priceText is None):
            priceText = sel.xpath('.//div[@class="product-main-info"]//div[@class="price-box"]/span[@class="regular-price"]/span[@class="price"]/text()').extract_first()
        return price_normalize(priceText)

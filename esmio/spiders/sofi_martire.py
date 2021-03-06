import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException

from esmio.items import Item

from pymongo import MongoClient
from text_parser import price_normalize, html_text_normalize
from pdb import set_trace as bp
from esmio.spiders.miocrawler import MioCrawler

class SofiMartire(MioCrawler):
    name = 'sofimartire'
    allowed_domains = ['www.sofimartire.com.ar']

    start_urls = []
    start_urls = start_urls + ['https://www.sofimartire.com.ar/zapatos.html?p='+str(i) for i in range(1,11)]
        
    def get_with_short_wait(self, seconds, url):
        try:
            self.browser.set_page_load_timeout(seconds)
            self.browser.get(url)
        except TimeoutException:
            pass

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.get_with_short_wait(10, response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="product-image"]/@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.get_with_short_wait(10, response.url)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'sofimartire'
            title = sel.xpath('.//div[@class="product-main-info"]//h1/text()').extract()[0]
            item['breadcrumb'] = [title.split(' ', 1)[0]]
            item['title'] = title
            item['description'] = html_text_normalize(sel.xpath('.//div[@id="collapseOne"]/div/text()').extract())
            item['code'] = sel.xpath('.//div[@class="sku"]/text()').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//div[@class="product-main-info"]//span[@class="price"]/text()').extract()[0])
            sizes = sel.xpath('.//label[@class="amconf-color-container amconf-noimage-div"]/text()').extract()
            item['sizes'] = sizes
            item['other'] = None
            item['image_urls'] = sel.xpath('.//a[contains(@data-image,"product/cache")]/@data-zoom-image').extract()
            yield item
        else:
            print("-------------- OLD -------------")
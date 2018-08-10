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


class JohnLCook(CrawlSpider):
    name = 'johnlcook'
    allowed_domains = ['shop.johnlcook.com.ar']

    start_urls = ['http://shop.johnlcook.com.ar/cook/winter/sneakers.html']


    def __init__(self):
        CrawlSpider.__init__(self)
        self.verificationErrors = []
        # self.browser = webdriver.PhantomJS()
        self.browser = webdriver.Chrome()
        self.browser.set_page_load_timeout(120)
        self.connection = MongoClient("localhost", 27017)
        self.comments = self.connection.ropa.items
        self.links = self.connection.ropa.links

    rules = [
        # Rule(LinkExtractor(restrict_xpaths="//a[@class='f-linkNota']"), callback='parse_item', follow=True)
        # Rule(LinkExtractor(allow_domains=allowed_domains), callback='parse_item', follow=True)
    ]

    def flaten_array_of_strings(self, array):
        if len(array) > 0:
            final_string = array[0]
            for i in range(1, len(array)-1):
                final_string += " " + array[i]
            return(final_string)
        else:
            return("")


    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        time.sleep(200) # To Manually scroll down
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
        else:
            print("-------------- OLD -------------")
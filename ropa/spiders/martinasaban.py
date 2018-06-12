import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ropa.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize
from pdb import set_trace as bp

class MartinaSaban(CrawlSpider):
    name = 'martinasaban'
    allowed_domains = ['www.martinasaban.com.ar']

    start_urls = ['https://www.martinasaban.com.ar/category/184999?page=' + str(i) for i in [1,2]]
                


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
        time.sleep(2)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="images TWL img"]/@href')
        for link in links:
            url_txt = 'https://www.martinasaban.com.ar' + link.extract()
            if self.links.find_one({"_id": url_txt}) is None:
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
            item['brand'] = 'martinasaban'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@class="name ng-binding"]/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//div[@class="tab-content"]//text()').extract())
            item['description'] = description
            item['code'] = ''
            item['price'] = price_normalize(sel.xpath('.//p[@class="price ng-binding"]/text()').extract()[0])
            sizes = []
            for size_span in self.browser.find_elements_by_xpath('.//tag-option/a/span'):
                size_span.click()
                time.sleep(0.5)
                actual_size = size_span.text
                if 'Agregar' in sel.xpath('.//button[@id="addItemMyCart"]//span/text()').extract()[0]:
                    sizes.append(actual_size)
            item['sizes'] = sizes
            item['image_urls'] = [url.replace('Square', 'Original') for url in \
                                  sel.xpath('.//li[@class="carousel-item ng-scope"]/img/@src').extract()]
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
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

class HonkyTonk(CrawlSpider):
    name = 'honkytonk'
    allowed_domains = ['www.honkytonkshop.com']

    start_urls = ['https://www.honkytonkshop.com/woman/calzado-woman/']
                


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
            item['brand'] = 'honkytonk'
            item['breadcrumb'] = sel.xpath('.//a[@class="breadcrumb-crumb"]/text()').extract()
            item['title'] = sel.xpath('.//span[contains(@class,"product-name")]/text()').extract()[0]
            item['description'] = ''
            item['code'] = ''
            item['price'] = price_normalize(sel.xpath('.//span[@class="price product-price js-price-display"]/@content').extract()[0])
            sizes = sel.xpath('.//div[contains(./label/text(),"talle")]/select/option/text()').extract()
            if len(sizes) == 0:
                sizes = sel.xpath('.//a[contains(@class,"custom Size")]/span/@data-name').extract()
            item['sizes'] = list(set(sizes))
            img_urls = [url[2:] for url in sel.xpath('.//div[@class="jTscroller scroller-thumbs"]/a/@href').extract()]
            if len(img_urls) == 0:
                img_urls = [url[2:] for url in sel.xpath('.//a[@id="zoom"]/@href').extract()]
            item['image_urls'] = img_urls
            yield item
        else:
            print("-------------- OLD -------------")
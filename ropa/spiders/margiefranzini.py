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

class MargieFranzini(CrawlSpider):
    name = 'margiefranzini'
    allowed_domains = ['www.margiefranzini.com']

    start_urls = ['https://www.margiefranzini.com/_XpO' + str(i) + 'XtOwXvOgalleryxSM' for i in [1,2]]


    def __init__(self):
        CrawlSpider.__init__(self)
        self.verificationErrors = []
        # self.browser = webdriver.PhantomJS()
        self.browser = webdriver.Firefox()
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
        # This page has 1 product per variant of size and color
        links = sel.xpath('.//a[@class="link link2"]/@href')
        for link in links:
            url_txt = 'https://www.margiefranzini.com' + link.extract()
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
            item['brand'] = 'margiefranzini'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@class="title border"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//article[@id="tabDescription"]/p/text()').extract())
            item['code'] = ''
            price = sel.xpath('.//dl[@class="priceInfo clearfix promotionPrice"]//span[@class="ch-price price"]/text()').extract()
            if len(price) == 0:
                price = sel.xpath('.//span[@class="ch-price price"]/text()').extract()[0]
            else:
                price = price[0]
            item['price'] = price_normalize(price)
            item['sizes'] = item['title'][1:3] # Tilte contains size 
            img_urls = sel.xpath('.//li[@role="listitem"]/img/@src').extract()
            item['image_urls'] = [url[2:] for url in img_urls]
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
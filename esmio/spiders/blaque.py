import time
from scrapy.http import Request, FormRequest
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

class Blaque(CrawlSpider):
    name = 'blaque'
    allowed_domains = ['www.blaque.com.ar']

    start_urls = ['https://www.blaque.com.ar/blaque/zapatos.html#/page/6']
                


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
            request = Request(url_txt, callback=self.parse_item)
            yield request

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
            item['brand'] = 'blaque'
            item['breadcrumb'] = ''
            item['title'] = sel.xpath('.//h2[@class="tituloproducto"]/text()').extract()[0]
            description = sel.xpath('.//p[@class="descri"]/text()').extract()
            if len(description) > 0:
                item['description'] = html_text_normalize(description)
            item['code'] = sel.xpath('.//span[@class="numart"]/text()').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//div[@class="descprod"]//div[@class="price-box"]//span[@itemprop="price"]/@content').extract()[0])
            sizes = sel.xpath('.//div[@class="swatchesContainer"]//li/div[not(contains(@class, "disabledSwatch"))]/text()').extract()
            item['sizes'] = sizes
            img_urls = sel.xpath('.//ul[@id="ul-moreviews"]//a[@class="cloud-zoom-gallery"]/@href').extract()
            item['image_urls'] = img_urls
            yield item
        else:
            print("-------------- OLD -------------")
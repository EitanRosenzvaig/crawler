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


class Wanama(CrawlSpider):
    name = 'wanama'
    allowed_domains = ['wanama.com']

    start_urls = ['http://www.wanama.com/wanama/mujer-327.html?p={i}'.format(i=i) for i in range(11)]


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
        if 'www.wanama.com/wanama/' in response.url:
            print("------------- Crawling ----------------")
            self.browser.get(response.url)
            sel = Selector(text=self.browser.page_source)
            links = sel.xpath('.//a[@class="product-image"]/@href')
            for link in links:
                url_txt = link.extract()
                if self.links.find_one({"_id": url_txt}) is None:
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
            item['brand'] = 'wanama'
            item['breadcrumb'] = None
            item['title'] = sel.xpath('.//h1[@id="nombreProducto"]/text()').extract()[0]
            item['description'] = sel.xpath('.//p[@id="descripcion"]/text()').extract()[0]
            item['code'] = sel.xpath('.//p[@id="sku"]/text()').extract()[0]
            item['price'] = sel.xpath('.//span[@class="price"]/text()').extract()[0]
            sizes = sel.xpath('.//ul[@id="ul-attribute251"]//li//div/@title').extract()
            availability = sel.xpath('.//ul[@id="ul-attribute251"]//li//div/@class').extract()
            available_sizes = list()
            for i in range(len(sizes)):
                if not str(availability[i]) == 'swatch disabledSwatch':
                    available_sizes.append(str(sizes[i]))
            item['sizes'] = available_sizes
            item['other'] = None
            item['image_urls'] = sel.xpath('.//li[contains(@class,"moreview")]//div/img[contains(@class,"zoomImg")]/@src').extract()
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
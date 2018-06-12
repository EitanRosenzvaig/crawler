import time
from scrapy.http import Request, FormRequest
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

class XL(CrawlSpider):
    name = 'xl'
    allowed_domains = ['www.xlshop.com.ar']

    start_urls = ['https://www.xlshop.com.ar/calzado']
                


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
        links = sel.xpath('.//li[@class="calzado---xl-extra-large"]//div[@class="image"]/a[not(contains(@href,"cartera"))]/@href')
        for link in links:
            url_txt = link.extract()
            if self.links.find_one({"_id": url_txt}) is None:
                print("------------Found new link: "+str(url_txt))
                price_xpath = './/a[@href="' + url_txt + '"]/span/text()'
                price = sel.xpath(price_xpath).extract()[0]
                request = Request(url_txt, callback=self.parse_item)
                request.meta['price'] = price
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
            item['brand'] = 'xl'
            item['breadcrumb'] = sel.xpath('.//li[@class="last" and @typeof="v:Breadcrumb"]/a/text()').extract()
            item['title'] = sel.xpath('.//div[contains(@class, "fn productName")]/text()').extract()[0]
            description = sel.xpath('.//div[contains(@class, "productDescription")]/text()').extract()
            if len(description) > 0:
                item['description'] = html_text_normalize(description[:-1]) # -1 to exclude code
            item['code'] = sel.xpath('.//div[contains(@class, "productDescription")]/text()').extract()[-1][8:]
            item['price'] = price_normalize(response.meta['price'])
            sizes = sel.xpath('.//div[@class="talles isTalle"]/span[@class="stock"]/text()').extract()
            item['sizes'] = sizes
            img_urls = sel.xpath('.//div[@class="thumbs"]/img/@src').extract()
            item['image_urls'] = ['https://www.xlshop.com.ar/' + url for url in img_urls]
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
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

class MaggioRossetto(CrawlSpider):
    name = 'maggiorossetto'
    allowed_domains = ['maggiorossetto.com']

    start_urls = ['https://maggiorossetto.com/collections/zapatos-1?page=' + str(i) for i in range(1,7)]
                


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
        fetch = self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[contains(@class, "ProductItem__ImageWrapper")]/@href')
        for link in links:
            url_txt = 'https://maggiorossetto.com' + link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            fetch = self.browser.get(response.url)
            time.sleep(2)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'maggiorossetto'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[contains(@class,"ProductMeta__Title")]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[contains(@class,"ProductMeta__Description")]/p/text()').extract())
            item['code'] = ''
            item['price'] = price_normalize(sel.xpath('.//span[contains(@class,"ProductMeta__Price") and not(contains(@class,"compareAt"))]/text()').extract()[0])
            sizes = sel.xpath('.//select[@name="id"]/option[not(@disabled)]/text()').extract()
            item['sizes'] = [size[:2] for size in sizes]
            item['image_urls'] = [url[2:] for url in sel.xpath('.//div[contains(@class, "Product__SlideItem")]//img/@data-original-src').extract()]
            yield item
        else:
            print("-------------- OLD -------------")
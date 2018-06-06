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

class Sarkany(CrawlSpider):
    name = 'sarkany'
    allowed_domains = ['www.rickysarkany.com']

    start_urls = []
    start_urls = start_urls + ['http://www.rickysarkany.com/calzado']
                


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
        print("NOW SCROLLLLLLL!!!!!")
        time.sleep(1)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[contains(@class,"productImage")]/@href')
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
            item['brand'] = 'sarkany'
            js_dict_variable = sel.xpath('//script[contains(.,"categoryName")]/text()').extract()[0]
            # String like --> vtxctx = {skus:"23",.....,categoryName:"Fiesta",....}
            js_dict_variable = js_dict_variable[js_dict_variable.find('categoryName')+14:]
            category = js_dict_variable[:js_dict_variable.find('"')]
            item['breadcrumb'] = [category]
            item['title'] = sel.xpath('.//div[contains(@class,"prodname")]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@class="productDescription"]/text()').extract()[0])
            item['code'] = None
            price = price_normalize(sel.xpath('.//strong[@class="skuBestPrice"]/text()').extract()[0])
            item['price'] = price
            sizes = sel.xpath('.//label[contains(@class,"Talle") and not(contains(@class,"unavailable"))]/text()').extract()
            item['sizes'] = sizes
            item['other'] = None
            item['image_urls'] = sel.xpath('.//a[@id="botaoZoom"]/@rel').extract()
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
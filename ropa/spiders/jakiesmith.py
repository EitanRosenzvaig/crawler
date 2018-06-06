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

class JackieSmith(CrawlSpider):
    name = 'jackiesmith'
    allowed_domains = ['jackiesmith.com.ar']

    start_urls = ['https://www.jackiesmith.com.ar/collections/zapatos']
                


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
        links = sel.xpath('.//div[@class="product"]/a/@href')
        for link in links:
            url_txt = 'https://jackiesmith.com.ar' + link.extract()
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
            item['brand'] = 'jackiesmith'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h3[@class="product-title page-title"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@class="seven columns"]/div[@class="description_style"]//text()').extract())
            item['code'] = sel.xpath('.//div[@class="seven columns"]/p[contains(text(),"SKU")]/text()').extract()[0].replace('SKU : ', '')
            item['price'] = price_normalize(sel.xpath('.//div[@id="price-field"]/span/text()').extract()[0])
            sizes = sel.xpath('.//div[@class="swatch clearfix"]/div[contains(@class,"available")]/@data-value').extract()
            item['sizes'] = sizes
            item['image_urls'] = [url[2:] for url in sel.xpath('.//div[@class="MagicToolboxSelectorsContainer"]/a/@href').extract()]
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
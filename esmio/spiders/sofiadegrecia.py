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
from pdb import set_trace as bp

class SofiaDeGrecia(CrawlSpider):
    name = 'sofiadegrecia'
    allowed_domains = ['www.sofiadegrecia.com.ar']

    start_urls = ['https://www.sofiadegrecia.com.ar/zapatos.html']
                

    next_page = './/div[@class="toolbar-bottom"]//div[@class="pages"]/ol/li[not(a[@class="next i-next"]) and not(a[@class="previous i-previous"])]'

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

    def last_page(self, selector):
        total_pages = selector.xpath(self.next_page+'/a/text()').extract()
        return int(total_pages[len(total_pages)-1])

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = []
        i = 0
        total_pages = self.last_page(sel)
        while i < total_pages:
            page = self.browser.find_elements_by_xpath(self.next_page)[i]
            page.click()
            time.sleep(10)
            sel = Selector(text=self.browser.page_source)
            links += sel.xpath('.//a[@class="product-image"]/@href').extract()
            i+=1
            total_pages = self.last_page(sel)
        for link in set(links):
            url_txt = link.replace('http://','https://')
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
            item['brand'] = 'sofiadegrecia'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@itemprop="name"]/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//div[@itemprop="description"]//text()').extract())
            item['description'] = description
            item['code'] = sel.xpath('.//meta[@itemprop="productID"]/@content').extract()[0]
            price = sel.xpath('.//span[@class="price"]/text()').extract()
            if len(price) > 1:
                price = price[len(price) - 1]
            else:
                price = price[0]
            item['price'] = price_normalize(price)
            item['sizes'] = [html_text_normalize(size) for size in sel.xpath('.//ul[@id="configurable_swatch_talle_calzado"]//span[@class="swatch-label"]/text()').extract()]
            item['image_urls'] = sel.xpath('.//div[@class="product-img-box"]//a/img[not(contains(@src,"thumb"))]/@src').extract()
            yield item
        else:
            print("-------------- OLD -------------")
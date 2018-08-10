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

class JuanitaJo(CrawlSpider):
    name = 'juanitajo'
    allowed_domains = ['juanitajo.com']

    start_urls = ['https://juanitajo.com/93-calzados?id_category=93&n=60']
                


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
        links = sel.xpath('.//a[@class="product_img_link"]/@href')
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
            item['brand'] = 'juanitajo'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@itemprop="name"]/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//div[@itemprop="description"]//text()').extract())
            item['description'] = description
            item['code'] = sel.xpath('.//span[@itemprop="sku"]/text()').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//span[@id="our_price_display"]/text()').extract()[0])
            sizes = []
            for size_span in self.browser.find_elements_by_xpath('.//select[@class="form-control attribute_select no-print"]/option'):
                try:
                    tmp = size_span.click()
                except:
                    pass
                time.sleep(0.5)
                actual_size = size_span.text
                buy_button = self.browser.find_elements_by_xpath('.//p[@id="add_to_cart"]')[0]
                if buy_button.is_enabled():
                    sizes.append(actual_size)
            item['sizes'] = sizes
            item['image_urls'] = [url.replace('-cart_default', '-large_default') for url in \
                                  sel.xpath('.//ul[@id="thumbs_list_frame"]//img/@src').extract()]
            yield item
        else:
            print("-------------- OLD -------------")
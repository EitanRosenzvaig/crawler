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

class Lucerna(CrawlSpider):
    name = 'lucerna'
    allowed_domains = ['www.calzadoslucerna.com.ar']

    start_urls = []
    start_urls = start_urls + ['https://www.calzadoslucerna.com.ar/coleccion/']
                
    more_path = './/a[@id="loadMoreBtn"]'

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
        for clicks in range(10):
            time.sleep(2)
            sel = Selector(text=self.browser.page_source)
            button = self.browser.find_elements_by_xpath(self.more_path)
            if len(button) > 0:
                button = button[0]
                if button.is_enabled():
                    try:
                        button.click()
                    except:
                        continue
                else:
                    break
            else:
                break
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//div[contains(@class,"product-item")]//a[contains(@href,"coleccion") and img]/@href')
        for link in links:
            url_txt = link.extract()
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
            item['brand'] = 'lucerna'
            title = sel.xpath('.//h1[@itemprop="name"]/text()').extract()[0]
            item['title'] = title
            item['breadcrumb'] = [title.split(' ', 1)[0]]
            item['description'] = html_text_normalize(sel.xpath('.//div[@class="description user-content clear"]/p/text()').extract())
            item['code'] = None
            price = price_normalize(sel.xpath('.//span[@id="price_display"]/text()').extract()[0])
            item['price'] = price
            sizes = sel.xpath('.//a[contains(@class,"insta-variations Talle") and span/@class="custom-variants"]/@data-option').extract()[0:5]
            item['sizes'] = sizes
            item['other'] = None
            img_urls = sel.xpath('.//a[contains(@class,"cloud-zoom") and not(contains(@rel,"position"))]/@href').extract()
            img_urls = list(map((lambda x: x[2:]), img_urls))
            item['image_urls'] = img_urls
            yield item
        else:
            print("-------------- OLD -------------")
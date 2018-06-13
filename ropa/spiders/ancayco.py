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
from pdb import set_trace as bp

class AncaYCo(CrawlSpider):
    name = 'ancayco'
    allowed_domains = ['www.ancayco.com.ar']

    start_urls = ['http://www.ancayco.com.ar/store/listing?filter=class:Tienda$0020Online_$0026&page=0']
                
    size_div_path = './/span[@class="attributeSelector"]/div'
    color_div_path = './/div[@class="colorSelector"]/div[contains(@class, "selectableColor")]'
    buy_button_path = './/a[@class="_cartLink button default"]/@style'

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
        links = sel.xpath('.//div[@class="productListing"]//a[contains(@href,"tienda-online")]/@href')
        for link in set(links):
            url_txt = 'http://www.ancayco.com.ar' + link.extract()
            if self.links.find_one({"_id": url_txt}) is None:
                print("------------Found new link: "+str(url_txt))
                yield Request(url_txt, callback=self.parse_item)

    def click_element(self, element):
        try:
            element.click()
        except:
            pass

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
            item['brand'] = 'ancayco'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//div[@class="name uppercase bold"]/text()').extract()[0]
            description = [(text if ('PRODUCTO' not in text and 'MERCADO' not in text) else '') for text in sel.xpath('.//div[@class="lfill top-1"]//text()').extract()]
            description = html_text_normalize(description)
            item['description'] = description
            item['code'] = sel.xpath('.//div[@class="lfill"]/text()').extract()[0].replace('Código ','')
            price = sel.xpath('.//span[@class="_totalContainer left-1"]//text()').extract()
            if len(price) > 0:
                price = price[0]
                item['price'] = price_normalize(price)
            else:
                item['price'] = 0
            sizes = []
            for size_div in self.browser.find_elements_by_xpath(self.size_div_path):
                for color_div in self.browser.find_elements_by_xpath(self.color_div_path):
                    self.click_element(size_div)
                    self.click_element(color_div)
                    time.sleep(1)
                    actual_size = size_div.text
                    source = self.browser.page_source
                    sel = Selector(text=source)
                    buy_button_style = sel.xpath(self.buy_button_path).extract()[0]
                    if not 'display: none;' in buy_button_style:
                        sizes.append(actual_size)
            item['sizes'] = list(set(sizes))
            item['image_urls'] = sel.xpath('.//div[@class="thumbnail"]/a/@href').extract()
            yield item
            self.links.insert({"_id": response.url})
        else:
            print("-------------- OLD -------------")
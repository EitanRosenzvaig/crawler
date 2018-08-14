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
from esmio.spiders.miocrawler import MioCrawler

class Sarkany(MioCrawler):
    name = 'sarkany'
    allowed_domains = ['www.rickysarkany.com']

    start_urls = []
    start_urls = start_urls + ['http://www.rickysarkany.com/calzado']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        SCROLL_PAUSE_TIME = 10

        # Get scroll height
        last_height = self.browser.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            nothing = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[contains(@class,"productImage")]/@href')
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
            item['brand'] = 'sarkany'
            js_dict_variable = sel.xpath('//script[contains(.,"categoryName")]/text()').extract()[0]
            # String like --> vtxctx = {skus:"23",.....,categoryName:"Fiesta",....}
            js_dict_variable = js_dict_variable[js_dict_variable.find('categoryName')+14:]
            category = js_dict_variable[:js_dict_variable.find('"')]
            item['breadcrumb'] = [category]
            item['title'] = sel.xpath('.//div[contains(@class,"prodname")]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@class="productDescription"]/text()').extract()[0])
            item['code'] = None
            price = sel.xpath('.//strong[@class="skuBestPrice"]/text()').extract()
            if len(price) > 0:
                price = price_normalize(price[0])
            else:
                price = 0
            item['price'] = price
            sizes = sel.xpath('.//label[contains(@class,"Talle") and not(contains(@class,"unavailable"))]/text()').extract()
            item['sizes'] = sizes
            item['other'] = None
            item['image_urls'] = sel.xpath('.//a[@id="botaoZoom"]/@rel').extract()
            yield item
        else:
            print("-------------- OLD -------------")
import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC


from esmio.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize

from esmio.spiders.miocrawler import MioCrawler


class Prune(MioCrawler):
    name = 'prune'
    allowed_domains = ['www.prune.com.ar']

    start_urls = []
    start_urls = start_urls + ['https://www.prune.com.ar/zapatos.html?p='+str(i) for i in range(1,10)]
                #'https://www.prune.com.ar/accesorios/ver-todo.html?p='+str(i) for i in range(1,10)

    def is_visible(self, locator, timeout=2):
        try:
            WebDriverWait(self.browser, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
            return True
        except TimeoutException:
            return False

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//div[@class="product photo product-item-photo"]/a//@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    """ Cuidado con algunos items que no tienes variaciones, ej: https://www.prune.com.ar/p703373giaa1039.html"""
    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.browser.get(response.url)
            # wait for sizes and color data to load
            sizes_path = './/div[@role="option"]/text()'
            self.is_visible(sizes_path, timeout=2)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'prune'
            item['breadcrumb'] = sel.xpath('.//title/text()').extract()[0].split(' ', 1)[0]
            item['title'] = sel.xpath('.//div[@class="page-title-wrapper product"]/h1/span/text()').extract()[0]
            sizes = sel.xpath(sizes_path).extract()
            item['sizes'] = sizes
            item['color'] = sel.xpath('.//div[@class="swatch-option color selected"]/@aria-label').extract()
            description = sel.xpath('.//div[@class="product attribute description"]/div/ul').extract()
            item['description'] = html_text_normalize(description)
            item['code'] = sel.xpath('.//div[@itemprop="sku"]/text()').extract()[0]
            price_str = sel.xpath('.//span[@class="price"]/text()').extract()[0]
            item['price'] = price_normalize(price_str)
            item['other'] = None
            item['image_urls'] = sel.xpath('.//img[@class="img-responsive"]/@src').extract()
            yield item
        else:
            print("-------------- OLD -------------")
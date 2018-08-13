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
from esmio.spiders.miocrawler import MioCrawler

class BrunoManetti(MioCrawler):
    name = 'brunomanetti'
    allowed_domains = ['shop.brunomanetti.com.ar']

    start_urls = ['https://shop.brunomanetti.com.ar/productos/']
                
    buy_button_path = './/div[contains(@class,"js-product-buy-container product-buy")]//input'
    more_path = './/a[@class="js-load-more-btn btn btn-primary full-width-xs"]'
    size_a_path = './/div[@class="js-product-variants row-fluid"]//a[contains(@class,"js-insta-variant btn-variant btn-variant-custom insta-variations insta-variations_btn-custom Talle")]'

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        while True:
            time.sleep(3)
            sel = Selector(text=self.browser.page_source)
            button = self.browser.find_elements_by_xpath(self.more_path)
            if len(button) > 0 and button[0].is_enabled():
                button[0].click()
            else:
                break
        links = sel.xpath('.//a[@class="product-image"]/@href')
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
            item['brand'] = 'brunomanetti'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//span[@itemprop="name"]/text()').extract()[0]
            description = [sel.xpath('.//h3/strong/font/i/text()').extract()[0]]
            description += sel.xpath('.//p[contains(@style,"color: rgb(51, 51, 51); font-family: sans-serif, Arial, Verdana, ")]//text()').extract()
            if len(description) > 3:
                description = html_text_normalize(description[:len(description)-2])
            item['description'] = description
            item['code'] = ''
            price = sel.xpath('.//span[@id="price_display"]/text()').extract()[0]
            item['price'] = price_normalize(price)
            sizes = []
            for size_a in self.browser.find_elements_by_xpath(self.size_a_path):
                try:
                    tmp = size_a.click()
                except:
                    pass
                time.sleep(0.2)
                actual_size = size_a.text
                buy_button = self.browser.find_elements_by_xpath(self.buy_button_path)[0]
                if buy_button.is_enabled():
                    sizes.append(actual_size)
            item['sizes'] = sizes
            item['image_urls'] = sel.xpath('.//a[@class="cloud-zoom"]/@href').extract()[0][2:]
            yield item
        else:
            print("-------------- OLD -------------")
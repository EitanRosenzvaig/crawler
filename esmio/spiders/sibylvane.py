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

class SibylVane(MioCrawler):
    name = 'sibylvane'
    allowed_domains = ['www.sibylvane.com']

    start_urls = ['http://www.sibylvane.com/catalogo/zapatos?pageindex=' + str(i) for i in range(1,12)]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@id="hplProduct"]/@href')
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
            item['brand'] = 'sibylvane'
            item['breadcrumb'] = []
            item['title'] = html_text_normalize(sel.xpath('.//h3[@class="light-blue"]/text()').extract())
            item['description'] = html_text_normalize(sel.xpath('.//div[@id="ctl00_HTMLContent_pnlDesc"]/p/text()').extract())
            item['code'] = sel.xpath('.//div[@class="ref"]/text()').extract()[0].replace('ref:', '').replace('\n','')
            item['price'] = price_normalize(sel.xpath('.//div[@id="ctl00_HTMLContent_pnlPrice"]/text()').extract()[1])
            sizes = sel.xpath('.//select[@id="ddlSizesPicker"]/option[not(@value="-1") and not(@disabled)]/text()').extract()
            item['sizes'] = sizes
            item['image_urls'] = sel.xpath('.//img[@id="imgProductGallery"]/@data-zoom-image').extract()
            yield item
        else:
            print("-------------- OLD -------------")
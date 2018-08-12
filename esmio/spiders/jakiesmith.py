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

class JackieSmith(MioCrawler):
    name = 'jackiesmith'
    allowed_domains = ['jackiesmith.com.ar']

    start_urls = ['https://www.jackiesmith.com.ar/collections/zapatos']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//div[@class="product"]/a/@href')
        for link in links:
            #print("-.-.-.-.-.-.-.-.- " + str(link.extract()))
            #url_txt = 'https://jackiesmith.com.ar' + link.extract()
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            res = Request(url_txt, callback=self.parse_item)
            yield res

    def parse_item(self, response):
        print("-.-.-.-.- Parsing Item")
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
        else:
            print("-------------- OLD -------------")
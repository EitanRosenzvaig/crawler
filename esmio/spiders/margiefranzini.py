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

from text_parser import price_normalize, html_text_normalize, sizes_normalize
from esmio.spiders.miocrawler import MioCrawler

class MargieFranzini(MioCrawler):
    name = 'margiefranzini'
    allowed_domains = ['www.margiefranzini.com']

    start_urls = [
                  'https://www.margiefranzini.com/_XpO' +
                  str(i) + 'XtOwXvOgalleryxSM' 
                  for i in range(1,11)
                  ]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        # This page has 1 product per variant of size and color
        links = sel.xpath('.//a[@class="link link2"]/@href')
        for link in links:
            url_txt = 'https://www.margiefranzini.com' + link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)


    def parse_item(self, response):
        print("------------- New Item ----------------")
        self.browser.get(response.url)
        source = self.browser.page_source
        sel = Selector(text=source)
        item = Item()
        item['created_at'] = datetime.now()
        item['url'] = response.url
        item['brand'] = 'margiefranzini'
        item['breadcrumb'] = []
        title = sel.xpath('.//h1[@class="title border"]/text()').extract()[0]
        item['title'] = title.replace(' Margie Franzini Shoes ', ' ').replace(' Margie Franzini ',' ')
        item['description'] = html_text_normalize(sel.xpath('.//article[@id="tabDescription"]/p/text()').extract())
        item['code'] = ''
        price = sel.xpath('.//dl[@class="priceInfo clearfix promotionPrice"]//span[@class="ch-price price"]/text()').extract()
        if len(price) == 0:
            price = sel.xpath('.//span[@class="ch-price price"]/text()').extract()[0]
        else:
            price = price[0]
        item['price'] = price_normalize(price)
        sizes = sel.xpath('.//menu/li/span[not(contains(text(),"Talle"))]/text()').extract()
        if len(sizes) == 0:
            sizes = sel.xpath('.//span[@data-idx="1" and contains(text(),"Talle")]/text()').extract()
        item['sizes'] = sizes_normalize(sizes)
        img_urls = sel.xpath('.//li[@role="listitem"]/img/@src').extract()
        item['image_urls'] = [url[2:] for url in img_urls]
        yield item
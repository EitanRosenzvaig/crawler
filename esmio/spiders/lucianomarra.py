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

class LucianoMarra(MioCrawler):
    name = 'lucianomarra'
    allowed_domains = ['lucianomarra.com.ar']

    start_urls = ['https://lucianomarra.com.ar/categoria-producto/clasicos']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/abotinados']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/botinetas']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/stilettos']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/sandalias']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/zuecos']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/botas']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/mules']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/texanas']
    start_urls = start_urls + ['https://lucianomarra.com.ar/categoria-producto/borcegos']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        # This page has 1 product per variant of size and color
        links = sel.xpath('.//article/div/header/a/@href')
        for link in links:
            url_txt = link.extract()
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
        item['brand'] = 'lucianomarra'
        item['breadcrumb'] = []
        title = sel.xpath('.//h1[@itemprop="name"]/span/text()').extract()
        item['title'] = html_text_normalize(title)
        item['description'] = html_text_normalize(sel.xpath('.//div[@id="tab-description"]//text()').extract())
        item['code'] = ''
        price = sel.xpath('.//div[@class="product-price"]/p/ins/span/text()').extract()
        if len(price) == 0:
            price = sel.xpath('.//div[@class="product-price"]/p/span/text()').extract()[0]
        else:
            price = price[0]
        item['price'] = price_normalize(price)
        sizes = sel.xpath('.//div[@class="select_option_label select_option"]/span/text()').extract()
        item['sizes'] = sizes_normalize(sizes)
        img_urls = sel.xpath('.//div[@class="images"]//a[@itemprop="image"]/@href').extract()
        if len(img_urls) ==0:
            img_urls = sel.xpath('.//div[@class="caroufredsel_wrapper"]//li/a/@href').extract()
        item['image_urls'] = img_urls
        yield item
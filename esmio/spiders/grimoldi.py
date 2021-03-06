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

from selenium.common.exceptions import UnexpectedAlertPresentException
from esmio.spiders.miocrawler import MioCrawler

class Grimoldi(MioCrawler):
    name = 'grimoldi'
    allowed_domains = ['www.grimoldi.com']

    start_urls = ['https://www.grimoldi.com/coleccionmujer/#/mujer/calzado']

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        SCROLL_PAUSE_TIME = 5

        # Get scroll height
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        scrolls = 0
        while scrolls < 15:
            # Scroll down to bottom
            nothing = self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@itemprop="url"]/@href')
        for link in links:
            url_txt = 'https://www.grimoldi.com' + link.extract()
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.browser.get(response.url)
            time.sleep(10)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'grimoldi'
            # Get first word of title i.e Abotinadas Berry
            item['breadcrumb'] = sel.xpath('.//title/text()').extract()[0].split(' ', 1)[0]
            item['title'] = sel.xpath('.//span[@id="Nombre"]/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//div[@class="description"]/p/text()').extract())
            # remove generic text
            description = description.split('. Compr', 1)[0]
            item['description'] = description
            item['code'] = None
            item['price'] = price_normalize(sel.xpath('.//label[@id="PrecioSeleccionado"]/text()').extract()[0])
            sizes = sel.xpath('.//select[@id="IdMedidaSeleccionada"]/option/text()').extract()
            item['sizes'] = sizes
            item['other'] = None
            urls = sel.xpath('.//div[@class="productImages"]//li/img/@data-image-url').extract()
            item['image_urls'] = [url[2:] for url in urls]
            yield item
        else:
            print("-------------- OLD -------------")


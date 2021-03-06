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

class Briganti(MioCrawler):
    name = 'briganti'
    allowed_domains = ['www.briganti.com.ar']

    start_urls = ['http://www.briganti.com.ar/mujer/calzado/zapato']
                
    buy_button_path = './/div[contains(@class,"js-product-buy-container product-buy")]//input'
    more_path = './/div[@class="btn_load_more_products"]'
    size_a_path = './/div[@class="js-product-variants row-fluid"]//a[contains(@class,"js-insta-variant btn-variant btn-variant-custom insta-variations insta-variations_btn-custom Talle")]'

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        while True:
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
            item['brand'] = 'briganti'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//div[contains(@class,"fn productName")]/text()').extract()[0]
            description = sel.xpath('.//div[@class="productDescription"]/text()').extract()
            description += sel.xpath('.//div[@id="tab_ficha"]//div[contains(@class, "field")]/div/text()').extract()
            item['description'] = html_text_normalize(description)
            item['code'] = sel.xpath('.//div[contains(@class,"skuReference")]/text()').extract()[0]
            price = sel.xpath('.//strong[@class="skuBestPrice"]/text()').extract()[0]
            item['price'] = price_normalize(price)
            item['sizes'] = sel.xpath('.//label[not(contains(@class, "unavailable")) and contains(@for,"Talle")]/text()').extract()
            item['image_urls'] = list(set(sel.xpath('.//ul[@class="thumbs"]/li/a[@id="botaoZoom" and @title="Zoom"]/@zoom').extract()))
            yield item
        else:
            print("-------------- OLD -------------")
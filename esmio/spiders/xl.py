import time
from scrapy.http import Request, FormRequest
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

class XL(MioCrawler):
    name = 'xl'
    allowed_domains = ['www.xlshop.com.ar']

    start_urls = ['https://www.xlshop.com.ar/calzado']

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
        links = sel.xpath('.//li[@class="calzado---xl-extra-large"]//div[@class="image"]/a[not(contains(@href,"cartera"))]/@href')
        for link in links:
            url_txt = link.extract()
            print("------------Found new link: "+str(url_txt))
            price_xpath = './/a[@href="' + url_txt + '"]/span/text()'
            price = sel.xpath(price_xpath).extract()
            if len(price) > 0:
                price = price[0]
                request = Request(url_txt, callback=self.parse_item)
                request.meta['price'] = price
                yield request
            else:
                print('Item out of stock')

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
            item['brand'] = 'xl'
            item['breadcrumb'] = sel.xpath('.//li[@class="last" and @typeof="v:Breadcrumb"]/a/text()').extract()
            item['title'] = sel.xpath('.//div[contains(@class, "fn productName")]/text()').extract()[0]
            description = sel.xpath('.//div[contains(@class, "productDescription")]/text()').extract()
            code = ''
            if len(description) > 0:
                for i, s in enumerate(description):
                    if 'Código:' in s:
                        start_of_code = s.index('Código:') + 8
                        code = s[start_of_code:]
                        del description[i]
            item['description'] = html_text_normalize(description)
            item['code'] = code
            item['price'] = price_normalize(response.meta['price'])
            sizes = sel.xpath('.//div[@class="talles isTalle"]/span[@class="stock"]/text()').extract()
            item['sizes'] = sizes
            img_urls = sel.xpath('.//div[@class="thumbs"]/img/@src').extract()
            item['image_urls'] = ['https://www.xlshop.com.ar/' + url for url in img_urls]
            yield item
        else:
            print("-------------- OLD -------------")
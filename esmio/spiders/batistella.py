import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from esmio.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize, sizes_normalize
from esmio.spiders.miocrawler import MioCrawler

class Batistella(MioCrawler):
    name = 'batistella'
    allowed_domains = ['calzadosbatistella.com.ar']
    start_urls = ['https://calzadosbatistella.com.ar/shop/6-mujeres#/talle-35-36-37-38-39-40-41']

    def get_next_page_link(self):
        try:
            tags = self.browser.find_element_by_id("pagination_next_bottom") \
                               .find_elements_by_tag_name("a")
            if len(tags) > 0:
                return tags[0]
            else:
                return None
        except NoSuchElementException:
            return None

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        time.sleep(5)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="item-image-link img-wrapper" and not(contains(@href, "accesorios"))]/@href').extract()
        next_page_link = self.get_next_page_link()
        while next_page_link is not None:
            next_page_link.click()
            time.sleep(5)
            sel = Selector(text=self.browser.page_source)
            links += sel.xpath('.//a[@class="item-image-link img-wrapper" and not(contains(@href, "accesorios"))]/@href').extract()
            next_page_link = self.get_next_page_link()
        for link in set(links):
            url_txt = link
            print("------------Found new link: "+str(url_txt))
            yield Request(url_txt, callback=self.parse_item)

    def parse_item(self, response):
        if self.links.find_one({"_id": response.url}) is None:
            print("------------- New Item ----------------")
            self.browser.get(response.url)
            time.sleep(1)
            source = self.browser.page_source
            sel = Selector(text=source)
            item = Item()
            item['created_at'] = datetime.now()
            item['url'] = response.url
            item['brand'] = 'batistella'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@itemprop="name"]/text()').extract()[0]
            description = html_text_normalize(
                sel.xpath('.//div[@class="column push-1-16 col-10-12"]/p/text()').extract() + \
                sel.xpath('.//table[@class="table-right"]//text()').extract()
                )
            item['description'] = description
            item['code'] = sel.xpath('.//span[@itemprop="sku"]/text()').extract()[0]
            item['price'] = price_normalize(sel.xpath('.//span[@itemprop="price"]/text()')
                .extract()[0])
            sizes = sel.xpath('.//select[@class="form-control attribute_select"]/option[@value!=0]/text()').extract()
            item['sizes'] = sizes_normalize(sizes)
            item['image_urls'] = sel.xpath('.//img[@data-src]/@data-src').extract()
            yield item
        else:
            print("-------------- OLD -------------")
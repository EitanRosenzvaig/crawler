#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from scrapy.http import Request
from datetime import datetime
from selenium import webdriver
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from ropa.items import Item

from pymongo import MongoClient

from text_parser import price_normalize, html_text_normalize

class BenditoPie(MioCrawler):
    name = 'benditopie'
    allowed_domains = ['benditopie.com']

    start_urls = ['https://benditopie.com/collections/zapatos-1?page=' + str(i) for i in range(1,7)]
                
    rules = [
        # Rule(LinkExtractor(restrict_xpaths="//a[@class='f-linkNota']"), callback='parse_item', follow=True)
        # Rule(LinkExtractor(allow_domains=allowed_domains), callback='parse_item', follow=True)
    ]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="product-image view-alt"]/@href')
        for link in links:
            url_txt = 'https://benditopie.com/' + link.extract()
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
            item['brand'] = 'benditopie'
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//h1[@itemprop="name"]/text()').extract()[0]
            item['description'] = html_text_normalize(sel.xpath('.//div[@itemprop="description"]//span/text()').extract())
            item['code'] = ''
            item['price'] = price_normalize(sel.xpath('.//span[@itemprop="price"]/text()').extract()[0])
            size_labels = sel.xpath('.//select[@id="ProductSelect-product-template"]/option[not(contains(text(),"gotado"))]/text()').extract()
            item['sizes'] = [label.strip()[:2] for label in size_labels]
            image_urls = sel.xpath('.//ul[@id="ProductThumbs-product-template"]/li/a/@href').extract()
            item['image_urls'] = [url[2:] for url in image_urls]
            yield item
        else:
            print("-------------- OLD -------------")
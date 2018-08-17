import time
from django.template.defaultfilters import slugify
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

class Falabella(MioCrawler):
    name = 'falabella'
    allowed_domains = ['www.falabella.com.ar']
    start_urls = ['https://www.falabella.com.ar/falabella-ar/category/cat20141/Zapatos-de-mujer?isPLP=1&page=' \
        + str(i) for i in range(1,2)]

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        time.sleep(2)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//div[@class="fb-pod-group__item fb-pod-group__item--product"]//a[@class="fb-pod__header-link gridSize-1"]/@href')
        for link in links:
            url_txt = 'https://www.falabella.com.ar' + link.extract()
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
            brand = sel.xpath('.//h6[@class="fb-product-cta__brand fb-stylised-caps"]/text()').extract()[0]
            item['brand'] = slugify(brand)
            item['breadcrumb'] = []
            item['title'] = sel.xpath('.//tr[th[contains(text(),"Modelo")]]/td/text()').extract()[0]
            description = html_text_normalize(sel.xpath('.//table[@class="fb-product-information__specification__table"]//tr[contains(@class,"row-data")]//text()')
                .extract())
            item['description'] = description
            item['code'] = sel.xpath('.//p[@class="fb-product-sets__product-code"]/text()').extract()[0].replace('Código del producto:','')
            item['price'] = price_normalize(sel.xpath('.//p[@class="fb-price" and contains(text(), "Contado")]/text()')
                .extract()[0]
                .replace('Contado',''))
            sizes = sel.xpath('.//select[@class="fb-inline-dropdown__native-dropdown fsrVisible"]/option[@value!=""]/@value').extract()
            item['sizes'] = sizes_normalize(sizes)
            item['image_urls'] = [url[2:] for url in \
                sel.xpath('.//span[@class="fb-pp-gallery-list__link js-pp-zoom-link" and not(span/i[@class="icon-productGalleryMore"])]/@data-image-zoom').extract()]
            yield item
        else:
            print("-------------- OLD -------------")
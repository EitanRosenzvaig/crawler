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

class Natacha(MioCrawler):
    name = 'natacha'
    allowed_domains = ['www.shop.natachaweb.com.ar']

    start_urls = ['https://www.shop.natachaweb.com.ar/ballerinas-zapatillas_qO30122645XoOmaxPriceXtOcXvOgalleryxSM']
    start_urls += ['https://www.shop.natachaweb.com.ar/botinetas_qO29847378XpO' + str(i) + 'XoOmaxPriceXtOcXvOgalleryxSM' for i in [1,2]]
    start_urls += ['https://www.shop.natachaweb.com.ar/mocasines_qO29847363XoOmaxPriceXtOcXvOgalleryxSM']
    start_urls += ['https://www.shop.natachaweb.com.ar/sandalias_qO27522484XoOmaxPriceXtOcXvOgalleryxSM']
    start_urls += ['https://www.shop.natachaweb.com.ar/stilettos_qO28011717XpO' + str(i) + 'XoOmaxPriceXtOcXvOgalleryxSM' for i in [1,2]]
    start_urls += ['https://www.shop.natachaweb.com.ar/zapatos_qO28012797XoOmaxPriceXtOcXvOgalleryxSM']
    start_urls += ['https://www.shop.natachaweb.com.ar/outlet_qO28012241XpO' + str(i) + 'XoOmaxPriceXtOcXvOgalleryxSM' for i in range(1,11)]
                
    buy_button_path = './/div[contains(@class,"js-product-buy-container product-buy")]//input'
    size_a_path = './/div[@class="js-product-variants row-fluid"]//a[contains(@class,"js-insta-variant btn-variant btn-variant-custom insta-variations insta-variations_btn-custom Talle")]'

    def parse(self, response):
        print("------------- Crawling ----------------")
        self.browser.get(response.url)
        sel = Selector(text=self.browser.page_source)
        links = sel.xpath('.//a[@class="secondImage"]/@href')
        for link in links:
            url_txt = 'https://www.shop.natachaweb.com.ar' + link.extract()
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
            item['brand'] = 'natacha'
            breadcrumb = sel.xpath('.//nav/ol/li/a/text()').extract()
            if len(breadcrumb) > 2:
                breadcrumb = breadcrumb[1:-1]
            else:
                breadcrumb = []
            item['breadcrumb'] = breadcrumb
            item['title'] = sel.xpath('.//h1[@class="title border"]/text()').extract()[0].replace('Natacha Zapato Mujer', '')
            description = sel.xpath('.//article[@id="tabDescription"]//text()').extract()
            description = html_text_normalize(description)
            generic_text_start = ' Productos confeccionados'
            if generic_text_start in description:
                description = description[:description.index(generic_text_start)]
            item['description'] = description
            item['code'] = ''
            price = sel.xpath('.//span[@class="ch-price price"]/text()').extract()[0]
            item['price'] = price_normalize(price)
            sizes = sel.xpath('.//div[@id="my-variation-1-container"]//menu[contains(@class,"ch-select-content")]/li/span[not(text()="Talle")]/text()').extract()
            if len(sizes) == 0:
                sizes = [sel.xpath('.//span[contains(text(),"Talle")]/text()').extract()[0].replace('Talle: ','')]
            item['sizes'] = [s for s in sizes if "Sin Stock" not in s] # Cuando no hay un talle queda asi [ "37 - Sin Stock", "39 - Sin Stock", "40 - Sin Stock", "41 - Sin Stock" ]
            img_urls = sel.xpath('.//ul[@class="ch-carousel-list"]/li/img/@src').extract()
            if len(img_urls) > 1:
                img_urls = img_urls[:-1] # Eliminate size table image
            item['image_urls'] = img_urls
            yield item
        else:
            print("-------------- OLD -------------")
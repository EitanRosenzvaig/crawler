import os
from pymongo import MongoClient
from selenium import webdriver
from scrapy.spiders import CrawlSpider


MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING')

"""
    Default Crawler with the base configuration.
"""
class MioCrawler(CrawlSpider):
    
    def __init__(self):
        CrawlSpider.__init__(self)
        self.verificationErrors = []
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        prefs = {"profile.managed_default_content_settings.images":2}
        chrome_options.add_experimental_option("prefs",prefs)
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.browser.set_page_load_timeout(120)
        self.connection = MongoClient(MONGO_CONNECTION_STRING, 27017)
        self.comments = self.connection.esmio.items
        self.links = self.connection.esmio.links

    # TODO: Borrar esto porque aparentemente no se usa.
    def flaten_array_of_strings(self, array):
        if len(array) > 0:
            final_string = array[0]
            for i in range(1, len(array)-1):
                final_string += " " + array[i]
            return(final_string)
        else:
            return("")

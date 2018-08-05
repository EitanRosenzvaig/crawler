from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.spiders import CrawlSpider


"""
    Default Crawler with the base configuration.
"""
class MioCrawler(CrawlSpider):
    
    def __init__(self):
        CrawlSpider.__init__(self)
        self.verificationErrors = []
        
        chrome_options = Options()  
        chrome_options.set_headless(headless=True)
        prefs = {"profile.managed_default_content_settings.images":2}
        chrome_options.add_experimental_option("prefs",prefs)
        self.browser = webdriver.Chrome(chrome_options=chrome_options)  
        self.browser.set_page_load_timeout(120)
        self.connection = MongoClient("localhost", 27017)
        self.comments = self.connection.ropa.items
        self.links = self.connection.ropa.links

    # TODO: Borrar esto porque aparentemente no se usa.
    def flaten_array_of_strings(self, array):
        if len(array) > 0:
            final_string = array[0]
            for i in range(1, len(array)-1):
                final_string += " " + array[i]
            return(final_string)
        else:
            return("")

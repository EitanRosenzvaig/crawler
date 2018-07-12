from scrapy import spiderloader
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

settings = get_project_settings()
spider_loader = spiderloader.SpiderLoader.from_settings(settings)
n_at_a_time = 2
all_spiders = spider_loader.list()

for i in range(0, len(all_spiders), n_at_a_time):
    process = CrawlerProcess(settings)
    spider_batch = all_spiders[i:(i+n_at_a_time)]
    for spider_name in spider_batch:
        print ("Running spider %s" % (spider_name))
        process.crawl(spider_name) 
    process.start()
from twisted.internet import reactor
from scrapy import spiderloader
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient


# settings = get_project_settings()
# spider_loader = spiderloader.SpiderLoader.from_settings(settings)
# n_at_a_time = 5
# all_spiders = spider_loader.list()

# for i in range(0, len(all_spiders), n_at_a_time):
#     process = CrawlerProcess(settings)
#     spider_batch = all_spiders[i:(i+n_at_a_time)]
#     for spider_name in spider_batch:
#         print ("Running spider %s" % (spider_name))
#         process.crawl(spider_name) 
#     process.start()


# Clean up
# Eliminate all new items if the only difference is the timestamp
client = MongoClient('localhost', 27017)
ropa_db = client['ropa']
items = ropa_db['items']

duplicates = items.aggregate([
    { 
        "$group": { 
            "_id": { 
            		 "url": "$url",
            		 "sizes": "$sizes",
            		 "price": "$price"
            		}, 
            "ids": { "$addToSet": "$_id" },
            "count": { "$sum": 1 } 
        }
    }, 
    { "$match": { "count": { "$gt": 1 } } },
    { "$sort": {"url":1, "created_at": 1}}
])

removed = 0
for one_duplicate_set in duplicates:
	ids_to_remove = one_duplicate_set['ids']
	if len(ids_to_remove) > 1:
		items.remove({"_id":{ "$in": ids_to_remove[1:]}})
		removed += len(ids_to_remove) - 1

print("Removed a total of " + str(removed) + " duplicates")
import os
import pymongo

from scrapy.conf import settings
from scrapy.exceptions import DropItem
from scrapy import log

MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING')

class MongoDBPipeline(object):

    def __init__(self):
        connection = pymongo.MongoClient(
            MONGO_CONNECTION_STRING, 
            27017
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        for data in item:
            if not data:
                raise DropItem("Missing data!")
        self.collection.insert(dict(item))
        log.msg("Comment added to MongoDB database!", level=log.DEBUG, spider=spider)
        return item
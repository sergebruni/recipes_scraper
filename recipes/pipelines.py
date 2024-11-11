from pymongo import MongoClient
from datetime import datetime, timezone

class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'recipes')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.recipes_collection = self.db['recipes']
        self.categories_collection = self.db['categories']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        now = datetime.now(timezone.utc).isoformat()
        item['source_updated_at'] = now
        item['record_updated_at'] = now

        existing_record = self.recipes_collection.find_one({'sid': item['sid']})
        if existing_record:
            self.recipes_collection.update_one({'_id': existing_record['_id']}, {'$set': dict(item)})
        else:
            item['record_created_at'] = now
            self.recipes_collection.insert_one(dict(item))
        
        # Update categories
        for tag in item.get('tags', []):
            category = tag['category']
            subcategory = tag['subcategory']
            self.categories_collection.update_one(
                {'category': category},
                {'$addToSet': {'subcategories': subcategory}},
                upsert=True
            )

        return item

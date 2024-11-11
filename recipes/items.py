# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RecipeItem(scrapy.Item):
    sid = scrapy.Field()
    title = scrapy.Field()
    image = scrapy.Field()
    created_by = scrapy.Field()
    created_at = scrapy.Field()
    rating = scrapy.Field()
    reviews_count = scrapy.Field()
    reviews_score = scrapy.Field()
    information = scrapy.Field()
    ingredients = scrapy.Field()
    instructions = scrapy.Field()
    reviews = scrapy.Field()
    tags = scrapy.Field()
    source_updated_at = scrapy.Field()
    record_created_at = scrapy.Field()
    record_updated_at = scrapy.Field()

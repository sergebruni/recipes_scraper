import re
import scrapy
import logging

from scrapy import signals
from scrapy.signalmanager import dispatcher

from datetime import datetime, timezone
from pymongo import MongoClient
from lxml import html

from ..items import RecipeItem

class RecipeSpider(scrapy.Spider):
    name = "recipes"

    start_urls = [
        # Meals
        "https://www.epicurious.com/recipes-menus/best-breakfast-recipes-gallery",
        "https://www.epicurious.com/type/lunch",
        "https://www.epicurious.com/recipes-menus/easy-dinner-ideas",
        "https://www.epicurious.com/recipes-menus/71-easy-dessert-recipes-for-baking-beginners-and-tired-cooks-gallery",
        "https://www.epicurious.com/recipes-menus/easy-cocktails-recipes-drinks-gallery",
        # Extras
        "https://www.epicurious.com/recipes-menus/batch-cocktails",
        "https://www.epicurious.com/holidays-events/easiest-thanksgiving-recipes-gallery"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_scraped = 0
        dispatcher.connect(self.item_scraped, signal=signals.item_scraped)
    
    def item_scraped(self, item, response, spider):
        self.total_scraped += 1
        if self.total_scraped % 10 == 0:
            print(f"Scraped {self.total_scraped} items.")
            self.log(f"Scraped {self.total_scraped} items.", level=logging.INFO)

    def parse(self, response):
        # Extract all recipe links from two types of list pages
        recipe_links = response.css('.grid-layout__content ul li.gallery__slides__slide a::attr(href)').getall()
        if not recipe_links:
            recipe_links = response.css('.summary-list__items .summary-item__hed-link::attr(href)').getall()

        for link in recipe_links:
            yield response.follow(link, self.parse_recipe)

        # Handle pagination for second type of list page
        next_page = response.css('.summary-list__items div[data-testid="summary-list_call-to-action"] div div').xpath('div[3]').css('a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_recipe(self, response):
        item = RecipeItem()

        item['sid'] = response.css('meta[property="og:url"]::attr(content)').get().split('/')[-1]
        item['title'] = response.css('.page__main-content h1::text').get()
        item['image'] = response.css('.page__main-content picture img::attr(src)').get()
        item['created_by'] = response.css('.page__main-content a::text').get()
        item['created_at'] = response.css('.page__main-content time::text').get()

        review_container = response.css('.page__main-content div[data-testid="RatingWrapper"]')
        information_container = response.css('.page__main-content div[data-testid="InfoSliceList"] ul')
        ingredients_container = response.css('.page__main-content div[data-testid="IngredientList"] div')
        instructions_container = response.css('.page__main-content div[data-testid="InstructionsWrapper"] ol li')
        tags_container = response.css('.page__main-content div[data-testid="TagCloudWrapper"]')

        # Extract the rating using regex
        rating_html = response.css('.page__main-content div[data-testid="RatingWrapper"]').xpath('div[1]/p[2]').get()
        rating = None
        if rating_html:
            match = re.search(r'\((\d+)\)', rating_html)
            if match:
                rating = match.group(1)
        
        review_score = 0
        reviews_count = 0
        reviews_nodes = review_container.css('p')
        if len(reviews_nodes) > 0:
            review_score = float(reviews_nodes[0].css('::text').get().strip())
            reviews_count = int(reviews_nodes[1].re_first(r'\d+').strip())

        information_nodes = information_container.css('li')
        information = []
        for node in information_nodes:
            blocks = node.css('div p')
            text_block = []
            for block in blocks:
                text = block.xpath('text()').get()
                text_block.append(text)

            information.append(': '.join(filter(None, text_block)))

        instructions = []
        for node in instructions_container:
            raw_html = node.get()
            tree = html.fromstring(raw_html)
            tree.attrib.pop('class', None)
            tree.tag = 'div'

            instructions.append(html.tostring(tree).decode())

        # Extract ingredients without relying on dynamic classes
        ingredients = [
            node.css('::text').get().strip() 
            for node in ingredients_container[1:]
            if node.css('::text').get() and not node.css('::text').get().startswith('####') and 'Nutritional analysis' not in node.css('::text').get()
        ]

        # Extract reviews without relying on dynamic classes
        reviews_container = response.css('div[data-journey-hook="recipe-footer"] #reviews ul')
        reviews = []
        # Using XPath to get only the direct li children
        reviews_nodes = reviews_container.xpath('./li[descendant::p]')
        for node in reviews_nodes:
            review_text = node.xpath('./p[1]/text()').get()
            review_info_nodes = node.xpath('./ul/li/p')
            review_info = [info.xpath('text()').get() for info in review_info_nodes]

            review = {
                'text': review_text,
                'info': review_info
            }

            reviews.append(review)

        tags = []
        categories_to_update = {}
        for node in tags_container.css('a'):
            href = node.css('::attr(href)').get()
            if href:
                parts = href.strip('/').split('/')
                if len(parts) == 2:
                    category, subcategory = parts
                    tag = {'category': category, 'subcategory': subcategory}
                    tags.append(tag)
                    # Add subcategory to the category
                    if category not in categories_to_update:
                        categories_to_update[category] = []
                    categories_to_update[category].append(subcategory)

        item['sid'] = response.css('meta[property="og:url"]::attr(content)').get().split('/')[-1]
        item['title'] = response.css('.page__main-content h1::text').get()
        item['image'] = response.css('.page__main-content picture img::attr(src)').get()
        item['created_by'] = response.css('.page__main-content a::text').get()
        item['created_at'] = response.css('.page__main-content time::text').get()
        item['rating'] = rating
        item['reviews_count'] = reviews_count
        item['reviews_score'] = review_score
        item['information'] = information
        item['ingredients'] = ingredients
        item['instructions'] = instructions
        item['reviews'] = reviews
        item['tags'] = tags

        yield item

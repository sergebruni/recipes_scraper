import scrapy
import re

from datetime import datetime, timezone
from pymongo import MongoClient
from lxml import html

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
        super(RecipeSpider, self).__init__(*args, **kwargs)
        # Configure MongoDB connection
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['recipes']
        self.collection = self.db['recipes']
        self.category_collection = self.db['categories']
    
    def parse(self, response):       
        # Extract all recipe links from the first type of list page
        recipe_links = response.css('.grid-layout__content ul li.gallery__slides__slide a::attr(href)').getall()

        # # If no links are found, try the second type of list page
        if len(recipe_links) == 0:
            recipe_links = response.css('.summary-list__items .summary-item__hed-link::attr(href)').getall()

        # # Follow each recipe link to parse the recipe details
        for link in recipe_links:
            yield response.follow(link, self.parse_recipe)

        # # Handle pagination for the second type of list page
        next_page = response.css('.summary-list__items div[data-testid="summary-list_call-to-action"] div div').xpath('div[3]').css('a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    
    def parse_recipe(self, response):
        sid = response.css('meta[property="og:url"]::attr(content)').get()
        title = response.css('.page__main-content h1::text').get()
        image = response.css('.page__main-content picture img::attr(src)').get()
        created_by = response.css('.page__main-content a::text').get()
        created_at = response.css('.page__main-content time::text').get()

        review_container = response.css('.page__main-content div[data-testid="RatingWrapper"]')
        information_container = response.css('.page__main-content div[data-testid="InfoSliceList"] ul')
        ingredients_container = response.css('.page__main-content div[data-testid="IngredientList"] div')
        instructions_container = response.css('.page__main-content div[data-testid="InstructionsWrapper"] ol li')
        tags_container = response.css('.page__main-content div[data-testid="TagCloudWrapper"]')

        if sid:
            sid = sid.split('/')[-1]

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

        ingredients = [node.css('::text').get().strip() for node in ingredients_container[1:]]

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

        # Check if title, ingredients, and instructions are not empty
        if title and ingredients and instructions:
            now = datetime.now(timezone.utc).isoformat()

            recipe_data = {
                'sid': sid,
                'title': title,
                'image': image,
                'created_by': created_by,
                'created_at': created_at,
                'rating': review_score,
                'reviews_count': reviews_count,
                'information': information,
                'ingredients': ingredients,
                'instructions': instructions,
                'reviews': reviews,
                'tags': tags,
                'source_updated_at': now,
                'record_updated_at': now
            }

            # Check if the record already exists
            existing_record = self.collection.find_one({'sid': sid})
            if existing_record:
                # Compare the new data with the existing data, ignoring date fields
                update_needed = False
                ignore_keys = {'source_updated_at', 'record_created_at', 'record_updated_at'}
                for key in recipe_data:
                    if key not in ignore_keys and recipe_data[key] != existing_record.get(key):
                        update_needed = True
                        break
                
                if update_needed:
                    # Update only if there are changes
                    self.collection.update_one(
                        {'_id': existing_record['_id']},
                        {'$set': recipe_data}
                    )
                    print(f'Record with sid {sid} updated.')
                else:
                    print(f'No changes detected for record with sid {sid}.')
            else:
                # Insert a new record
                recipe_data['record_created_at'] = now
                self.collection.insert_one(recipe_data)
                print(f'New record with sid {sid} inserted.')

            # Insert or update categories and subcategories
            for category, subcategories in categories_to_update.items():
                existing_category = self.category_collection.find_one({'category': category})
                if existing_category:
                    # Update existing category with new subcategories
                    updated_subcategories = list(set(existing_category.get('subcategories', []) + subcategories))
                    self.category_collection.update_one(
                        {'_id': existing_category['_id']},
                        {'$set': {'subcategories': updated_subcategories}}
                    )
                    print(f'Category {category} updated with new subcategories.')
                else:
                    # Insert new category
                    self.category_collection.insert_one({'category': category, 'subcategories': subcategories})
                    print(f'New category {category} inserted with subcategories.')

            print('======================')
            print('sid:', sid)
            print('title:', title)
            print('created_by:', created_by)
            print('created_at:', created_at)
            print('rating:', rating)
            print('source_updated_at:', now)
            print('record_updated_at:', now)
            print('----------------------')
            print('Recipe Information:')
            print(information)
            print('----------------------')
            print('ingredients:', ingredients)
            print('----------------------')
            print('instructions:', instructions)
            print('----------------------')
            print('reviews:', reviews)
            print('----------------------')
            print('tags:', tags)
            print('======================')

        else:
            print(f'Skipping record with sid {sid} due to missing title, ingredients, or instructions.')

        # Handle pagination for the second type of list page (if needed)
        next_page_button = response.css('.summary-list__nav--next button')
        if next_page_button:
            next_page_url = response.css('.summary-list__nav--next a::attr(href)').get()
            if next_page_url:
                yield response.follow(next_page_url, self.parse)

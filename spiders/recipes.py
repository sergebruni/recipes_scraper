import scrapy
from datetime import datetime, timezone
from pymongo import MongoClient

class RecipeSpider(scrapy.Spider):
    name = "recipes"
    start_urls = [
        "https://www.epicurious.com/recipes-menus/best-breakfast-recipes-gallery",
        "https://www.epicurious.com/type/lunch",
        "https://www.epicurious.com/recipes-menus/easy-dinner-ideas",
        "https://www.epicurious.com/recipes-menus/71-easy-dessert-recipes-for-baking-beginners-and-tired-cooks-gallery",
        "https://www.epicurious.com/recipes-menus/easy-cocktails-recipes-drinks-gallery"
    ]

    def __init__(self, *args, **kwargs):
        super(RecipeSpider, self).__init__(*args, **kwargs)
        # Configure MongoDB connection
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['recipes']
        self.collection = self.db['recipes']
    
    def parse(self, response):
        # Extract all recipe links from the first type of list page
        recipe_links = response.css('.grid-layout__content ul li.gallery__slides__slide a::attr(href)').getall()

        # If no links are found, try the second type of list page
        if len(recipe_links) == 0:
            recipe_links = response.css('.summary-list__items .summary-item__hed-link::attr(href)').getall()

        # Follow each recipe link to parse the recipe details
        for link in recipe_links:
            yield response.follow(link, self.parse_recipe)

        # Handle pagination for the second type of list page
        next_page = response.css('.summary-list__items div[data-testid="summary-list_call-to-action"] div div').xpath('div[3]').css('a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_recipe(self, response):
        sid = response.css('meta[property="og:url"]::attr(content)').get()
        title = response.css('.page__main-content h1::text').get()
        image = response.css('.page__main-content picture img::attr(src)').get()
        created_by = response.css('.page__main-content a::text').get()
        created_at = response.css('.page__main-content time::text').get()

        information_container = response.css('.page__main-content div[data-testid="InfoSliceList"] ul')
        ingredients_container = response.css('.page__main-content div[data-testid="IngredientList"] div')
        instructions_container = response.css('.page__main-content div[data-testid="InstructionsWrapper"] ol li')
        tags_container = response.css('.page__main-content div[data-testid="TagCloudWrapper"]')

        now = datetime.now(timezone.utc).isoformat()

        if sid:
            sid = sid.split('/')[-1]

        information_nodes = information_container.css('li')
        information = []
        for node in information_nodes:
            blocks = node.css('div p')
            text_block = []
            for block in blocks:
                text = block.xpath('text()').get()
                text_block.append(text)

            information.append(': '.join(text_block))

        instructions_nodes = instructions_container.css('p')
        instructions = []
        for node in instructions_nodes:
            text = node.get()
            instructions.append(text)

        ingredients_nodes = ingredients_container.css('div')
        ingredients = []
        for node in ingredients_nodes[1:]:
            text = node.get()
            ingredients.append(text)

        tags_nodes = tags_container.css('a')
        tags = []
        for node in tags_nodes:
            href = node.css('::attr(href)').get()
            if href:
                parts = href.strip('/').split('/')
                if len(parts) == 2:
                    category, subcategory = parts
                    tags.append(subcategory)

        recipe_data = {
            'sid': sid,
            'title': title,
            'image': image,
            'created_by': created_by,
            'created_at': created_at,
            'information': information,
            'ingredients': ingredients,
            'instructions': instructions,
            'tags': tags,
            'source_updated_at': now
        }

        # Check if the record already exists
        existing_record = self.collection.find_one({'sid': sid})
        if existing_record:
            # Compare the new data with the existing data
            update_needed = False
            ignore_keys = {'source_updated_at', 'record_created_at', 'record_updated_at'}
            for key in recipe_data:
                if key not in ignore_keys and recipe_data[key] != existing_record.get(key):
                    update_needed = True
                    break
            
            if update_needed:
                # Update only if there are changes
                recipe_data['record_updated_at'] = now
                self.collection.update_one(
                    {'_id': existing_record['_id']},
                    {'$set': recipe_data}
                )
                print(f'Record with sid {sid} updated.')
            else:
                self.collection.update_one(
                    {'_id': existing_record['_id']},
                    {'$set': {'source_updated_at': now}}
                )
                print(f'No changes detected for record with sid {sid}.')
        else:
            # Insert a new record
            recipe_data['record_created_at'] = now
            recipe_data['record_updated_at'] = now
            self.collection.insert_one(recipe_data)
            print(f'New record with sid {sid} inserted.')
        
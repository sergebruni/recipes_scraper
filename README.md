# Recipe Scraper

This project is a web scraper built using Scrapy to collect recipe data from Epicurious. The scraper extracts the title, author, creation date, ingredients, instructions, nutritional information, and tags from a given recipe page and stores them in a MongoDB database.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/recipe-scraper.git
    cd recipe-scraper
    ```

2. Create a virtual environment and activate it:

    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

4. Install MongoDB:

    - On macOS:
        ```sh
        brew tap mongodb/brew
        brew install mongodb-community@6.0
        ```

    - On Ubuntu:
        ```sh
        sudo apt-get update
        sudo apt-get install -y mongodb
        ```

    - On Windows, download and install MongoDB from [MongoDB Community Server](https://www.mongodb.com/try/download/community).

5. Start MongoDB:

    - On macOS and Linux:
        ```sh
        sudo systemctl start mongod
        sudo systemctl enable mongod
        ```

    - On Windows, start MongoDB from the Services menu or use:
        ```sh
        net start MongoDB
        ```

## Usage

To run the scraper, execute the following command:

```sh
scrapy crawl recipes
```

This command will start the spider, begin scraping the specified recipe pages, and store the scraped data in the MongoDB database `recipes` in the `recipes` collection. It also updates the `categories` collection with unique categories and subcategories.

### Progress Tracking

The scraper logs its progress to the console, showing how many recipes have been scraped so far.

## Project Structure

```plaintext
recipe-scraper/
├── __init__.py
├── items.py             # Defines the data structure for scraped items
├── middlewares.py       # Custom middlewares (if any)
├── pipelines.py         # Handles MongoDB storage
├── settings.py          # Scrapy settings for the project
├── spiders/
│   ├── __init__.py
│   └── recipe_spider.py  # Main spider logic for scraping recipes
├── utils.py             # Helper functions for data cleaning and processing
├── requirements.txt
└── README.md
```

- **`spiders/`**: Contains all spider files.
    - `recipe_spider.py`: Main spider to scrape recipe data.
- **`pipelines.py`**: Manages data persistence in MongoDB.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/my-new-feature`
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

### **Updates and Enhancements**:
- **Added Progress Tracking Section**: Mentioned that progress is logged to the console.
- **Updated Project Structure**: Included `utils.py` and `pipelines.py` for a more complete view of the project.
- **Clarified MongoDB Usage**: Highlighted the collections used (`recipes`, `categories`).
- **Improved Formatting**: Enhanced readability with better section titles and explanations.
# Recipe Scraper

This project is a web scraper built using Scrapy to collect recipe data from Epicurious. The scraper extracts the title, author, creation date, ingredients, instructions, and tags from a given recipe page and stores them in a MongoDB database.

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
scrapy runspider recipes.py
```

This command will start the spider, begin scraping the specified recipe pages, and store the scraped data in the MongoDB database recipes in the recipes collection. It also updates the categories collection with unique categories and subcategories.

### Project Structure

recipe-scraper/
├── __init__.py
├── spiders/
│   ├── __init__.py
│   └── recipes_spider.py
├── requirements.txt
└── README.md

- recipe_scraper/: Contains the Scrapy project files.
    - spiders/: Directory for spider files.
        -    recipes_spider.py: Spider for scraping recipe data.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

1. Fork the repository.
2. Create your feature branch: git checkout -b feature/my-new-feature
3. Commit your changes: git commit -am 'Add some feature'
4. Push to the branch: git push origin feature/my-new-feature
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.


### Explanation:
- **Installation**: Detailed instructions on how to set up the environment and install MongoDB.
- **Usage**: How to run the scraper and what it does.
- **Project Structure**: Overview of the project's file structure.
- **Example Output**: Sample output of the scraper.
- **Contributing**: Instructions for contributing to the project.
- **License**: Information about the project's license.


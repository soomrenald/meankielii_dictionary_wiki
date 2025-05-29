# Meänkieli Dictionary Scraper

This script scrapes the Meänkieli dictionary from the Språkbanken website (https://språk.isof.se/meänkieli/).

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the script:
```bash
python scrape_meankieli.py
```

## Features

- Scrapes word definitions from the Meänkieli dictionary
- Saves results in both JSON and CSV formats
- Includes error handling and logging
- Respects the server by implementing delays between requests

## Output Files

The script generates two files:
- `meankieli_dictionary.json`: Contains the scraped data in JSON format
- `meankieli_dictionary.csv`: Contains the scraped data in CSV format

## Customization

You can modify the `test_words` list in the `main()` function to search for different words. The script will search for each word and save the results.

## Note

Please be respectful of the website's resources and don't make too many requests in a short time period. The script includes a 1-second delay between requests to avoid overwhelming the server. 
# PropertyScraper

[![asciicast](https://asciinema.org/a/ZfGvmQlhOOJraKcSgbyPhEWmV.png)](https://asciinema.org/a/ZfGvmQlhOOJraKcSgbyPhEWmV)

## Description

Displays rental information for a given Airbnb listing url.

For usage run:
```bash
./property_scraper.py --help
```

Findings are stored in an SQLite database table `listings` with the following columns.
- url
- name
- market,
- score),
- review_count
- type
- bed
- bath
- guest
- price
- photo_url
- description
- amenities (CSV)

### NOTE: It appears Airbnb will throttle results. If this occurs a warning will be printed to stderr and the scraper will quit.

## Usage

Requires Python 3

```bash
./property_scraper.py "https://www.airbnb.co.uk/rooms/14531512"
./property_scraper.py urls.txt
echo "https://www.airbnb.co.uk/rooms/14531512" | ./property_scraper.py -
```

## Future Improvements

- [x] CLI flags
- [x] Database storage
- [x] Handle mutiple urls
- [x] Add requirements.txt
- [ ] Proper testing
- [ ] Implement with different libraries and languages to explore performance variations
- [ ] Create Slack bot

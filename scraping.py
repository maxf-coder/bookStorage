import requests
from bs4 import BeautifulSoup
import time
import re
import db_functions
import configs
from datetime import datetime

def soup_maker(url, HEADERS = configs.default_headers, retries = 3):
    for attempt in range(retries):
        try:
            webpage = requests.get(url, headers = HEADERS, timeout=(3,7))
            webpage.raise_for_status()
            return BeautifulSoup(webpage.content, "lxml")
        except requests.exceptions.RequestException as e:
            configs.scraping_logger.warning(f"soup_maker : Unsuccessful attempt to make a soup, error {e} at {url}, attempt {attempt+1}/{retries}")
            time.sleep(1)
            continue
    configs.scraping_logger.error(f"soup_maker : Can not make a soup at {url}")
    return None

def find_all_books(page_url):
#checking if the request is successful
    page_soup = soup_maker(page_url)
    if page_soup is None:
        configs.scraping_logger.error(f"find_all_books : No soup for finding book's links at {page_url}")
        return []
    
#finding all books divs
    cards = page_soup.find_all("div", class_ = "anyproduct-card")
    if len(cards) == 0:
        configs.scraping_logger.error(f"find_all_books : Can't find any book card at {page_url}")
        return []
    books_links = []
#geting every book url
    for card in cards:
        a = card.find('a')
        if a is None:
            configs.scraping_logger.warning(f"find_all_books : Can't find any 'a' tag in a book card at {page_url}")
            continue
        try:
            books_links.append(a["href"])
        except KeyError:
            configs.scraping_logger.warning(f"find_all_books : The tag 'a' in a book card have not attribute 'href' at {page_url}")
    return books_links

def book_props_save(book_url):
#checking if the request is successful
    BookSoup = soup_maker(book_url)
    if BookSoup is None:
        configs.scraping_logger.error(f"book_props_save : No soup for geting book's props at {book_url}")
        return None
    
    props = {}
#geting every propriety from PROPS DIV
    rows = BookSoup.find_all("div", class_ = "row book-props-item")
    if len(rows) == 0:
        configs.scraping_logger.warning(f"book_props_save : Can't find book's props card at {book_url}")
        return None
    for row in rows:
        key = row.find("div", class_ = "book-prop-name").text.strip()
        value = row.find("div", class_ = "book-prop-value").text.strip()
        props[key] = value
    if 'Cod produs' not in props.keys():
        configs.scraping_logger.warning(f"book_props_save : Book at {book_url} have no id")
        return None
    props["id"] = props.pop("Cod produs")
#geting book's NAME
    try:
        props["name"] = BookSoup.find("h1", class_ = "main-title").text.strip()
    except AttributeError:
        props["name"] = None
#geting book's PRICE
    try:
        price_card_text = BookSoup.find("div", class_ = "product-book-price__actual").text
        price = int("".join(re.findall(r"\d+", price_card_text)))
        props["price"] = price
    except AttributeError:
        props["price"] = None
#geting book's URL from librarius
    props["url"] = book_url
#geting book's IMG source
    try:
        props["img_src"] = BookSoup.find("img", class_ = "product-image")["src"]
    except AttributeError:
        props["img_src"] = None
#geting book's STOCK SIZE
    try:
        props["stock_size"] = BookSoup.find("div", class_="product-book-price__stock").text.strip()
    except AttributeError:
        props["stock_size"] = None
    
    db_functions.insert_book_props(props)

if __name__ == "__main__":
    start_time = datetime.now()

    current_page_url = configs.start_page_url

    books_urls = find_all_books(current_page_url)
    for book_url in books_urls:
        book_props_save(book_url)

    end_time = datetime.now()
    print('Duration: {}'.format(end_time - start_time))
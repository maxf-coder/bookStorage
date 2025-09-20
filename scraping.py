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

def book(book_url):
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
        numbers = [n.replace(",", ".") for n in re.findall(r"\d+[\.,]?\d*", price_card_text)]
        if len(numbers) == 1:
            props["price"] = float(numbers[0])
        elif len(numbers) == 3:
            props["price"] = float(numbers[2])
            props["old_price"] = float(numbers[0])
            props["discount"] = int(numbers[1])
        else:
            configs.db_logger.warning(f"book : Unknown price_card type at {book_url}")
            props["price"] = None
    except AttributeError:
        props["price"] = None
#geting book's URL from librarius
    props["url"] = book_url
#geting book's IMG source
    try:
        props["img_src"] = BookSoup.find("img", class_ = "product-image")["src"]
    except (AttributeError, TypeError):
        props["img_src"] = None
#geting book's STOCK SIZE
    try:
        props["stock_size"] = BookSoup.find("div", class_="product-book-price__stock").text.strip()
    except AttributeError:
        props["stock_size"] = None
    
#geting book's disponibility
    disp = {}

    if props["stock_size"] == None or props["stock_size"] == "Stoc epuizat":
        return props, disp
    try:
        disp_table = BookSoup.find("table", class_ = "table table-striped").find("tbody")
        shop_rows = disp_table.find_all("tr")
    except Exception as e:
        configs.scraping_logger.error(f"Can't find disponibility at {book_url} : {e}", exc_info=True)
        return props, disp
    
    for row in shop_rows:
        try:
            tds = row.find_all("td")
            disp[tds[0].text.split()[1]] = tds[2].text.strip()
        except Exception as e:
            configs.scraping_logger.warning(f"Book: {book_url} : {e}", exc_info=True)

    return props, disp

def shop_props(shop_card):
    props = {}
    try:
        props["name"] = shop_card.find("label").text.split(' ')[2]
        divs = shop_card.find_all("div")
        props["adress"] = divs[0].text
        props["phone_number"] = divs[1].text.replace(" ","")
        props["work_hours"] = divs[2].text
    except Exception as e:
        configs.scraping_logger.error(f"shop_props : {e}", exc_info=True)
    return props

def shops_props(url = configs.shops_url):
#checking if the request is successful
    shops_soup = soup_maker(url)
    if shops_soup is None:
        configs.scraping_logger.error(f"shops_props_save : No soup for geting shops props at {url}")
        return None
    
    shops = []
    shop_cards = shops_soup.find_all("div", class_ = "shop-item list-group-item")
    if(len(shop_cards) == 0):
        configs.scraping_logger.error("shops_props_save : Can't find any shops cards")
        return []
    
    for shop_card in shop_cards:
        props = shop_props(shop_card)
        if props:
            shops.append(props)
    return shops

if __name__ == "__main__":
    start_time = datetime.now()

    db_functions.save_shops_props(shops_props())

    books_urls = find_all_books(configs.start_page_url)
    for book_url in books_urls:
        db_functions.save_books_props(book(book_url))

    end_time = datetime.now()
    print('Duration: {}'.format(end_time - start_time))
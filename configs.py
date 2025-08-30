import logging
from logging.handlers import RotatingFileHandler


start_page_url = "https://librarius.md/ro/books/page/1"

default_headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept-Language' : 'ro-RO, ro;q=0.9'}

db_location = "Books_Storage/DataBase/booksDB.db"

scraping_logger = logging.getLogger("scraping_logger")
scraping_logger.setLevel(logging.INFO)
fileFormater = logging.Formatter("%(asctime)s : %(levelname)s : %(message)s")
scraping_fileHandler = RotatingFileHandler("Books_Storage/logs/scraping_logs/scraping.log", maxBytes=1024, backupCount=5)
scraping_fileHandler.setFormatter(fileFormater)
scraping_logger.addHandler(scraping_fileHandler)

db_logger = logging.getLogger("db_logger")
db_logger.setLevel(logging.INFO)
db_fileHandler = RotatingFileHandler("Books_Storage/logs/db_logs/database.log", maxBytes=1024, backupCount=5)
db_fileHandler.setFormatter(fileFormater) 
db_logger.addHandler(db_fileHandler)

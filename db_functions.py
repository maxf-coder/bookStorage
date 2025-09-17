import sqlite3
import configs

def save_books_props(book_props):
    try:
        with sqlite3.connect(configs.db_location) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM books WHERE id = ?", (book_props["id"],))
            if cursor.fetchone() == None:
                cursor.execute("INSERT INTO books (id) VALUES(?)", (book_props["id"],))
            
            cursor.execute("PRAGMA table_info(books)")
            existing_cols = [col[1] for col in cursor.fetchall()]
            
            for key, value in book_props.items():
                if key not in existing_cols:
                    cursor.execute(f'ALTER TABLE books ADD COLUMN "{key}" TEXT')
                cursor.execute(f"""
                    UPDATE books
                    SET "{key}" = ?
                    WHERE id = ?
                """, (value, book_props["id"]))
    except Exception as e:
        configs.db_logger.error(f"insert_book_props : {e}", exc_info=True)

def save_shops_props(shops_props):
    try:
        with sqlite3.connect(configs.db_location) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM shops")
            names = [n[0] for n in cursor.fetchall()]
            for shop in shops_props:
                if shop["name"] not in names:
                    cursor.execute("INSERT INTO shops (name) VALUES(?)", (shop["name"], ))
                cursor.execute("""
                                UPDATE shops
                                SET adress = ?,
                                    phone_number = ?,
                                    work_hours = ?
                                WHERE name = ?
                            """, (shop["adress"], shop["phone_number"], shop["work_hours"], shop["name"], ))
    except Exception as e:
        configs.db_logger.error(f"save_shops_props : {e}", exc_info=True)

def create_tables():
    try:
        with sqlite3.connect(configs.db_location) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books(
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        price INTEGER,
                        img_src TEXT,
                        url TEXT,
                        stock_size TEXT
                        )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shops(
                        name TEXT UNIQUE,
                        adress TEXT,
                        phone_number TEXT,
                        work_hours TEXT
                        )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_shop(
                        book_id INTEGER,
                        shop_id INTEGER,
                        stock_size TEXT,
                        FOREIGN KEY (book_id) REFERENCES books(id),
                        FOREIGN KEY (shop_id) REFERENCES shops(id),
                        PRIMARY KEY (book_id, shop_id)
                        )
            """)
    except Exception as e:
        configs.db_logger.critical(f"{e}", exc_info=True)


if __name__ == "__main__":
   create_tables()
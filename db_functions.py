import sqlite3
import configs

def save_books_props(book):
    props, disp = book
    try:
        with sqlite3.connect(configs.db_location) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM books WHERE id = ?", (props["id"],))
            if cursor.fetchone() == None:
                cursor.execute("INSERT INTO books (id) VALUES(?)", (props["id"],))
            
            cursor.execute("PRAGMA table_info(books)")
            existing_cols = [col[1] for col in cursor.fetchall()]
            
            for key, value in props.items():
                if key not in existing_cols:
                    cursor.execute(f'ALTER TABLE books ADD COLUMN "{key}" TEXT')
                cursor.execute(f"""
                    UPDATE books
                    SET "{key}" = ?
                    WHERE id = ?
                """, (value, props["id"]))
            conn.commit()

            for shop, disponibility in disp.items():
                cursor.execute("""
                               INSERT INTO book_shop (book_id, shop_name, stock_size)
                               VALUES(?,?,?)
                               ON CONFLICT(book_id, shop_name) DO UPDATE
                               SET stock_size = excluded.stock_size""", (props["id"], shop, disponibility))
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
                        price REAL,
                        old_price REAL,
                        discount INTEGER,
                        img_src TEXT,
                        url TEXT,
                        stock_size TEXT
                        )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shops(
                        name TEXT PRIMARY KEY,
                        adress TEXT,
                        phone_number TEXT,
                        work_hours TEXT
                        )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_shop(
                        book_id INTEGER,
                        shop_name TEXT,
                        stock_size TEXT,
                        FOREIGN KEY (book_id) REFERENCES books(id),
                        FOREIGN KEY (shop_name) REFERENCES shops(name),
                        PRIMARY KEY (book_id, shop_name)
                        )
            """)
    except Exception as e:
        configs.db_logger.critical(f"{e}", exc_info=True)


if __name__ == "__main__":
   create_tables()
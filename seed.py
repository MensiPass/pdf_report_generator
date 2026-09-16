import random
import sqlite3
from datetime import date, timedelta

DB_PATH = "report.db"

PRODUCTS = [
    "Laptop Stand",
    "Wireless Mouse",
    "Keyboard",
    "USB-C Hub",
    "Webcam",
    "Headphones",
]


def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Make the script idempotent.
    cursor.execute("DELETE FROM orders")

    for i in range(200):
        customer = f"Customer {i + 1}"
        product = random.choice(PRODUCTS)
        amount = round(random.uniform(5, 200), 2)

        days_ago = random.randint(0, 29)
        created_at = (
            date.today() - timedelta(days=days_ago)
        ).isoformat()

        cursor.execute(
            """
            INSERT INTO orders
                (customer, product, amount, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (customer, product, amount, created_at),
        )

    conn.commit()
    conn.close()

    print("Seeded 200 orders.")


if __name__ == "__main__":
    seed_database()
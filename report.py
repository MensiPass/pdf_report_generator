import json
import sqlite3

DB_PATH = "report.db"


def getReportData():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Total number of orders
    total_orders = cursor.execute("""
        SELECT COUNT(*) AS total_orders
        FROM orders
    """).fetchone()["total_orders"]

    # 2. Total revenue
    total_revenue = cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total_revenue
        FROM orders
    """).fetchone()["total_revenue"]

    # 3. Top 5 products by revenue
    top_products = cursor.execute("""
        SELECT
            product,
            ROUND(SUM(amount), 2) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchall()

    # 4. Orders per day for the last 7 days
    orders_per_day = cursor.execute("""
        SELECT
            created_at,
            COUNT(*) AS orders
        FROM orders
        WHERE created_at >= date('now', '-6 days')
        GROUP BY created_at
        ORDER BY created_at
    """).fetchall()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
    }


if __name__ == "__main__":
    print(json.dumps(getReportData(), indent=2))
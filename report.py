import json
import sqlite3
from pathlib import Path

from playwright.sync_api import sync_playwright

DB_PATH = "report.db"


def getReportData():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_orders = cursor.execute("""
        SELECT COUNT(*) AS total_orders
        FROM orders
    """).fetchone()["total_orders"]

    total_revenue = cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total_revenue
        FROM orders
    """).fetchone()["total_revenue"]

    top_products = cursor.execute("""
        SELECT
            product,
            ROUND(SUM(amount), 2) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """).fetchall()

    orders_per_day = cursor.execute("""
        SELECT
            created_at,
            COUNT(*) AS orders
        FROM orders
        WHERE created_at >= date('now', '-6 days')
        GROUP BY created_at
        ORDER BY created_at
    """).fetchall()

    all_orders = cursor.execute("""
        SELECT
            id,
            customer,
            product,
            amount,
            created_at
        FROM orders
        ORDER BY created_at DESC, id DESC
    """).fetchall()

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "top_products": [dict(row) for row in top_products],
        "orders_per_day": [dict(row) for row in orders_per_day],
        "all_orders": [dict(row) for row in all_orders],
    }


def build_html(data):
    top_products_rows = ""

    for product in data["top_products"]:
        top_products_rows += f"""
        <tr>
            <td>{product["product"]}</td>
            <td>£{product["revenue"]:.2f}</td>
        </tr>
        """

    orders_rows = ""

    for order in data["all_orders"]:
        orders_rows += f"""
        <tr>
            <td>{order["id"]}</td>
            <td>{order["customer"]}</td>
            <td>{order["product"]}</td>
            <td>£{order["amount"]:.2f}</td>
            <td>{order["created_at"]}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Sales Report</title>

        <style>
            @page {{
                size: A4;
                margin: 18mm;
            }}

            body {{
                font-family: Arial, sans-serif;
                font-size: 11px;
                color: #222;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            h2 {{
                margin-top: 25px;
                border-bottom: 1px solid #ccc;
                padding-bottom: 5px;
            }}

            .date {{
                color: #666;
                margin-bottom: 20px;
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }}

            .card {{
                border: 1px solid #ccc;
                padding: 15px;
                flex: 1;
            }}

            .value {{
                font-size: 20px;
                font-weight: bold;
                margin-top: 5px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 6px;
                text-align: left;
            }}

            th {{
                background: #eee;
            }}

            thead {{
                display: table-header-group;
            }}

            tr {{
                break-inside: avoid;
            }}
        </style>
    </head>

    <body>

        <h1>Sales Report</h1>
        <div class="date">Generated: {__import__("datetime").date.today()}</div>

        <div class="summary">
            <div class="card">
                <div>Total Orders</div>
                <div class="value">{data["total_orders"]}</div>
            </div>

            <div class="card">
                <div>Total Revenue</div>
                <div class="value">£{data["total_revenue"]:.2f}</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>

        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody>
                {top_products_rows}
            </tbody>
        </table>

        <h2>Orders Per Day — Last 7 Days</h2>

        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Orders</th>
                </tr>
            </thead>
            <tbody>
                {"".join(
                    f'<tr><td>{item["created_at"]}</td><td>{item["orders"]}</td></tr>'
                    for item in data["orders_per_day"]
                )}
            </tbody>
        </table>

        <h2>All Orders</h2>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>
            </thead>

            <tbody>
                {orders_rows}
            </tbody>
        </table>

    </body>
    </html>
    """


def generate_pdf(output_path=None):
    data = getReportData()
    html = build_html(data)

    if output_path is None:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        pdf_path = reports_dir / "test.pdf"
    else:
        pdf_path = Path(output_path)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()

        page.set_content(html)

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )

        browser.close()

    print(f"PDF created: {pdf_path}")


if __name__ == "__main__":
    generate_pdf()
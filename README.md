# PDF Report Generator

A small FastAPI application that generates sales reports from SQLite data, renders the report as HTML, converts it to PDF with Playwright, stores the PDF artifact, and serves it through an API.

## Features

* SQLite sales dataset with 200 orders
* SQL aggregation queries
* HTML report generation
* PDF generation with Playwright and Chromium
* A4 PDF layout
* Multi-page report with repeating table headers
* Stored PDF artifacts
* FastAPI endpoints for creating and retrieving reports
* Same-day idempotency
* Optional `force` parameter for generating a new report

## Project structure

```text
pdf_report_generator/
├── main.py
├── report.py
├── seed.py
├── report.db
├── reports/
├── .gitignore
└── README.md
```

`report.db` and generated files in `reports/` are ignored by Git.

## Requirements

* Python 3.10+
* FastAPI
* Playwright
* Chromium

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install dependencies:

```bash
pip install fastapi "uvicorn[standard]" playwright
```

Install Chromium:

```bash
python -m playwright install chromium
```

## Seed the database

Run:

```bash
python seed.py
```

The seed script creates the `orders` table and inserts exactly 200 orders.

Running the seed script again deletes the previous rows and creates a fresh set of 200 orders.

The dataset contains:

* customer
* product
* amount
* created_at

The generated dates cover the previous 30 days.

## Run the API

Start FastAPI:

```bash
python -m fastapi dev main.py
```

The API runs at:

```text
http://127.0.0.1:8000
```

## Health check

```bash
curl.exe http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

## Report generation

Create or retrieve today's report:

```bash
curl.exe -X POST http://127.0.0.1:8000/reports
```

The response contains the report ID and file endpoint:

```json
{
  "id": 1,
  "file": "/reports/1/file"
}
```

Open the generated PDF at:

```text
http://127.0.0.1:8000/reports/1/file
```

## Report information

```bash
curl.exe http://127.0.0.1:8000/reports/1
```

The response contains:

* report ID
* stored PDF path
* creation timestamp
* PDF file endpoint

## Unknown report

Requesting a report that does not exist returns HTTP 404:

```bash
curl.exe http://127.0.0.1:8000/reports/999
```

## Idempotency

`POST /reports` checks whether a report has already been generated today.

If one exists, the existing report ID and file link are returned instead of generating another PDF.

This prevents repeated clicks or repeated requests from unnecessarily creating duplicate daily reports.

To intentionally generate a new report, use:

```bash
curl.exe -X POST http://127.0.0.1:8000/reports -H "Content-Type: application/json" -d "{\"force\":true}"
```

The `force` option bypasses the same-day idempotency check and creates a new report.

In a production system, stronger database-level concurrency protection could be added if multiple workers may receive requests simultaneously.

## Aggregation SQL

The report calculates the total number of orders:

```sql
SELECT COUNT(*) AS total_orders
FROM orders;
```

Total revenue:

```sql
SELECT COALESCE(SUM(amount), 0) AS total_revenue
FROM orders;
```

Top five products by revenue:

```sql
SELECT
    product,
    ROUND(SUM(amount), 2) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5;
```

Orders per day during the last seven days:

```sql
SELECT
    created_at,
    COUNT(*) AS orders
FROM orders
WHERE created_at >= date('now', '-6 days')
GROUP BY created_at
ORDER BY created_at;
```

## PDF generation

The application:

1. Reads the SQLite dataset.
2. Calculates the report aggregations.
3. Loads all orders.
4. Builds an HTML document.
5. Uses Playwright and Chromium to render the HTML.
6. Generates an A4 PDF.
7. Stores the PDF under `reports/`.
8. Saves the report metadata in SQLite.
9. Serves the PDF through FastAPI.

The generated report contains:

* total orders
* total revenue
* top five products by revenue
* orders per day for the last seven days
* all orders

The order table uses a repeating table header and prevents individual rows from being split across PDF pages.

## Background jobs

PDF generation is currently synchronous because this is a small assignment and the complete pipeline is simple enough to execute inside the API request.

For a production system, PDF generation should move to a background job when reports become large, generation becomes slow, or many users can request reports simultaneously.

A production implementation could use a job queue such as Inngest, Celery, or another background worker system.

## Example workflow

```text
POST /reports
       |
       v
Check today's report
       |
       +---- exists ----> return existing report
       |
       v
Query SQLite
       |
       v
Build HTML
       |
       v
Playwright / Chromium
       |
       v
Generate PDF
       |
       v
reports/<id>.pdf
       |
       v
Store metadata in SQLite
       |
       v
Return file link
```


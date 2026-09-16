import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
from report import generate_pdf



app = FastAPI()

DB_PATH = "report.db"
REPORTS_DIR = Path("reports")

class ReportRequest(BaseModel):
    force: bool = False

def init_reports_table():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_reports_table()


@app.get("/health")
def health():
    return {"status": "ok"}




@app.post("/reports")
def create_report(request: ReportRequest | None = None):
    if request is None:
        request = ReportRequest()
    if not request.force:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        existing_report = conn.execute(
            """
            SELECT id, path
            FROM reports
            WHERE date(created_at) = date('now')
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        conn.close()

        if existing_report:
            return {
                "id": existing_report["id"],
                "file": f"/reports/{existing_report['id']}/file",
            }

    conn = sqlite3.connect(DB_PATH)

    created_at = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)

    created_at = datetime.now().isoformat()

    cursor = conn.execute(
        """
        INSERT INTO reports (path, created_at)
        VALUES (?, ?)
        """,
        ("", created_at),
    )
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    REPORTS_DIR.mkdir(exist_ok=True)

    pdf_path = REPORTS_DIR / f"{report_id}.pdf"

    try:
        generate_pdf(output_path=pdf_path)
    except Exception:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "DELETE FROM reports WHERE id = ?",
            (report_id,),
        )
        conn.commit()
        conn.close()
        raise

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE reports
        SET path = ?
        WHERE id = ?
        """,
        (str(pdf_path), report_id),
    )

    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    report = conn.execute(
        """
        SELECT id, path, created_at
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    ).fetchone()

    conn.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return {
        "id": report["id"],
        "path": report["path"],
        "created_at": report["created_at"],
        "file": f"/reports/{report['id']}/file",
    }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    report = conn.execute(
        """
        SELECT id, path
        FROM reports
        WHERE id = ?
        """,
        (report_id,),
    ).fetchone()

    conn.close()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    pdf_path = Path(report["path"])

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"report-{report_id}.pdf",
    )
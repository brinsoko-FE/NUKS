from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from runner import run
import psycopg2
import os
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
def submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    org_id: str = Form(...),
):
    result = run(username, password, org_id)
    return templates.TemplateResponse("form.html", {
        "request": request,
        "result": result
    })


@app.get("/pdfs", response_class=HTMLResponse)
def list_pdfs(request: Request):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "pdfstore"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASS", "pass"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432)
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, created_at FROM pdf_files ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return templates.TemplateResponse("pdf_list.html", {
        "request": request,
        "files": rows
    })


@app.get("/pdfs/{pdf_id}")
def download_pdf(pdf_id: int):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "pdfstore"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASS", "pass"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432)
    )
    cursor = conn.cursor()
    cursor.execute("SELECT filename, data FROM pdf_files WHERE id = %s", (pdf_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        filename, data = result
        return StreamingResponse(BytesIO(data), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename={filename}"
        })
    else:
        return {"error": "File not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from typing import Optional, List
import sqlite3
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "books.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

app = FastAPI(title="Books API", version="1.0")

# CORS (front/local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

def as_dict(row):
    return {k: row[k] for k in row.keys()}

@app.get("/books")
def list_books(
    q: Optional[str] = Query(None, description="Recherche plein texte sur title/description"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Optional[str] = Query(None, description="ex: price_asc, price_desc, rating_desc")
):
    sql = "SELECT * FROM books WHERE 1=1"
    params: List = []

    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if min_price is not None:
        sql += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)

    if min_rating is not None:
        sql += " AND rating >= ?"
        params.append(min_rating)

    if max_rating is not None:
        sql += " AND rating <= ?"
        params.append(max_rating)

    order_by = ""
    if sort == "price_asc":
        order_by = " ORDER BY price ASC"
    elif sort == "price_desc":
        order_by = " ORDER BY price DESC"
    elif sort == "rating_desc":
        order_by = " ORDER BY rating DESC"
    elif sort == "rating_asc":
        order_by = " ORDER BY rating ASC"
    elif sort == "title_asc":
        order_by = " ORDER BY title ASC"

    sql += order_by + " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [as_dict(r) for r in rows]

@app.get("/books/{upc}")
def get_book(upc: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM books WHERE upc = ?", (upc,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Book not found")
        return as_dict(row)

@app.get("/stats")
def stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM books").fetchone()["c"]
        per_cat = conn.execute("""
            SELECT category, COUNT(*) AS c, ROUND(AVG(price),2) AS avg_price
            FROM books GROUP BY category ORDER BY c DESC
        """).fetchall()
        return {
            "total": total,
            "by_category": [as_dict(r) for r in per_cat]
        }
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("books.db")

FIX_CATEGORIES = {
    "Spiritality": "Spirituality",
    "Bsiness": "Business",
    "Adlt Fiction": "Adult Fiction",
    "Atobiography": "Autobiography",
    "Seqential Art": "Sequential Art",
    "Hmor": "Humor",
    "New Adlt": "New Adult",
    "Yong Adlt": "Young Adult",
    "Cltral": "Cultural",
    "Sspense": "Suspense",
    "Childrens": "Children's",
    "Womens Fiction": "Women's Fiction",
    "Add a comment": "Nonfiction",
    "Food and Drink": "Food & Drink",
}

def fix_url(u: str) -> str:
    if not u:
        return u
    u = u.replace("/cataloge/", "/catalogue/")
    u = re.sub(r"(?<!:)//", "/", u)
    if u.startswith("http") and "books.toscrape.com" in u:
        return u
    return u

def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("UPDATE books SET price = ROUND(price, 2) WHERE price IS NOT NULL")

    for bad, good in FIX_CATEGORIES.items():
        cur.execute("UPDATE books SET category = ? WHERE category = ?", (good, bad))

    cur.execute(
        """
        UPDATE books
        SET category = TRIM(REPLACE(REPLACE(category, '  ', ' '), '  ', ' '))
        WHERE category IS NOT NULL
        """
    )

    cur.execute("""
        UPDATE books
        SET availability = TRIM(availability)
        WHERE availability IS NOT NULL
    """)
    cur.execute(
        """
        UPDATE books
        SET available_count = 0
        WHERE (
            LOWER(availability) LIKE 'in stock%'
        ) AND (available_count IS NULL OR available_count = '')
        """
    )
    cur.execute("""
        UPDATE books
        SET description = NULLIF(TRIM(description), '')
    """)
    cur.execute("""
        UPDATE books
        SET title = TRIM(title)
    """)

    rows = cur.execute("SELECT upc, product_page_url, image_url FROM books").fetchall()
    for r in rows:
        new_page = fix_url(r["product_page_url"])
        new_img  = fix_url(r["image_url"])
        if new_page != r["product_page_url"] or new_img != r["image_url"]:
            cur.execute("""
                UPDATE books SET product_page_url = ?, image_url = ?
                WHERE upc = ?
            """, (new_page, new_img, r["upc"]))

    cur.execute("""
        UPDATE books
        SET rating = NULL
        WHERE rating NOT BETWEEN 1 AND 5
    """)

    con.commit()

    total = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    bad_urls = cur.execute("""
        SELECT COUNT(*) FROM books
        WHERE product_page_url NOT LIKE 'https://books.toscrape.com/catalogue/%'
    """).fetchone()[0]
    print(f"OK: nettoyé. total={total}, urls_restantes_incorrectes={bad_urls}")

    for row in cur.execute("""
        SELECT category, COUNT(*) c, ROUND(AVG(price),2) avg_price
        FROM books GROUP BY category ORDER BY c DESC
    """).fetchall()[:5]:
        print(dict(row))

    con.close()

if __name__ == "__main__":
    main()
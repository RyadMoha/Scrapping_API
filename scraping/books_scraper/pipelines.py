
import re
from urllib.parse import urljoin


def _to_float_price(val: str) -> float:
    """
    Convertit un prix de type '£52.98' ou '52,98 €' ou '52.98' en float.
    Renvoie None si vide/invalide.
    """
    if val is None:
        return None
    s = str(val).strip()
    s = re.sub(r'[^\d,.\-]', '', s)
    if s.count(',') == 1 and s.count('.') == 0:
        s = s.replace(',', '.')
    if s.count('.') > 1:
        parts = s.split('.')
        s = ''.join(parts[:-1]) + '.' + parts[-1]
    if s.count(',') > 1:
        parts = s.split(',')
        s = ''.join(parts[:-1]) + ',' + parts[-1]
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


_RATING_MAP = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
}

def _parse_rating(val):
    """
    Accepte :
      - 'star-rating Three'
      - 'Three'
      - 3 / '3'
    Retourne int 1..5 ou None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            n = int(val)
            return n if 1 <= n <= 5 else None
        except Exception:
            return None
    s = str(val).strip()
    m = re.search(r'(one|two|three|four|five|[1-5])', s, flags=re.I)
    if not m:
        return None
    key = m.group(1).lower()
    return _RATING_MAP.get(key)


_AVAIL_RE = re.compile(
    r'(in\s*stock|out\s*of\s*stock)?(?:.*?\()?\s*(\d+)\s+available',
    flags=re.I | re.S
)
_IN_STOCK_RE = re.compile(r'in\s*stock', flags=re.I)

def _clean_availability(av_text):
    """
    Nettoie la disponibilité bruyante type:
      'In stock (9 available) In stock In stock ...'
    Retourne tuple: (availability_str, available_count_int)
      availability_str ∈ {'In stock', 'Out of stock', None}
      available_count_int ∈ int (0 si inconnu/out)
    """
    if not av_text:
        return None, 0
    s = ' '.join(str(av_text).split()) 
    m = _AVAIL_RE.search(s)
    count = int(m.group(2)) if m else None
    in_stock = bool(_IN_STOCK_RE.search(s))
    availability = 'In stock' if in_stock else ('Out of stock' if s else None)
    if availability == 'Out of stock':
        count = 0
    if count is None:
        count = 0
    return availability, count


def _clean_description(text: str, max_len: int = 1200) -> str:
    """
    - Supprime doublons fréquents et le '...more'
    - Normalise espaces/UTF-8 (nbsp, BOM, etc.)
    - Tronque proprement à max_len
    """
    if not text:
        return None
    s = str(text)
    s = s.replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')
    s = re.sub(r'\s*\.\.\.\s*more\s*$', '', s, flags=re.I)
    s = re.sub(r'(.{80,400}?)\1+', r'\1', s, flags=re.S)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{2,}', '\n', s)
    s = s.strip()
    if max_len and len(s) > max_len:
        s = s[:max_len].rsplit(' ', 1)[0].rstrip() + '…'
    return s


def _absolute_url(url: str, base: str) -> str:
    if not url:
        return None
    try:
        return urljoin(base, url)
    except Exception:
        return url


class CleanBookPipeline:
    """
    Pipeline de nettoyage pour les items 'book'.
    À activer dans settings.py:
        ITEM_PIPELINES = {
            'yourproject.pipelines.CleanBookPipeline': 300,
        }
    """

    def process_item(self, item, spider):

        base_url = getattr(spider, 'base_url', None)
        if not base_url:
            try:
                base_url = spider.start_urls[0]
            except Exception:
                base_url = 'https://books.toscrape.com/'

        # title
        if item.get('title'):
            item['title'] = ' '.join(str(item['title']).split())

        # category
        if item.get('category'):
            item['category'] = ' '.join(str(item['category']).split())

        # price -> float
        if item.get('price') is not None:
            item['price'] = _to_float_price(item['price'])

        # rating -> int
        if item.get('rating') is not None:
            item['rating'] = _parse_rating(item['rating'])

        # availability + available_count
        availability, count = _clean_availability(item.get('availability'))
        if availability:
            item['availability'] = availability
        # toujours définir available_count si le champ existe dans le projet
        item['available_count'] = int(count or 0)

        # upc -> normalise (majuscules sans espaces)
        if item.get('upc'):
            item['upc'] = str(item['upc']).strip()

        # description -> nettoyage + tronquage
        if item.get('description'):
            item['description'] = _clean_description(item['description'], max_len=1600)

        # product_page_url / image_url -> absolus, trim
        if item.get('product_page_url'):
            item['product_page_url'] = _absolute_url(str(item['product_page_url']).strip(), base_url)
        if item.get('image_url'):
            item['image_url'] = _absolute_url(str(item['image_url']).strip(), base_url)

        return item


import sqlite3

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_page_url TEXT UNIQUE,
    title TEXT,
    category TEXT,
    price REAL,
    rating INTEGER,
    availability TEXT,
    available_count INTEGER,
    upc TEXT,
    description TEXT,
    image_url TEXT
);
"""

UPSERT_SQL = """
INSERT INTO books
(product_page_url, title, category, price, rating, availability, available_count, upc, description, image_url)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(product_page_url) DO UPDATE SET
  title=excluded.title,
  category=excluded.category,
  price=excluded.price,
  rating=excluded.rating,
  availability=excluded.availability,
  available_count=excluded.available_count,
  upc=excluded.upc,
  description=excluded.description,
  image_url=excluded.image_url;
"""

class SQLitePipeline:
    """
    Stockage minimaliste en SQLite (UPsert par URL produit).
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get('SQLITE_DB_PATH', 'books.db')
        return cls(db_path)

    def open_spider(self, spider):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.execute('PRAGMA synchronous=NORMAL;')
        self.conn.execute(CREATE_SQL)
        self.conn.commit()

    def close_spider(self, spider):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def process_item(self, item, spider):
        vals = (
            item.get('product_page_url'),
            item.get('title'),
            item.get('category'),
            item.get('price'),
            item.get('rating'),
            item.get('availability'),
            int(item.get('available_count') or 0),
            item.get('upc'),
            item.get('description'),
            item.get('image_url'),
        )
        self.conn.execute(UPSERT_SQL, vals)
        return item
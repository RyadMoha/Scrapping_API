# 📚 Books Scraping Pipeline

## 🚀 Contexte
Projet académique : collecter des données du site [books.toscrape.com](https://books.toscrape.com) puis les rendre accessibles via une API.

### Étapes :
1. **Scraping (Scrapy)**
   - Récupération des livres (titre, prix, catégorie, disponibilité, rating, etc.)
   - Export CSV (`out_detail.csv`).

2. **Nettoyage**
   - Conversion des prix (`£` → float).
   - Correction des catégories et des URLs.
   - Uniformisation de la disponibilité.

3. **Stockage (SQLite)**
   - Données insérées dans `books.db` (table `books`).
   - Requêtes SQL pour analyser les catégories, prix moyens, etc.

4. **API REST (FastAPI)**
   - Endpoints :
     - `GET /books?limit=10&sort=title_asc` → liste des livres
     - `GET /books/{id}` → détail d’un livre
     - `GET /stats` → stats par catégorie
   - Lancement avec :
     ```bash
     uvicorn scraping.app:app --reload
     ```

---

## 🛠 Installation
```bash
git clone https://github.com/TonPseudo/books_pipeline.git
cd books_pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 📊 Utilisation

1. **Scrapper les données**

```bash
cd scraping
scrapy crawl books -O out_detail.csv
python load_to_sqlite.py
python clean_after_load.py
```

2. **Lancer l'APi**

```bash
uvicorn scraping.app:app --reload
```

3. Tester

  •	http://127.0.0.1:8000/books
	•	http://127.0.0.1:8000/stats

---

## 📂 Arborescence

books_pipeline/
│── scraping/
│   ├── books_scraper/       # projet Scrapy
│   ├── app.py               # FastAPI
│   ├── load_to_sqlite.py    # import CSV → SQLite
│   ├── clean_after_load.py  # nettoyage données
│   ├── books.db             # base SQLite
│── README.md
│── requirements.txt
│── .gitignore


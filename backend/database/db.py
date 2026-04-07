import sqlite3
import json
import os

# Resolve DB path from this file so imports work regardless of process cwd
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BACKEND_ROOT, "database", "auracart.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_products(category, budget, query=None):
    # Strategy 1: Exact category + budget filter
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Try category + budget strictly
    if category and category.lower() != 'unknown':
        cursor.execute('''
            SELECT * FROM products WHERE category = ? AND price_pkr <= ?
        ''', (category.lower(), budget))
        results = [dict(row) for row in cursor.fetchall()]
        if len(results) > 0:
            return results, "Strategy 1: Exact category match + budget"
            
    # 2. Keyword check fallback + budget
    if query:
        terms = f"%{query}%"
        cursor.execute('''
            SELECT * FROM products WHERE (name LIKE ? OR category LIKE ?) AND price_pkr <= ?
        ''', (terms, terms, budget))
        results = [dict(row) for row in cursor.fetchall()]
        if len(results) > 0:
            return results, "Strategy 2: Keyword search across name and category"
            
    # 3. Top-rated items fallback ignoring budget (or up to 300k) limit
    cursor.execute('''
        SELECT * FROM products ORDER BY rating DESC LIMIT 10
    ''')
    results = [dict(row) for row in cursor.fetchall()]
    return results, "Strategy 3: Top-rated products fallback (could not match exactly)"

def get_all_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category, image_emoji FROM products')
    cats = [{"name": row["category"], "emoji": row["image_emoji"]} for row in cursor.fetchall()]
    conn.close()
    return cats

def get_products_by_category(category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE category = ?', (category,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as c FROM products')
    total = cursor.fetchone()["c"]
    cursor.execute('SELECT COUNT(DISTINCT category) as c FROM products')
    cats = cursor.fetchone()["c"]
    cursor.execute('SELECT AVG(rating) as r FROM products')
    avg_rating = round(cursor.fetchone()["r"], 2)
    conn.close()
    return {
        "total_products": total,
        "categories_count": cats,
        "avg_rating": avg_rating
    }

def verify_database():
    """Log category counts at startup for debugging empty-result issues."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) as cnt FROM products GROUP BY category ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    print("Database contents (category counts):")
    for row in rows:
        print(f"  {row['category']}: {row['cnt']} products")
    return rows


def save_feedback(query, result_id, rating, comment):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO feedback (query, result_id, rating, comment) VALUES (?, ?, ?, ?)', (query, result_id, rating, comment))
    conn.commit()
    conn.close()
    return True

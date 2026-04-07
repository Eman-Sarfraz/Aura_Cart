import sqlite3
import json

def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            price REAL,
            specs TEXT,
            rating REAL,
            reviews_mock TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        dummy_products = [
            ("iPhone 15 Pro", "Smartphone", 120000, json.dumps({"battery": "3274 mAh", "performance": "A17 Pro"}), 4.8, "['Amazing camera', 'Battery life could be better', 'Premium build']"),
            ("Samsung Galaxy S24 Ultra", "Smartphone", 130000, json.dumps({"battery": "5000 mAh", "performance": "Snapdragon 8 Gen 3"}), 4.9, "['Best Android phone', 'A bit heavy', 'Stylus is great']"),
            ("MacBook Pro M3", "Laptop", 250000, json.dumps({"ram": "16GB", "storage": "512GB", "use": "gaming and programming"}), 4.9, "['Incredible for programming', 'Expensive', 'Amazing battery']"),
            ("Dell XPS 15", "Laptop", 200000, json.dumps({"ram": "16GB", "storage": "1TB", "use": "programming"}), 4.7, "['Great display', 'Gets hot during gaming', 'Good keyboard']"),
            ("ASUS ROG Zephyrus G14", "Laptop", 180000, json.dumps({"ram": "16GB", "storage": "1TB", "use": "gaming"}), 4.8, "['Perfect for gaming', 'Loud fans', 'Portable']"),
            ("Google Pixel 8", "Smartphone", 85000, json.dumps({"battery": "4575 mAh", "performance": "Tensor G3"}), 4.6, "['Great camera', 'Battery life is average', 'Clean UI']"),
            ("Sony WH-1000XM5", "Headphones", 35000, json.dumps({"type": "over-ear", "anc": "yes"}), 4.8, "['Best ANC', 'Comfortable', 'Expensive']"),
            ("Xiaomi Redmi Note 13", "Smartphone", 40000, json.dumps({"battery": "5000 mAh", "performance": "Snapdragon 685"}), 4.3, "['Great budget pick', 'Average camera', 'Good battery']"),
        ]
        cursor.executemany('''
            INSERT INTO products (name, category, price, specs, rating, reviews_mock)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', dummy_products)
        print("Inserted dummy products into the database.")
    else:
        print("Database already initialized.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

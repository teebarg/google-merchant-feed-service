import os
import psycopg2
from psycopg2.extras import RealDictCursor

def fetch_products():
    """
    Fetch products from PostgreSQL and map fields for Google Merchant feed.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            p.id,
            p.sku,
            p.name AS title,
            p.description,
            v.price,
            v.old_price,
            pi.image AS image_url,
            p.is_new,
            v.color,
            v.size,
            v.age,
            v.measurement,
            p.active AS is_active
        FROM products p
        LEFT JOIN LATERAL (
            SELECT * FROM product_variants
            WHERE product_id = p.id
            ORDER BY id ASC
            LIMIT 1
        ) v ON true
        LEFT JOIN LATERAL (
            SELECT * FROM product_images
            WHERE product_id = p.id
            ORDER BY "order" ASC
            LIMIT 1
        ) pi ON true
        WHERE p.active = TRUE
        LIMIT 2
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Optionally, convert to list of dicts for Google Sheets
    products = []
    for row in rows:
        products.append({
            "id": row["sku"],
            "title": row["title"],
            "description": row["description"] or "",
            "availability": "in_stock",
            "link": f"https://www.revoque.com.ng/products/{row['sku']}",
            "image link": row["image_url"] or "",
            "price": float(row["price"]) if row["price"] else 0.0,
            "identifier exists": "no",
            "gtin": "",
            "mpn": "",
            "brand": "Revoque",
            "product highlight": "",
            "product detail": "",
            "additional image link": "",
            "condition": "new" if row["is_new"] else "thrift",
            "adult": "no",
            "color": row["color"] or "",
            "size": row["size"] or "",
            "gender": "female",
            "material": "100% Cotton",
            "pattern": "",
            "age group": row["age"] or "",
            "multipack": "",
            "is bundle": "no",
            "unit pricing measure": "",
            "unit pricing base measure": "",
            "energy efficiency class": "",
            "min energy efficiency class": "",
            "max energy efficiency class": "",
            "item group id": "",
            "sell on google quantity": "1",
            "is_active": row["is_active"]
        })

    return products


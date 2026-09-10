import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from document_store import DocumentDB

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DB_PATH = os.path.join(BASE_DIR, "data", "ecommerce_sql.db")
NOSQL_DIR = os.path.join(BASE_DIR, "data", "nosql_store")


class ECommerceService:
    """The hybrid application layer: one object, two backing stores."""

    def __init__(self):
        self.sql = sqlite3.connect(SQL_DB_PATH)
        self.sql.row_factory = sqlite3.Row
        self.sql.execute("PRAGMA foreign_keys = ON;")
        self.nosql = DocumentDB(NOSQL_DIR)

    # ------------------------------------------------------------------
    def get_product_detail(self, product_id: str) -> dict:
        """Product page: combines the NoSQL product document, a live
        aggregate of its NoSQL reviews, and its real-time SQL stock level."""
        product = self.nosql["products"].find_one({"_id": product_id})
        if not product:
            return {"error": "product not found"}

        review_agg = self.nosql["reviews"].aggregate([
            {"$match": {"product_id": product_id}},
            {"$group": {"_id": "$product_id", "avg_rating": {"$avg": "$rating"},
                        "review_count": {"$sum": 1}}},
        ])
        top_reviews = self.nosql["reviews"].find(
            {"product_id": product_id}, limit=3, sort=("helpful_votes", -1))

        cur = self.sql.execute(
            "SELECT warehouse_location, stock_quantity FROM inventory WHERE product_id = ?",
            (product_id,))
        stock_rows = [dict(r) for r in cur.fetchall()]
        total_stock = sum(r["stock_quantity"] for r in stock_rows)

        return {
            "product": product,
            "review_summary": review_agg[0] if review_agg else {"avg_rating": None, "review_count": 0},
            "top_reviews": top_reviews,
            "stock_by_warehouse": stock_rows,
            "total_stock": total_stock,
            "in_stock": total_stock > 0,
        }

    # ------------------------------------------------------------------
    def place_order(self, user_id: int, cart_items: list) -> dict:
        """cart_items: [{"product_id": "P00001", "quantity": 2}, ...]
        Prices/names are fetched live from NoSQL (source of truth for
        catalog data); the order itself is written with full ACID
        guarantees on the SQL side, and stock is decremented atomically."""
        cur = self.sql.cursor()
        subtotal = 0.0
        line_items = []
        for item in cart_items:
            product = self.nosql["products"].find_one({"_id": item["product_id"]})
            if not product:
                raise ValueError(f"Unknown product {item['product_id']}")
            line_total = round(product["price"] * item["quantity"], 2)
            subtotal += line_total
            line_items.append((item["product_id"], product["name"],
                                item["quantity"], product["price"], line_total))

        tax = round(subtotal * 0.08, 2)
        shipping_fee = 0.0 if subtotal > 100 else 5.99
        total = round(subtotal + tax + shipping_fee, 2)

        try:
            cur.execute("""INSERT INTO orders (user_id, status, subtotal_amount, tax_amount,
                            shipping_amount, total_amount) VALUES (?,?,?,?,?,?)""",
                (user_id, "confirmed", round(subtotal, 2), tax, shipping_fee, total))
            order_id = cur.lastrowid

            for pid, name, qty, price, line_total in line_items:
                cur.execute("""INSERT INTO order_items (order_id, product_id,
                                product_name_snapshot, quantity, unit_price, line_total)
                                VALUES (?,?,?,?,?,?)""",
                    (order_id, pid, name, qty, price, line_total))
                # atomic, oversell-safe stock decrement (SQL side keeps this guarantee)
                cur.execute("""UPDATE inventory SET stock_quantity = stock_quantity - ?
                                WHERE product_id = ? AND stock_quantity >= ?
                                AND inventory_id = (SELECT inventory_id FROM inventory
                                    WHERE product_id = ? AND stock_quantity >= ? LIMIT 1)""",
                    (qty, pid, qty, pid, qty))

            cur.execute("""INSERT INTO payments (order_id, payment_method, amount, status,
                            transaction_ref, paid_at) VALUES (?,?,?,?,?,?)""",
                (order_id, "upi", total, "success", f"TXN{order_id:08d}{datetime.now():%f}",
                 datetime.now().isoformat()))
            self.sql.commit()
        except Exception:
            self.sql.rollback()
            raise

        self.record_activity(user_id, "checkout_start",
                              {"order_id": order_id, "item_count": len(cart_items)})
        return {"order_id": order_id, "subtotal": round(subtotal, 2), "tax": tax,
                "shipping": shipping_fee, "total": total}

    # ------------------------------------------------------------------
    def get_user_dashboard(self, user_id: int) -> dict:
        """'My Account' page: SQL order history + NoSQL recent activity,
        merged into a single response."""
        user_row = self.sql.execute(
            "SELECT user_id, first_name, last_name, email, city, country FROM users WHERE user_id=?",
            (user_id,)).fetchone()
        orders = self.sql.execute("""SELECT order_id, order_date, status, total_amount
                                      FROM orders WHERE user_id=? ORDER BY order_date DESC LIMIT 5""",
                                    (user_id,)).fetchall()
        recent_activity = self.nosql["activity_logs"].find(
            {"user_id": user_id}, limit=5, sort=("timestamp", -1))

        return {
            "user": dict(user_row) if user_row else None,
            "recent_orders": [dict(o) for o in orders],
            "recent_activity": recent_activity,
        }

    # ------------------------------------------------------------------
    def search_products(self, keyword: str) -> list:
        """Search bar: NoSQL tag/keyword match, enriched with live SQL stock."""
        matches = self.nosql["products"].find({"tags": {"$regex": keyword}})
        if not matches:
            matches = [p for p in self.nosql["products"].find()
                        if keyword.lower() in p["name"].lower()]
        enriched = []
        for p in matches[:10]:
            stock = self.sql.execute(
                "SELECT COALESCE(SUM(stock_quantity),0) AS s FROM inventory WHERE product_id=?",
                (p["_id"],)).fetchone()["s"]
            enriched.append({"_id": p["_id"], "name": p["name"], "price": p["price"],
                              "avg_rating": p["avg_rating"], "in_stock": stock > 0})
        return enriched

    # ------------------------------------------------------------------
    def record_activity(self, user_id: int, action_type: str, metadata: dict):
        """Unstructured event write -- NoSQL is the natural fit since every
        action_type has a different metadata shape."""
        self.nosql["activity_logs"].insert_one({
            "user_id": user_id, "session_id": "sess_live", "action_type": action_type,
            "timestamp": datetime.now().isoformat(), "metadata": metadata,
        })

    def close(self):
        self.sql.close()


if __name__ == "__main__":
    svc = ECommerceService()

    print("=" * 70)
    print("DEMO 1: get_product_detail('P00001')")
    print("=" * 70)
    detail = svc.get_product_detail("P00001")
    print(f"Product : {detail['product']['name']} (${detail['product']['price']})")
    print(f"Rating  : {detail['review_summary']}")
    print(f"Stock   : {detail['total_stock']} units across "
          f"{len(detail['stock_by_warehouse'])} warehouse(s)")

    print("\n" + "=" * 70)
    print("DEMO 2: place_order(user_id=1, cart)")
    print("=" * 70)
    order = svc.place_order(1, [{"product_id": "P00001", "quantity": 1},
                                  {"product_id": "P00002", "quantity": 2}])
    print(order)

    print("\n" + "=" * 70)
    print("DEMO 3: get_user_dashboard(user_id=1)")
    print("=" * 70)
    dash = svc.get_user_dashboard(1)
    print(f"User: {dash['user']}")
    print(f"Recent orders: {len(dash['recent_orders'])}")
    print(f"Recent activity events: {len(dash['recent_activity'])}")

    print("\n" + "=" * 70)
    print("DEMO 4: search_products('wireless')")
    print("=" * 70)
    for p in svc.search_products("wireless"):
        print(p)

    svc.close()

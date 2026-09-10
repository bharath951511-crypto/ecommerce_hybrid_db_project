import io
import os
import sqlite3
import sys
from contextlib import redirect_stdout
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from document_store import DocumentDB

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DB_PATH = os.path.join(BASE_DIR, "data", "ecommerce_sql.db")
NOSQL_DIR = os.path.join(BASE_DIR, "data", "nosql_store")
OUT_PATH = os.path.join(BASE_DIR, "output", "query_results.txt")


def hdr(n, title):
    print(f"\n[{n}] {title}")
    print("-" * 70)


def run():
    conn = sqlite3.connect(SQL_DB_PATH)
    conn.row_factory = sqlite3.Row
    db = DocumentDB(NOSQL_DIR)

    print("############################################################")
    print("  SQL SIDE  —  CRUD + Aggregation query results")
    print("############################################################")

    hdr(1, "CREATE — insert a new user")
    cur = conn.execute("""INSERT OR IGNORE INTO users
                    (first_name,last_name,email,phone,password_hash,
                     role,address_line1,city,state,postal_code,country)
                    VALUES ('Aisha','Khan','aisha.khan.demo@example.com','+91-98765-11111',
                    'hash$demo','customer','12 MG Road','Hyderabad','Telangana','500001','IN')""")
    conn.commit()
    row = conn.execute(
    "SELECT user_id FROM users WHERE email=?",
    ("aisha.khan.demo@example.com",)
    ).fetchone()
    print(f"User_id = {row['user_id']}")

    hdr(2, "READ — user profile by email")
    row = conn.execute("SELECT user_id,first_name,last_name,email,city,country FROM users WHERE email=?",
                         ("aisha.khan.demo@example.com",)).fetchone()
    print(dict(row))

    hdr(3, "READ — full order detail (order_id = 1)")
    for r in conn.execute("""SELECT o.order_id, o.status AS order_status, o.total_amount,
               oi.product_id, oi.quantity, oi.unit_price,
               p.payment_method, p.status AS payment_status,
               s.carrier, s.status AS shipping_status
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        LEFT JOIN payments p ON p.order_id = o.order_id
        LEFT JOIN shipping s ON s.order_id = o.order_id
        WHERE o.order_id = 1"""):
        print(dict(r))

    hdr(4, "UPDATE — mark order 1 as shipped")
    conn.execute("UPDATE orders SET status='shipped' WHERE order_id=1")
    conn.commit()
    print(dict(conn.execute("SELECT order_id,status FROM orders WHERE order_id=1").fetchone()))

    hdr(5, "DELETE — cancel a pending order (id=5, guarded)")
    cur = conn.execute("UPDATE orders SET status='cancelled' WHERE order_id=5 AND status='pending'")
    conn.commit()
    print(f"Rows affected: {cur.rowcount}")

    hdr(6, "AGGREGATION — revenue & order count per month")
    for r in conn.execute("""SELECT strftime('%Y-%m',order_date) AS month, COUNT(*) AS orders,
                              ROUND(SUM(total_amount),2) AS revenue
                              FROM orders WHERE status!='cancelled'
                              GROUP BY month ORDER BY month"""):
        print(dict(r))

    hdr(7, "AGGREGATION — top 10 customers by lifetime spend")
    for r in conn.execute("""SELECT u.user_id, u.first_name, u.last_name,
                              COUNT(o.order_id) AS orders_placed, ROUND(SUM(o.total_amount),2) AS spend
                              FROM users u JOIN orders o ON o.user_id=u.user_id
                              WHERE o.status!='cancelled' GROUP BY u.user_id
                              ORDER BY spend DESC LIMIT 10"""):
        print(dict(r))

    hdr(8, "AGGREGATION — order status funnel")
    for r in conn.execute("""SELECT status, COUNT(*) AS cnt,
                              ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM orders),1) AS pct
                              FROM orders GROUP BY status ORDER BY cnt DESC"""):
        print(dict(r))

    hdr(9, "AGGREGATION — payment method success rate")
    for r in conn.execute("""SELECT payment_method, COUNT(*) AS attempts,
                              SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS successes,
                              ROUND(100.0*SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct
                              FROM payments GROUP BY payment_method ORDER BY attempts DESC"""):
        print(dict(r))

    hdr(10, "AGGREGATION — low-stock reorder alert (top 10)")
    for r in conn.execute("""SELECT product_id, warehouse_location, stock_quantity, reorder_level
                              FROM inventory WHERE stock_quantity <= reorder_level
                              ORDER BY stock_quantity ASC LIMIT 10"""):
        print(dict(r))

    print("\n\n############################################################")
    print("  NOSQL SIDE  —  CRUD + Aggregation query results")
    print("############################################################")

    hdr(11, "CREATE — insert a new product")
    new_id = db["products"].insert_one({
        "_id": "P00999", "name": "Apple AirPods Pro", "category": "Electronics",
        "brand": "Apple", "price": 249.0, "attributes": {"color": "White"},
        "tags": ["electronics", "apple", "airpods"], "avg_rating": 0, "review_count": 0,
        "is_active": True, "created_at": datetime.now().isoformat()})
    print(f"Inserted product _id = {new_id}")

    hdr(12, "READ — electronics under $200, cheapest first")
    for p in db["products"].find({"category": "Electronics", "price": {"$lt": 200}},
                                    limit=5, sort=("price", 1)):
        print({"_id": p["_id"], "name": p["name"], "price": p["price"]})

    hdr(13, "READ — reviews for product P00001, most helpful first")
    revs = db["reviews"].find({"product_id": "P00001"}, limit=5, sort=("helpful_votes", -1))
    for r in revs:
        print({"_id": r["_id"], "rating": r["rating"], "helpful_votes": r["helpful_votes"]})
    if not revs:
        print("(no reviews yet for this product)")

    hdr(14, "UPDATE — change product price + increment review helpful_votes")
    db["products"].update_one({"_id": "P00001"}, {"$set": {"price": 329.99}})
    print(db["products"].find_one({"_id": "P00001"})["price"])

    hdr(15, "DELETE — remove the demo product created above")
    removed = db["products"].delete_one({"_id": "P00999"})
    print(f"Documents removed: {removed}")

    hdr(16, "AGGREGATION — avg rating & review count per category (via $lookup)")
    result = db["reviews"].aggregate([
        {"$lookup": {"from": "products", "localField": "product_id",
                     "foreignField": "_id", "as": "product"}},
        {"$unwind": "$product"},
    ])
    from collections import defaultdict
    cat_ratings = defaultdict(list)
    for r in result:
        cat_ratings[r["product"]["category"]].append(r["rating"])
    for cat, ratings in sorted(cat_ratings.items(), key=lambda x: -sum(x[1])/len(x[1])):
        print({"category": cat, "avg_rating": round(sum(ratings)/len(ratings), 2),
               "total_reviews": len(ratings)})

    hdr(17, "AGGREGATION — top 10 highest-rated products (>=3 reviews)")
    top = db["products"].aggregate([
        {"$match": {"review_count": {"$gte": 3}}},
        {"$sort": {"avg_rating": -1}},
        {"$limit": 10},
    ])
    for p in top:
        print({"name": p["name"], "brand": p["brand"], "avg_rating": p["avg_rating"],
               "review_count": p["review_count"]})

    hdr(18, "AGGREGATION — action_type counts, last 30 days")
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    logs = db["activity_logs"].aggregate([
        {"$match": {"timestamp": {"$gte": cutoff}}},
        {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ])
    for l in logs:
        print(l)

    hdr(19, "AGGREGATION — most-searched keywords")
    searches = db["activity_logs"].aggregate([
        {"$match": {"action_type": "search"}},
        {"$group": {"_id": "$metadata.query", "searches": {"$sum": 1}}},
        {"$sort": {"searches": -1}},
        {"$limit": 5},
    ])
    for s in searches:
        print(s)

    hdr(20, "CROSS-DATABASE — product detail combining NoSQL catalog + SQL live stock")
    pid = "P00002"
    product = db["products"].find_one({"_id": pid})
    stock = conn.execute("SELECT COALESCE(SUM(stock_quantity),0) AS s FROM inventory WHERE product_id=?",
                           (pid,)).fetchone()["s"]
    print({"product": product["name"], "price": product["price"], "live_stock": stock})

    conn.close()


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        run()
    text = buf.getvalue()
    print(text)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(text)
    print(f"\n(Full results also saved to {OUT_PATH})")

import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from document_store import DocumentDB

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DB_PATH = os.path.join(BASE_DIR, "data", "ecommerce_sql.db")
NOSQL_DIR = os.path.join(BASE_DIR, "data", "nosql_store")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")

FIRST_NAMES = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Reyansh","Krishna","Ishaan",
    "Sai","Ayaan","Priya","Ananya","Diya","Saanvi","Aadhya","Kavya","Meera","Ishita",
    "Riya","Anika","James","Olivia","Liam","Emma","Noah","Ava","Ethan","Sophia",
    "Mason","Isabella","Lucas","Mia","Henry","Amelia","Daniel","Grace","Ravi","Sneha",
    "Karan","Neha","Rohan","Pooja","Nikhil","Divya","Arnav","Tanya","Yash","Simran"]
LAST_NAMES = ["Sharma","Verma","Gupta","Iyer","Nair","Reddy","Patel","Mehta","Khan",
    "Chowdhury","Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Kapoor","Malhotra","Chauhan","Bansal","Joshi","Pillai"]
CITIES = [("Hyderabad","Telangana","IN"),("Bengaluru","Karnataka","IN"),
    ("Mumbai","Maharashtra","IN"),("Delhi","Delhi","IN"),("Chennai","Tamil Nadu","IN"),
    ("Pune","Maharashtra","IN"),("Kolkata","West Bengal","IN"),("Jaipur","Rajasthan","IN"),
    ("New York","NY","US"),("San Francisco","CA","US"),("Austin","TX","US"),
    ("London","England","UK"),("Toronto","Ontario","CA")]

CATEGORIES = {
    "Electronics": {
        "brands": ["Sony","Samsung","Apple","boAt","JBL","Dell","HP","Lenovo","OnePlus","Xiaomi"],
        "items": ["Wireless Headphones","Bluetooth Speaker","Smartwatch","Laptop","Smartphone",
                  "Tablet","Power Bank","Wireless Mouse","Mechanical Keyboard","4K Monitor"],
        "attrs": lambda: {"color": random.choice(["Black","White","Blue","Silver","Space Grey"]),
                            "warranty_months": random.choice([6,12,24]),
                            "battery_life_hrs": random.choice([8,10,20,30,None])}
    },
    "Fashion": {
        "brands": ["Levi's","Zara","H&M","Nike","Adidas","Puma","Allen Solly","Van Heusen","Fabindia","Roadster"],
        "items": ["Cotton T-Shirt","Denim Jeans","Running Shoes","Formal Shirt","Hoodie",
                  "Leather Jacket","Sneakers","Chinos","Kurta","Sports Jacket"],
        "attrs": lambda: {"size": random.choice(["S","M","L","XL","XXL"]),
                            "color": random.choice(["Black","Navy","Maroon","Olive","White"]),
                            "material": random.choice(["Cotton","Polyester","Denim","Wool"])}
    },
    "Home & Kitchen": {
        "brands": ["Prestige","IKEA","Milton","Philips","Bajaj","Havells","Borosil","Cello"],
        "items": ["Non-Stick Pan","Electric Kettle","Mixer Grinder","Study Table","Bed Sheet Set",
                  "Table Lamp","Air Fryer","Vacuum Cleaner","Dinner Set","Wall Clock"],
        "attrs": lambda: {"color": random.choice(["White","Beige","Grey","Red"]),
                            "capacity_l": random.choice([0.5,1,1.5,2,5,None]),
                            "warranty_months": random.choice([6,12,24])}
    },
    "Books": {
        "brands": ["Penguin","HarperCollins","Bloomsbury","Rupa","Scholastic"],
        "items": ["The Silent Patient","Atomic Habits","Sapiens","Rich Dad Poor Dad","Ikigai",
                  "The Alchemist","Clean Code","1984","Deep Work","Think Again"],
        "attrs": lambda: {"pages": random.randint(150,600),
                            "language": random.choice(["English","Hindi"]),
                            "format": random.choice(["Paperback","Hardcover","eBook"])}
    },
    "Sports & Fitness": {
        "brands": ["Nivia","Yonex","Cosco","Decathlon","Wilson","Nike"],
        "items": ["Yoga Mat","Badminton Racket","Dumbbell Set","Cricket Bat","Football",
                  "Resistance Bands","Treadmill","Cycling Helmet","Skipping Rope","Gym Gloves"],
        "attrs": lambda: {"weight_kg": random.choice([0.5,1,2,5,10,None]),
                            "color": random.choice(["Black","Blue","Red","Green"])}
    },
}

ACTION_TYPES = ["page_view","search","add_to_cart","remove_from_cart","wishlist_add",
                "checkout_start","click_recommendation"]
DEVICES = [("mobile","Android 14"),("mobile","iOS 18"),("desktop","Windows 11"),
           ("desktop","macOS 15"),("tablet","iPadOS 18")]


def rand_date(days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, days_back),
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))


def build_sql_database():
    if os.path.exists(SQL_DB_PATH):
        os.remove(SQL_DB_PATH)
    os.makedirs(os.path.dirname(SQL_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQL_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH) as f:
        script = f.read()
    # SQLite-compatible tweaks (ENUM/AUTO_INCREMENT/UNIQUE KEY aren't native to sqlite)
    script = script.replace("AUTO_INCREMENT", "AUTOINCREMENT")
    import re
    script = re.sub(r"ENUM\([^)]*\)", "VARCHAR(20)", script)
    script = re.sub(r",\s*UNIQUE KEY uq_product_warehouse \(product_id, warehouse_location\)", "", script)
    script = re.sub(r"\s*ON UPDATE CURRENT_TIMESTAMP", "", script)
    conn.executescript(script)
    conn.commit()
    return conn


def generate_products(nosql_db, n=120):
    products = []
    pid_counter = 1
    for _ in range(n):
        category, meta = random.choice(list(CATEGORIES.items()))
        brand = random.choice(meta["brands"])
        item = random.choice(meta["items"])
        pid = f"P{pid_counter:05d}"
        pid_counter += 1
        price = round(random.uniform(9.99, 1999.99), 2)
        doc = {
            "_id": pid,
            "name": f"{brand} {item}",
            "category": category,
            "subcategory": item.split()[-1],
            "brand": brand,
            "description": f"{brand} {item} - premium quality, factory sealed, "
                            f"trusted by thousands of customers across India.",
            "price": price,
            "currency": "USD",
            "attributes": meta["attrs"](),
            "tags": [category.lower().split()[0], brand.lower(), item.split()[0].lower()],
            "images": [f"https://cdn.example.com/{pid}/1.jpg"],
            "avg_rating": 0.0,
            "review_count": 0,
            "is_active": True,
            "created_at": rand_date(600).isoformat(),
        }
        products.append(doc)
    nosql_db["products"].insert_many(products)
    return products


def generate_reviews(nosql_db, products, sql_user_ids, n=250):
    reviews = []
    review_texts_pos = ["Absolutely love it, exceeded my expectations!",
        "Great value for money, works flawlessly.", "Fast delivery and superb quality.",
        "Exactly as described, highly recommend.", "Solid build quality, very happy."]
    review_texts_neg = ["Not what I expected, quality could be better.",
        "Arrived a bit late but product is okay.", "Average product for the price.",
        "Had some issues but support resolved it.", "Decent, though packaging was poor."]
    for i in range(n):
        product = random.choice(products)
        rating = random.choices([5,4,3,2,1], weights=[40,30,15,10,5])[0]
        text = random.choice(review_texts_pos if rating >= 4 else review_texts_neg)
        rid = f"R{i+1:06d}"
        reviews.append({
            "_id": rid,
            "product_id": product["_id"],
            "user_id": random.choice(sql_user_ids),
            "rating": rating,
            "title": "Great purchase" if rating >= 4 else "Could be better",
            "review_text": text,
            "verified_purchase": random.random() > 0.2,
            "helpful_votes": random.randint(0, 80),
            "images": [],
            "seller_response": None,
            "review_date": rand_date(300).isoformat(),
        })
    nosql_db["reviews"].insert_many(reviews)

    # roll up avg_rating / review_count back onto products (denormalised counter pattern)
    from collections import defaultdict
    agg = defaultdict(list)
    for r in reviews:
        agg[r["product_id"]].append(r["rating"])
    for pid, ratings in agg.items():
        nosql_db["products"].update_one(
            {"_id": pid},
            {"$set": {"avg_rating": round(sum(ratings) / len(ratings), 2),
                      "review_count": len(ratings)}})
    return reviews


def generate_logs(nosql_db, products, sql_user_ids, n=400):
    logs = []
    for i in range(n):
        action = random.choice(ACTION_TYPES)
        device, os_name = random.choice(DEVICES)
        meta = {"device": device, "os": os_name}
        if action == "search":
            meta["query"] = random.choice(["wireless headphones","running shoes","yoga mat",
                                            "smartwatch","laptop bag","air fryer"])
            meta["results_count"] = random.randint(0, 120)
        else:
            product = random.choice(products)
            meta["product_id"] = product["_id"]
            if action == "add_to_cart":
                meta["quantity"] = random.randint(1, 3)
        logs.append({
            "_id": f"L{i+1:07d}",
            "user_id": random.choice(sql_user_ids),
            "session_id": f"sess_{random.randint(100000,999999)}",
            "action_type": action,
            "timestamp": rand_date(90).isoformat(),
            "metadata": meta,
        })
    nosql_db["activity_logs"].insert_many(logs)
    return logs


def generate_sql_data(conn, products, n_users=150, n_orders=220):
    cur = conn.cursor()

    # ---- USERS ----
    user_ids = []
    used_emails = set()
    for i in range(n_users):
        fn, ln = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        city, state, country = random.choice(CITIES)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        used_emails.add(email)
        cur.execute("""INSERT INTO users (first_name,last_name,email,phone,password_hash,role,
                        address_line1,city,state,postal_code,country,is_active,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (fn, ln, email, f"+1-555-{random.randint(1000,9999)}",
             f"hash${uuid_like()}", "customer" if random.random() > 0.03 else "admin",
             f"{random.randint(1,999)} {random.choice(['MG Road','Park Street','Main St','Oak Ave'])}",
             city, state, f"{random.randint(10000,99999)}", country,
             1, rand_date(700).isoformat()))
        user_ids.append(cur.lastrowid)

    # ---- INVENTORY ---- (>=100 rows: one or two warehouse rows per product)
    warehouses = ["Hyderabad-WH1","Mumbai-WH2","Delhi-WH3","Bengaluru-WH4"]
    for p in products:
        for wh in random.sample(warehouses, k=random.choice([1,2])):
            cur.execute("""INSERT INTO inventory (product_id,warehouse_location,stock_quantity,
                            reorder_level,last_restocked) VALUES (?,?,?,?,?)""",
                (p["_id"], wh, random.randint(0, 500), random.choice([10,20,30]),
                 rand_date(60).isoformat()))

    # ---- ORDERS + ORDER_ITEMS + PAYMENTS + SHIPPING ----
    statuses = ["pending","confirmed","shipped","delivered","cancelled","returned"]
    pay_methods = ["credit_card","debit_card","upi","net_banking","wallet","cod"]
    carriers = ["BlueDart","FedEx","DHL","Delhivery","India Post"]

    for o in range(n_orders):
        uid = random.choice(user_ids)
        odate = rand_date(365)
        chosen_products = random.sample(products, k=random.randint(1, 4))
        subtotal = 0.0
        cur.execute("""INSERT INTO orders (user_id,order_date,status,subtotal_amount,
                        tax_amount,shipping_amount,total_amount)
                        VALUES (?,?,?,?,?,?,?)""",
            (uid, odate.isoformat(), "pending", 0, 0, 0, 0))  # placeholder, fixed below
        order_id = cur.lastrowid

        for p in chosen_products:
            qty = random.randint(1, 3)
            unit_price = p["price"]
            line_total = round(unit_price * qty, 2)
            subtotal += line_total
            cur.execute("""INSERT INTO order_items (order_id,product_id,product_name_snapshot,
                            quantity,unit_price,line_total) VALUES (?,?,?,?,?,?)""",
                (order_id, p["_id"], p["name"], qty, unit_price, line_total))

        tax = round(subtotal * 0.08, 2)
        shipping_fee = 0.0 if subtotal > 100 else 5.99
        total = round(subtotal + tax + shipping_fee, 2)
        status = random.choices(statuses, weights=[10,15,20,40,10,5])[0]
        cur.execute("""UPDATE orders SET status=?, subtotal_amount=?, tax_amount=?,
                        shipping_amount=?, total_amount=? WHERE order_id=?""",
            (status, round(subtotal,2), tax, shipping_fee, total, order_id))

        pay_status = "success" if status in ("confirmed","shipped","delivered") else \
                     ("refunded" if status == "returned" else
                      random.choice(["success","failed","initiated"]))
        cur.execute("""INSERT INTO payments (order_id,payment_method,amount,status,
                        transaction_ref,paid_at) VALUES (?,?,?,?,?,?)""",
            (order_id, random.choice(pay_methods), total, pay_status,
             f"TXN{order_id:08d}{random.randint(100,999)}",
             odate.isoformat() if pay_status == "success" else None))

        if status in ("shipped","delivered"):
            ship_date = odate + timedelta(days=random.randint(1,3))
            est = ship_date + timedelta(days=random.randint(2,7))
            delivered = est if status == "delivered" else None
            cur.execute("""INSERT INTO shipping (order_id,carrier,tracking_number,ship_address,
                            status,shipped_date,estimated_delivery,delivered_date)
                            VALUES (?,?,?,?,?,?,?,?)""",
                (order_id, random.choice(carriers), f"TRK{random.randint(10**9,10**10-1)}",
                 f"{random.choice(CITIES)[0]} shipping address", status,
                 ship_date.isoformat(), est.isoformat(),
                 delivered.isoformat() if delivered else None))

    conn.commit()
    return user_ids


def uuid_like():
    return "".join(random.choices("abcdef0123456789", k=32))


def main():
    print("Building SQL schema ...")
    conn = build_sql_database()

    print("Initialising NoSQL document store ...")
    if os.path.exists(NOSQL_DIR):
        import shutil
        shutil.rmtree(NOSQL_DIR)
    nosql_db = DocumentDB(NOSQL_DIR)

    print("Generating NoSQL products (>=100) ...")
    products = generate_products(nosql_db, n=120)

    print("Generating SQL users + orders + items + payments + shipping + inventory (>=100 each) ...")
    # generate a provisional user pool first for review/log FK-like references
    user_ids = generate_sql_data(conn, products, n_users=150, n_orders=220)

    print("Generating NoSQL reviews (>=100) ...")
    generate_reviews(nosql_db, products, user_ids, n=250)

    print("Generating NoSQL activity logs (>=100) ...")
    generate_logs(nosql_db, products, user_ids, n=400)

    # create declared indexes on the document store (recorded, see document_store.py)
    for field in ["category", "brand", "tags"]:
        nosql_db["products"].create_index(field)
    for field in ["product_id", "user_id"]:
        nosql_db["reviews"].create_index(field)
    for field in ["user_id", "action_type"]:
        nosql_db["activity_logs"].create_index(field)

    cur = conn.cursor()
    print("\n--- ROW / DOCUMENT COUNTS ---")
    for t in ["users","orders","order_items","payments","shipping","inventory"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"SQL   {t:<15}: {cur.fetchone()[0]}")
    for c in ["products","reviews","activity_logs"]:
        print(f"NoSQL {c:<15}: {nosql_db[c].count_documents()}")

    conn.close()
    print("\nDone. SQL DB at:", SQL_DB_PATH)
    print("NoSQL store at:", NOSQL_DIR)


if __name__ == "__main__":
    main()

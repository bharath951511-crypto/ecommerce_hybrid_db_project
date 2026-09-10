# NoSQL Side — Document Structures (MongoDB)

Database: `ecommerce_nosql`
Engine target: **MongoDB 6.x** (the live demo in this project runs an
embedded, file-backed document store — `scripts/document_store.py` — that
implements the same `insert_one / find / update_one / delete_one /
aggregate` API so the whole system runs offline without a Mongo server;
the collections, documents and queries below are written in real MongoDB
syntax and are directly portable to a MongoDB instance).

---

## 1. Collection: `products`
Flexible schema — different categories need different attributes, which is
exactly the case a relational table handles badly (either hundreds of
nullable columns, or an EAV table). A document per product with a nested,
category-specific `attributes` object solves this cleanly.

```json
{
  "_id": "P00001",
  "name": "Sony WH-1000XM5 Wireless Headphones",
  "category": "Electronics",
  "subcategory": "Audio",
  "brand": "Sony",
  "description": "Industry-leading noise cancelling wireless headphones ...",
  "price": 349.99,
  "currency": "USD",
  "attributes": {
    "color": "Black",
    "battery_life_hrs": 30,
    "connectivity": ["Bluetooth 5.2", "USB-C"],
    "warranty_months": 12
  },
  "tags": ["headphones", "wireless", "noise-cancelling"],
  "images": ["https://cdn.example.com/p00001/1.jpg"],
  "avg_rating": 4.6,
  "review_count": 128,
  "is_active": true,
  "created_at": {"$date": "2025-01-14T10:20:00Z"}
}
```

Because a *clothing* item needs `size`, `material`, `fit`; a *book* needs
`author`, `isbn`, `pages`; a *grocery* item needs `expiry_date`,
`weight_kg` — the `attributes` sub-document differs per document while the
outer shape (`name`, `category`, `price`, `tags`...) stays consistent.

**Validation (`db.createCollection` with `$jsonSchema`):**
```javascript
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "category", "brand", "price"],
      properties: {
        name:     { bsonType: "string" },
        category: { bsonType: "string" },
        price:    { bsonType: "double", minimum: 0 },
        avg_rating: { bsonType: "double", minimum: 0, maximum: 5 }
      }
    }
  }
});
```

**Indexes:**
```javascript
db.products.createIndex({ category: 1 });
db.products.createIndex({ brand: 1 });
db.products.createIndex({ name: "text", description: "text" });   // full-text search
db.products.createIndex({ price: 1 });
db.products.createIndex({ tags: 1 });                              // multikey index
```

---

## 2. Collection: `reviews`
Semi-structured, high write-volume, benefits from schema flexibility
(optional fields like `seller_response`, variable-length `images` array).

```json
{
  "_id": "R000045",
  "product_id": "P00001",
  "user_id": 214,
  "rating": 5,
  "title": "Best headphones I've owned",
  "review_text": "Noise cancellation is superb, battery lasts...",
  "verified_purchase": true,
  "helpful_votes": 37,
  "images": [],
  "seller_response": null,
  "review_date": {"$date": "2025-03-02T08:15:00Z"}
}
```

**Indexes:**
```javascript
db.reviews.createIndex({ product_id: 1 });
db.reviews.createIndex({ user_id: 1 });
db.reviews.createIndex({ product_id: 1, rating: -1 });   // compound, supports rating filters
```

---

## 3. Collection: `activity_logs`
Unstructured, append-only, extremely high volume, no fixed shape —
the textbook case for a NoSQL document store instead of a relational
table (a `page_view` log entry and a `search` log entry carry completely
different metadata).

```json
{
  "_id": "L0000998",
  "user_id": 214,
  "session_id": "sess_9f31ac",
  "action_type": "add_to_cart",
  "timestamp": {"$date": "2025-06-11T14:02:31Z"},
  "metadata": {
    "product_id": "P00001",
    "quantity": 1,
    "referrer": "search_results",
    "device": "mobile",
    "os": "Android 14"
  }
}
```

A `search` event, by contrast, stores `{"query": "...", "results_count": 24,
"filters_applied": {...}}` in the very same `metadata` field — no schema
migration needed, unlike adding new nullable columns to a SQL table.

**Indexes:**
```javascript
db.activity_logs.createIndex({ user_id: 1, timestamp: -1 });
db.activity_logs.createIndex({ action_type: 1 });
db.activity_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 15552000 }); // TTL: auto-purge after 180 days
```

---

## Example CRUD / Aggregation (mongosh syntax)

```javascript
// CREATE
db.products.insertOne({ _id: "P00101", name: "Kindle Paperwhite", category: "Electronics",
  brand: "Amazon", price: 139.99, attributes: { storage_gb: 16 }, tags: ["ereader"] });

// READ
db.products.find({ category: "Electronics", price: { $lt: 200 } }).sort({ price: 1 });

// UPDATE
db.products.updateOne({ _id: "P00101" }, { $set: { price: 129.99 }, $inc: { review_count: 1 } });

// DELETE
db.reviews.deleteOne({ _id: "R000045" });

// AGGREGATION — average rating & review count per category
db.reviews.aggregate([
  { $lookup: { from: "products", localField: "product_id", foreignField: "_id", as: "product" } },
  { $unwind: "$product" },
  { $group: { _id: "$product.category", avgRating: { $avg: "$rating" }, totalReviews: { $sum: 1 } } },
  { $sort: { avgRating: -1 } }
]);
```

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, AlignmentType, BorderStyle, PageBreak,
  TableOfContents, LevelFormat, convertInchesToTwip, VerticalAlign
} = require("docx");

const BASE = "/home/claude/ecommerce_hybrid_db";
const NAVY = "1F618D";
const GOLD = "B7950B";
const DARK = "2C3E50";
const GREY = "5D6D7E";

// ---------------------------------------------------------------- helpers
function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 300 },
    children: [new TextRun({ text, ...opts })],
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    text, bullet: { level }, spacing: { after: 80 },
  });
}
function code(lines) {
  return new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: "F4F6F7" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "D5D8DC" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "D5D8DC" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "D5D8DC" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "D5D8DC" },
    },
    spacing: { after: 200 },
    children: lines.split("\n").flatMap((line, i) => [
      ...(i > 0 ? [new TextRun({ break: 1 })] : []),
      new TextRun({ text: line || " ", font: "Consolas", size: 17, color: "1B2631" }),
    ]),
  });
}
function image(path, widthPx) {
  const data = fs.readFileSync(path);
  const dims = widthPx || 550;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new ImageRun({ data, transformation: { width: dims, height: dims * 0.62 }, type: "png" })],
  });
}
function imageAuto(path, w, h) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new ImageRun({ data, transformation: { width: w, height: h }, type: "png" })],
  });
}
function cell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.header ? { fill: NAVY, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({ text: String(text), bold: !!opts.header, color: opts.header ? "FFFFFF" : "000000", size: 19 })],
    })],
  });
}
function table(headers, rows, widths) {
  const w = widths || headers.map(() => Math.floor(9000 / headers.length));
  return new Table({
    width: { size: 9000, type: WidthType.DXA },
    columnWidths: w,
    rows: [
      new TableRow({ children: headers.map((h, i) => cell(h, { header: true, width: w[i] })) }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, { width: w[i] })) })),
    ],
  });
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 260 },
    children: [new TextRun({ text, italics: true, size: 18, color: "5D6D7E" })],
  });
}

// ---------------------------------------------------------------- content
const children = [];

// TITLE PAGE
children.push(
  new Paragraph({ spacing: { before: 2400 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Hybrid SQL + NoSQL Database System", bold: true, size: 52, color: NAVY })] }),
  new Paragraph({ spacing: { before: 200, after: 100 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "for an E-Commerce Platform", size: 34, color: DARK })] }),
  new Paragraph({ spacing: { before: 600 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "A Comprehensive Database Systems Project", italics: true, size: 24, color: GREY })] }),
  new Paragraph({ spacing: { before: 1800 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Course: Database Management Systems", size: 22 })] }),
  new Paragraph({ spacing: { before: 100 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Submission Date: September 2026", size: 22 })] }),
  pageBreak(),
);

// TABLE OF CONTENTS (static list — reliable across Word/LibreOffice/Google Docs
// without requiring a manual "update fields" step)
const tocEntries = [
  "1. Introduction & Project Overview",
  "2. Technology Stack & Implementation Note",
  "3. System Architecture",
  "4. Database Schema — SQL Side (Structured Data)",
  "5. Database Schema — NoSQL Side (Semi-/Unstructured Data)",
  "6. Sample Data",
  "7. Functional Queries — CRUD & Aggregation",
  "8. Application (Integration) Layer",
  "9. Performance & Optimization Techniques",
  "10. Design Decisions & Challenges",
  "11. Conclusion",
  "12. Appendix — Project File Structure",
];
children.push(
  h1("Table of Contents"),
  ...tocEntries.map(t => new Paragraph({
    spacing: { after: 140 },
    children: [new TextRun({ text: t, size: 23, color: DARK })],
  })),
  pageBreak(),
);

// 1. INTRODUCTION
children.push(
  h1("1. Introduction & Project Overview"),
  p("This project designs and implements a hybrid database system for an E-Commerce Platform, combining a relational (SQL) database for structured, transaction-critical data with a NoSQL document database for flexible, semi-structured and unstructured data. The two systems are unified by an application/integration layer that coordinates reads and writes across both stores, mirroring how real-world e-commerce systems (e.g. Amazon, Flipkart) split their data between strongly-consistent order/payment systems and flexible product-catalog systems."),
  p("An e-commerce platform was chosen because it naturally produces both kinds of data in large volume: user accounts, orders, and payments demand strict ACID guarantees and a fixed relational shape, while product catalogs, customer reviews, and clickstream/activity logs are highly variable in structure and benefit from a schema-flexible document store. This makes the domain an ideal, realistic demonstration of when to use SQL versus NoSQL — and how to combine them."),
  h2("1.1 Objectives"),
  bullet("Design a normalized relational schema for structured e-commerce data (users, orders, payments, shipping, inventory)."),
  bullet("Design flexible document structures for semi-structured/unstructured data (product catalog, reviews, activity logs)."),
  bullet("Implement both databases with realistic sample data (100+ records per table/collection)."),
  bullet("Write functional CRUD and aggregation queries for both systems."),
  bullet("Build an application layer that integrates both databases into unified business operations."),
  bullet("Apply and document indexing and other performance-optimization techniques."),
  h2("1.2 Why a Hybrid Approach?"),
  p("Relational databases enforce referential integrity, transactions, and a fixed schema — ideal for money-related and account-related data where correctness matters more than flexibility. Document databases drop rigid schemas in exchange for the ability to store heterogeneous, evolving data (a laptop and a t-shirt have almost nothing in common as products) without constant migrations. Using one engine for everything forces an uncomfortable trade-off; using both, matched to the shape of each dataset, avoids it."),
);

// 2. TECHNOLOGY / IMPLEMENTATION NOTE
children.push(
  h1("2. Technology Stack & Implementation Note"),
  table(
    ["Layer", "Design Target (production)", "Used for this demo"],
    [
      ["SQL database", "MySQL 8 / PostgreSQL 13+", "SQLite 3 (same DDL, minor dialect tweaks)"],
      ["NoSQL database", "MongoDB 6.x", "A custom embedded JSON document store (document_store.py) implementing the pymongo API: insertOne/Many, find, updateOne/Many, deleteOne/Many, aggregate, createIndex"],
      ["Application layer", "Python (psycopg2/PyMySQL + pymongo)", "Python (sqlite3 + document_store.py)"],
      ["Diagrams", "—", "Graphviz"],
    ],
    [2200, 4000, 2800]
  ),
  p(""),
  p("All schema, query, and integration code in this report is written in standard, portable syntax (real SQL DDL/DML and real MongoDB mongosh query syntax — see sql/schema.sql, sql/queries.sql, nosql/schema_design.md, nosql/queries.js). The offline substitutes above exist purely because this project was developed in a sandboxed environment without network access to run live MySQL/MongoDB server processes; the substitutes implement the identical query semantics so every result in Section 7 is real, reproducible output rather than a mock-up. Deploying to a real MySQL + MongoDB pair requires no design changes — only swapping the connection layer.", { italics: true, size: 20, color: "5D6D7E" }),
);

// 3. ARCHITECTURE
children.push(
  h1("3. System Architecture"),
  p("The architecture follows a simple three-tier separation: a thin client layer, a central application/service layer that owns all business logic, and two independent data stores that the application layer alone knows how to reconcile."),
  image(`${BASE}/diagrams/architecture_diagram.png`, 520),
  caption("Figure 1 — System architecture: application layer mediates between the SQL and NoSQL stores."),
  p("Because the NoSQL side has no native foreign key to the SQL side (and vice versa), referential consistency between order_items.product_id (SQL) and products._id (NoSQL) is enforced entirely in the application layer — see Section 8. This is the central engineering trade-off of a polyglot-persistence design: you gain schema flexibility on the document side, but you give up the database's automatic enforcement of cross-store integrity and must write that logic yourself."),
);

// 4. SQL SCHEMA
children.push(
  h1("4. Database Schema — SQL Side (Structured Data)"),
  p("Six relational tables model everything that must be transactionally consistent: accounts, orders, order line items, payments, shipping, and warehouse inventory."),
  image(`${BASE}/diagrams/er_diagram.png`, 560),
  caption("Figure 2 — Entity-Relationship diagram. Solid arrows are enforced foreign keys inside the SQL database; dashed gold arrows are logical (application-enforced) references into the NoSQL collections."),
  h2("4.1 Tables & Design Rationale"),
  table(
    ["Table", "Purpose", "Key constraints"],
    [
      ["users", "Account/identity data", "UNIQUE(email), CHECK via role ENUM"],
      ["orders", "One row per checkout", "FK -> users, CHECK(total_amount >= 0)"],
      ["order_items", "Order line items", "FK -> orders (CASCADE), CHECK(quantity > 0)"],
      ["payments", "Payment transactions", "FK -> orders (CASCADE), UNIQUE(transaction_ref)"],
      ["shipping", "Fulfilment/tracking", "FK -> orders (CASCADE)"],
      ["inventory", "Per-warehouse stock", "CHECK(stock_quantity >= 0), UNIQUE(product_id, warehouse_location)"],
    ],
    [1800, 3800, 3400]
  ),
  p(""),
  h2("4.2 Full DDL (excerpt)"),
  p("The complete script is in sql/schema.sql. Representative excerpt:"),
  code(fs.readFileSync(`${BASE}/sql/schema.sql`, "utf8").split("\n").slice(24, 60).join("\n")),
  h2("4.3 Indexing Strategy"),
  p("Beyond primary keys and the UNIQUE constraints above, the following secondary indexes were added based on the query patterns in Section 7 (lookups by email, filtering orders by user/status/date, and joining on foreign keys):"),
  bullet("idx_users_email, idx_users_city — user lookup and demographic filtering"),
  bullet("idx_orders_user_id, idx_orders_status_date — a user's order history; the status funnel query"),
  bullet("idx_items_order_id, idx_items_product_id — order detail joins and per-product sales lookups"),
  bullet("idx_payments_order_id, idx_payments_status — payment reconciliation and success-rate reporting"),
  bullet("idx_shipping_order_id, idx_shipping_tracking — tracking-number lookup"),
  bullet("idx_inventory_product_id — resolving live stock for a NoSQL product"),
);

// 5. NOSQL SCHEMA
children.push(
  pageBreak(),
  h1("5. Database Schema — NoSQL Side (Semi-/Unstructured Data)"),
  p("Three MongoDB-style collections hold data whose shape genuinely varies record-to-record: the product catalog (a laptop and a t-shirt need different attributes), reviews (optional fields such as seller responses or image attachments), and activity logs (a 'search' event and an 'add_to_cart' event carry completely different metadata)."),
  h2("5.1 products"),
  p("Flexible per-category attributes live in a nested attributes sub-document, avoiding either a wide table of mostly-NULL columns or a generic EAV table on the relational side."),
  code(`{
  "_id": "P00001",
  "name": "Sony WH-1000XM5 Wireless Headphones",
  "category": "Electronics", "brand": "Sony",
  "price": 349.99, "currency": "USD",
  "attributes": { "color": "Black", "battery_life_hrs": 30,
                  "connectivity": ["Bluetooth 5.2","USB-C"] },
  "tags": ["headphones","wireless","noise-cancelling"],
  "avg_rating": 4.6, "review_count": 128, "is_active": true
}`),
  h2("5.2 reviews"),
  code(`{
  "_id": "R000045", "product_id": "P00001", "user_id": 214,
  "rating": 5, "title": "Best headphones I've owned",
  "review_text": "Noise cancellation is superb...",
  "verified_purchase": true, "helpful_votes": 37,
  "seller_response": null, "review_date": "2025-03-02T08:15:00Z"
}`),
  h2("5.3 activity_logs"),
  p("The clearest case for schema flexibility: a search event and an add_to_cart event share only user_id/session_id/action_type/timestamp — everything else lives in a metadata field whose shape depends on action_type, with zero schema migration required to add a new event type."),
  code(`{
  "_id": "L0000998", "user_id": 214, "session_id": "sess_9f31ac",
  "action_type": "add_to_cart", "timestamp": "2025-06-11T14:02:31Z",
  "metadata": { "product_id": "P00001", "quantity": 1,
                "referrer": "search_results", "device": "mobile" }
}`),
  h2("5.4 Schema Validation & Indexes"),
  p("MongoDB's $jsonSchema validator (defined in nosql/schema_design.md) enforces required fields and types on insert without forcing a fixed shape for optional/variable fields. Indexes created:"),
  bullet("products: category, brand, tags (multikey), text index on name+description, price"),
  bullet("reviews: product_id, user_id, compound (product_id, rating)"),
  bullet("activity_logs: compound (user_id, timestamp), action_type, TTL index on timestamp (auto-purge after 180 days)"),
);

// 6. SAMPLE DATA
children.push(
  pageBreak(),
  h1("6. Sample Data"),
  p("Both databases were populated programmatically (scripts/generate_data.py) with randomized but realistic data — no external data-generation library was used, so the whole pipeline runs offline with zero third-party dependencies. Every table/collection comfortably exceeds the 100-record minimum:"),
  table(
    ["Store", "Table / Collection", "Record Count"],
    [
      ["SQL", "users", "150"],
      ["SQL", "orders", "220"],
      ["SQL", "order_items", "538"],
      ["SQL", "payments", "220"],
      ["SQL", "shipping", "112 (only shipped/delivered orders)"],
      ["SQL", "inventory", "177 (1-2 warehouse rows per product)"],
      ["NoSQL", "products", "120"],
      ["NoSQL", "reviews", "250"],
      ["NoSQL", "activity_logs", "400"],
    ],
    [2000, 4000, 3000]
  ),
  p(""),
  p("Order totals, tax, and shipping fees are computed from live product prices pulled from the NoSQL catalog at generation time (mirroring how the real application layer prices a cart), and order status distribution, payment success rates, and review ratings are weighted to resemble realistic e-commerce distributions rather than uniform randomness (e.g. 5-star reviews are more common than 1-star, 'delivered' is the most common order status)."),
);

// 7. QUERIES
const results = fs.readFileSync(`${BASE}/output/query_results.txt`, "utf8");
function extractSection(marker, nextMarker) {
  const start = results.indexOf(marker);
  const end = nextMarker ? results.indexOf(nextMarker) : results.length;
  return results.slice(start, end === -1 ? undefined : end).trim();
}
children.push(
  pageBreak(),
  h1("7. Functional Queries — CRUD & Aggregation"),
  p("All queries below are written in full in sql/queries.sql (15 SQL queries) and nosql/queries.js (15 MongoDB queries). This section shows a representative subset actually executed against the populated databases, with real captured output (full transcript: output/query_results.txt, 20 numbered queries)."),
  h2("7.1 SQL — CRUD"),
  h3("CREATE — register a user"),
  code(`INSERT INTO users (first_name,last_name,email,phone,password_hash,role,
    address_line1,city,state,postal_code,country)
VALUES ('Aisha','Khan','aisha.khan.demo@example.com', ...);`),
  code(extractSection("[1] CREATE", "[2] READ")),
  h3("READ — full order detail (join across 4 tables)"),
  code(`SELECT o.order_id, o.status, o.total_amount, oi.product_id, oi.quantity,
       p.payment_method, p.status AS payment_status, s.carrier, s.status
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
LEFT JOIN payments p ON p.order_id = o.order_id
LEFT JOIN shipping s ON s.order_id = o.order_id
WHERE o.order_id = 1;`),
  code(extractSection("[3] READ", "[4] UPDATE")),
  h3("UPDATE — order status transition"),
  code(extractSection("[4] UPDATE", "[5] DELETE")),
  h3("DELETE — guarded cancellation"),
  code(extractSection("[5] DELETE", "[6] AGGREGATION")),
  h2("7.2 SQL — Aggregation"),
  h3("Monthly revenue & order count"),
  code(extractSection("[6] AGGREGATION", "[7] AGGREGATION")),
  h3("Top customers by lifetime spend"),
  code(extractSection("[7] AGGREGATION", "[8] AGGREGATION")),
  h3("Order status funnel"),
  code(extractSection("[8] AGGREGATION", "[9] AGGREGATION")),
  h3("Payment method success rate"),
  code(extractSection("[9] AGGREGATION", "[10] AGGREGATION")),
  pageBreak(),
  h2("7.3 NoSQL — CRUD"),
  h3("CREATE — insert a product document"),
  code(extractSection("[11] CREATE", "[12] READ")),
  h3("READ — filtered, sorted find()"),
  code(`db.products.find({ category: "Electronics", price: { $lt: 200 } }).sort({ price: 1 });`),
  code(extractSection("[12] READ", "[13] READ")),
  h3("UPDATE — price change"),
  code(extractSection("[14] UPDATE", "[15] DELETE")),
  h3("DELETE — remove a document"),
  code(extractSection("[15] DELETE", "[16] AGGREGATION")),
  h2("7.4 NoSQL — Aggregation"),
  h3("Average rating per category (via $lookup + $group)"),
  code(`db.reviews.aggregate([
  { $lookup: { from: "products", localField: "product_id",
               foreignField: "_id", as: "product" } },
  { $unwind: "$product" },
  { $group: { _id: "$product.category", avgRating: { $avg: "$rating" },
              totalReviews: { $sum: 1 } } },
  { $sort: { avgRating: -1 } }
]);`),
  code(extractSection("[16] AGGREGATION", "[17] AGGREGATION")),
  h3("Top-rated products"),
  code(extractSection("[17] AGGREGATION", "[18] AGGREGATION")),
  h3("User action funnel (last 30 days)"),
  code(extractSection("[18] AGGREGATION", "[19] AGGREGATION")),
  h3("Most-searched keywords (mining flexible metadata)"),
  code(extractSection("[19] AGGREGATION", "[20] CROSS-DATABASE")),
  h2("7.5 Cross-Database Query"),
  p("The clearest demonstration of the hybrid design: a single logical 'product detail' answer assembled from both stores in one call."),
  code(extractSection("[20] CROSS-DATABASE")),
);

// 8. INTEGRATION LAYER
children.push(
  pageBreak(),
  h1("8. Application (Integration) Layer"),
  p("scripts/integration_layer.py defines ECommerceService, the single object every part of a real backend would call. It never lets a caller talk to SQLite or the document store directly — each method internally decides which store owns which piece of data and merges the results."),
  h2("8.1 place_order() — cross-database write coordination"),
  p("Demonstrates the central challenge of polyglot persistence: pricing comes from the NoSQL catalog (source of truth for product data), but the order itself must be written with full ACID guarantees on the SQL side, including an atomic, oversell-safe stock decrement."),
  code(`def place_order(self, user_id, cart_items):
    subtotal = 0.0
    for item in cart_items:
        product = self.nosql["products"].find_one({"_id": item["product_id"]})
        line_total = round(product["price"] * item["quantity"], 2)
        subtotal += line_total
        ...
    # SQL side: order + items + atomic stock decrement, inside a transaction
    cur.execute("INSERT INTO orders (...) VALUES (...)")
    ...
    cur.execute("""UPDATE inventory SET stock_quantity = stock_quantity - ?
                    WHERE product_id = ? AND stock_quantity >= ?""", ...)
    self.sql.commit()   # rolled back on any exception
    self.record_activity(user_id, "checkout_start", {...})   # NoSQL log write`),
  p("Live output from running this method:"),
  code(`svc.place_order(1, [{"product_id": "P00001", "quantity": 1},
                     {"product_id": "P00002", "quantity": 2}])
=> {'order_id': 221, 'subtotal': 890.2, 'tax': 71.22,
    'shipping': 0.0, 'total': 961.42}`),
  h2("8.2 get_product_detail() — cross-database read"),
  p("Combines the NoSQL product document, a live NoSQL aggregation over its reviews, and a real-time SQL stock count — the three pieces a product page needs, from the two databases that separately own them."),
  code(`detail = svc.get_product_detail("P00001")
=> Product : Sony Smartphone ($497.32)
   Rating  : {'avg_rating': None, 'review_count': 0}
   Stock   : 462 units across 1 warehouse(s)`),
  h2("8.3 get_user_dashboard() and search_products()"),
  p("get_user_dashboard() merges SQL order history with the NoSQL activity feed for an account page; search_products() runs a NoSQL tag/keyword search and enriches each hit with a live SQL stock lookup so the search-results page never shows an item as available when the warehouse count is actually zero."),
  code(`svc.search_products("wireless")
=> {'_id': 'P00045', 'name': 'HP Wireless Headphones', 'price': 1718.59,
    'avg_rating': 4.0, 'in_stock': True}
   {'_id': 'P00120', 'name': 'JBL Wireless Mouse', 'price': 76.39,
    'avg_rating': 3.33, 'in_stock': True}`),
);

// 9. OPTIMIZATION
children.push(
  pageBreak(),
  h1("9. Performance & Optimization Techniques"),
  h2("9.1 Indexing"),
  p("Every foreign key and every column that appears in a WHERE/JOIN/ORDER BY in Section 7's queries has a matching index (Section 4.3 for SQL, Section 5.4 for NoSQL). Without idx_orders_user_id, for example, the 'user order history' query degrades from an index seek to a full table scan as order volume grows; the same applies to the compound (user_id, timestamp) index on activity_logs, which is what lets 'this user's last 5 events' stay fast even with millions of log entries."),
  h2("9.2 Denormalization Where It Pays Off"),
  bullet("order_items.product_name_snapshot stores the product name at time of purchase, so an order's receipt never changes even if the product is later renamed or deleted from the catalog — avoiding a join back to NoSQL just to render order history."),
  bullet("products.avg_rating / products.review_count are pre-aggregated counters updated whenever a review is written, so the (very common) 'show star rating on the product card' path avoids re-running an aggregation over all reviews on every page view — a classic read-heavy/write-light trade-off."),
  h2("9.3 Query & Schema Design Choices"),
  bullet("Compound indexes are ordered to match actual query patterns, e.g. (status, order_date) supports both 'orders with this status' and 'orders with this status, most recent first' without a second index."),
  bullet("The inventory table is separated from the products document specifically so that high-frequency, small, atomic stock updates (which need row-level locking to prevent overselling) never contend with catalog reads/writes, which are comparatively rare and can tolerate eventual consistency."),
  bullet("A TTL index on activity_logs.timestamp lets MongoDB automatically expire old log documents instead of a manual batch-delete job, keeping the collection — and its indexes — from growing unbounded."),
  h2("9.4 Scaling Considerations (Design Discussion)"),
  p("Although this project runs on a single embedded instance for demonstration, the design anticipates standard scaling paths: the SQL side would use read replicas for reporting queries (Section 7.2's aggregations) to keep them off the primary that handles checkout writes; the NoSQL side is a natural candidate for sharding on category or product_id once the catalog grows past a single node's comfortable working set, since products/reviews/logs have no cross-document transactional requirement forcing them onto the same shard."),
);

// 10. CHALLENGES
children.push(
  pageBreak(),
  h1("10. Design Decisions & Challenges"),
  h2("10.1 Where to draw the SQL/NoSQL boundary"),
  p("The guiding rule applied throughout: if losing or corrupting a piece of data has a direct financial or legal consequence (an order total, a payment status, a stock count), it belongs in the SQL layer, where transactions and constraints can protect it. If a piece of data is read-heavy, evolves in shape over time, or its worst-case inconsistency is merely cosmetic (a stale review count, a slightly-delayed activity log), it belongs in the NoSQL layer, where schema flexibility and write throughput matter more than strict consistency."),
  h2("10.2 Referential integrity across two databases"),
  p("The single hardest problem in this design: order_items.product_id and inventory.product_id point into the NoSQL products collection, but no foreign key can enforce that across engines. The application layer (Section 8) is the only thing guaranteeing this reference stays valid — e.g. place_order() looks the product up before ever writing the order row, and product deletion would, in a production system, need a check (or soft-delete pattern) to avoid orphaning historical orders. This project's order_items.product_name_snapshot column is a direct mitigation: even if the NoSQL product document is later deleted, the historical order remains fully readable."),
  h2("10.3 Building without live database servers"),
  p("This project was implemented without network access to run MySQL/MongoDB server processes. Rather than only writing schema files that were never executed, a small embedded engine (document_store.py) was built to implement the real MongoDB query semantics used in nosql/queries.js, so every query result quoted in Section 7 is genuine, re-runnable output rather than a hypothetical example — a deliberate choice to keep the project's evidence honest."),
);

// 11. CONCLUSION
children.push(
  pageBreak(),
  h1("11. Conclusion"),
  p("This project demonstrates a complete, working hybrid database system for an e-commerce platform: a normalized, constraint-enforced SQL schema for accounts, orders, payments, shipping and inventory; a flexible NoSQL document design for the product catalog, reviews and activity logs; over a hundred realistic records in every table and collection; a full set of CRUD and aggregation queries proven against real data; an application layer that coordinates both stores into coherent business operations; and a set of indexing and denormalization choices justified by the query patterns actually exercised. The result reflects how production e-commerce systems genuinely split their data — not as an academic exercise in using two databases for their own sake, but because the two engines are each the right tool for a different half of the problem."),
);

// 12. APPENDIX
children.push(
  pageBreak(),
  h1("12. Appendix — Project File Structure"),
  code(`ecommerce_hybrid_db/
├── sql/
│   ├── schema.sql            DDL: 6 tables, constraints, indexes
│   └── queries.sql           15 CRUD + aggregation SQL queries
├── nosql/
│   ├── schema_design.md      Document structures, validation, indexes
│   └── queries.js            15 CRUD + aggregation MongoDB queries
├── scripts/
│   ├── document_store.py     Embedded document-DB engine (pymongo-style API)
│   ├── generate_data.py      Populates both databases (100+ rows/collection)
│   ├── integration_layer.py  ECommerceService — the application layer
│   └── run_all_queries.py    Executes & captures all 20 demo queries
├── diagrams/
│   ├── make_diagrams.py      Graphviz source for both diagrams
│   ├── er_diagram.png
│   └── architecture_diagram.png
├── data/                     Generated SQLite DB + JSON document store
└── output/
    └── query_results.txt     Captured output of every query, numbered 1-20`),
  h2("How to Run"),
  bullet("python3 scripts/generate_data.py        # builds & populates both databases"),
  bullet("python3 scripts/run_all_queries.py       # runs all 20 CRUD/aggregation queries"),
  bullet("python3 scripts/integration_layer.py     # runs the 4 application-layer demos"),
  bullet("python3 diagrams/make_diagrams.py        # regenerates both diagrams"),
);

const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
      heading1: { run: { color: NAVY, size: 30, bold: true }, paragraph: { spacing: { before: 360, after: 160 } } },
      heading2: { run: { color: DARK, size: 25, bold: true } },
      heading3: { run: { color: GREY, size: 22, bold: true, italics: true } },
    },
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 } } }, // A4
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(`${BASE}/report/Hybrid_Ecommerce_Database_Report.docx`, buf);
  console.log("Report written.");
});

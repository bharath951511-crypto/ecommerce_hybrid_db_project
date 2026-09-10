// ============================================================================
//  FUNCTIONAL NOSQL QUERIES — CRUD + Aggregation + Retrieval  (mongosh)
//  Collections: products, reviews, activity_logs
//  (Executed live in this project via the equivalent document_store.py API
//   — see scripts/run_all_queries.py for actual output.)
// ============================================================================

// ---------------------------------------------------------------- CREATE ---
// 1. Add a new product
db.products.insertOne({
  _id: "P00121", name: "Apple AirPods Pro", category: "Electronics", brand: "Apple",
  description: "Active noise cancellation, adaptive transparency.", price: 249.00,
  currency: "USD", attributes: { color: "White", battery_life_hrs: 6 },
  tags: ["electronics", "apple", "airpods"], images: [], avg_rating: 0,
  review_count: 0, is_active: true, created_at: new Date()
});

// 2. Add a review for a product
db.reviews.insertOne({
  _id: "R000251", product_id: "P00001", user_id: 12, rating: 5,
  title: "Fantastic", review_text: "Sound quality is unreal.",
  verified_purchase: true, helpful_votes: 0, images: [],
  seller_response: null, review_date: new Date()
});

// ------------------------------------------------------------------ READ ---
// 3. Find all electronics under $200, cheapest first
db.products.find({ category: "Electronics", price: { $lt: 200 } }).sort({ price: 1 });

// 4. Find a single product by id
db.products.findOne({ _id: "P00001" });

// 5. Get all reviews for a product, most helpful first
db.reviews.find({ product_id: "P00001" }).sort({ helpful_votes: -1 });

// 6. Text/tag search across products (search bar use-case)
db.products.find({ tags: "wireless" });

// ---------------------------------------------------------------- UPDATE ---
// 7. Change a product's price
db.products.updateOne({ _id: "P00001" }, { $set: { price: 329.99 } });

// 8. Increment helpful_votes on a review (concurrent-safe counter)
db.reviews.updateOne({ _id: "R000045" }, { $inc: { helpful_votes: 1 } });

// 9. Bulk-deactivate all products of a brand (e.g. discontinued line)
db.products.updateMany({ brand: "OldBrand" }, { $set: { is_active: false } });

// ---------------------------------------------------------------- DELETE ---
// 10. Remove a single review (e.g. moderation takedown)
db.reviews.deleteOne({ _id: "R000045" });

// 11. Purge activity logs older than 180 days (in production this is a TTL
//     index, shown here as an explicit query for clarity)
db.activity_logs.deleteMany({ timestamp: { $lt: new Date(Date.now() - 180*24*60*60*1000) } });

// ------------------------------------------------------------ AGGREGATION ---
// 12. Average rating & review count per category (join across collections)
db.reviews.aggregate([
  { $lookup: { from: "products", localField: "product_id", foreignField: "_id", as: "product" } },
  { $unwind: "$product" },
  { $group: { _id: "$product.category", avgRating: { $avg: "$rating" }, totalReviews: { $sum: 1 } } },
  { $sort: { avgRating: -1 } }
]);

// 13. Top 10 highest-rated products with at least 3 reviews
db.products.aggregate([
  { $match: { review_count: { $gte: 3 } } },
  { $sort: { avg_rating: -1 } },
  { $limit: 10 },
  { $project: { name: 1, brand: 1, avg_rating: 1, review_count: 1 } }
]);

// 14. User behaviour funnel: count of each action_type in the last 30 days
db.activity_logs.aggregate([
  { $match: { timestamp: { $gte: new Date(Date.now() - 30*24*60*60*1000) } } },
  { $group: { _id: "$action_type", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);

// 15. Most-searched keywords (mining the flexible metadata field)
db.activity_logs.aggregate([
  { $match: { action_type: "search" } },
  { $group: { _id: "$metadata.query", searches: { $sum: 1 } } },
  { $sort: { searches: -1 } },
  { $limit: 10 }
]);

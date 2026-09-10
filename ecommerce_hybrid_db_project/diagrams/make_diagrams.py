import graphviz

OUT_DIR = "/home/claude/ecommerce_hybrid_db/diagrams"

# ---------------------------------------------------------------- ER DIAGRAM
er = graphviz.Digraph("ER", format="png")
er.attr(rankdir="LR", bgcolor="white", fontname="Helvetica", splines="ortho")
er.attr("node", shape="none", fontname="Helvetica", fontsize="10")

def table_html(title, rows, color="#2C3E50"):
    html = f'''<
<table border="0" cellborder="1" cellspacing="0" cellpadding="6">
<tr><td bgcolor="{color}"><font color="white"><b>{title}</b></font></td></tr>'''
    for r in rows:
        html += f'<tr><td align="left">{r}</td></tr>'
    html += "</table>>"
    return html

er.node("users", table_html("USERS", [
    "<b>PK user_id</b>", "first_name", "last_name", "email (UQ)", "phone",
    "role", "address_line1/2, city, state", "postal_code, country", "created_at"]))

er.node("orders", table_html("ORDERS", [
    "<b>PK order_id</b>", "<i>FK user_id</i>", "order_date", "status",
    "subtotal_amount", "tax_amount", "shipping_amount", "total_amount"], color="#1F618D"))

er.node("order_items", table_html("ORDER_ITEMS", [
    "<b>PK order_item_id</b>", "<i>FK order_id</i>",
    "<i>REF product_id (NoSQL)</i>", "product_name_snapshot",
    "quantity", "unit_price", "line_total"], color="#1F618D"))

er.node("payments", table_html("PAYMENTS", [
    "<b>PK payment_id</b>", "<i>FK order_id</i>", "payment_method",
    "amount", "status", "transaction_ref (UQ)", "paid_at"], color="#1F618D"))

er.node("shipping", table_html("SHIPPING", [
    "<b>PK shipping_id</b>", "<i>FK order_id</i>", "carrier",
    "tracking_number", "ship_address", "status",
    "shipped_date, estimated_delivery, delivered_date"], color="#1F618D"))

er.node("inventory", table_html("INVENTORY", [
    "<b>PK inventory_id</b>", "<i>REF product_id (NoSQL)</i>",
    "warehouse_location", "stock_quantity", "reorder_level", "last_restocked"], color="#117864"))

er.node("products", table_html("products  (MongoDB)", [
    "<b>_id</b>", "name, category, brand", "description, price",
    "attributes { ... flexible ... }", "tags[ ]", "avg_rating, review_count"], color="#B7950B"))

er.node("reviews", table_html("reviews  (MongoDB)", [
    "<b>_id</b>", "<i>REF product_id</i>", "<i>REF user_id</i>",
    "rating, title, review_text", "verified_purchase, helpful_votes"], color="#B7950B"))

er.node("activity_logs", table_html("activity_logs  (MongoDB)", [
    "<b>_id</b>", "<i>REF user_id</i>", "session_id", "action_type",
    "timestamp", "metadata { ... variable shape ... }"], color="#B7950B"))

er.edge("users", "orders", label="1 : N", color="#1F618D")
er.edge("orders", "order_items", label="1 : N", color="#1F618D")
er.edge("orders", "payments", label="1 : N", color="#1F618D")
er.edge("orders", "shipping", label="1 : N", color="#1F618D")
er.edge("order_items", "products", label="references", style="dashed", color="#B7950B")
er.edge("inventory", "products", label="references", style="dashed", color="#B7950B")
er.edge("products", "reviews", label="1 : N", color="#B7950B")
er.edge("products", "activity_logs", label="referenced in metadata", style="dashed", color="#B7950B")
er.edge("users", "reviews", label="references", style="dashed", color="#B7950B")
er.edge("users", "activity_logs", label="references", style="dashed", color="#B7950B")

er.render(f"{OUT_DIR}/er_diagram", cleanup=True)
print("ER diagram written")

# ---------------------------------------------------------- ARCHITECTURE DIAGRAM
arch = graphviz.Digraph("Architecture", format="png")
arch.attr(rankdir="TB", bgcolor="white", fontname="Helvetica", fontsize="11")
arch.attr("node", fontname="Helvetica", fontsize="10", style="filled", fontcolor="white")

arch.node("client", "Client / API Consumer\n(CLI demo scripts in this project)",
            shape="box", fillcolor="#5D6D7E")
arch.node("app", "APPLICATION LAYER\nECommerceService (integration_layer.py)\n"
                 "place_order() · get_product_detail() ·\nget_user_dashboard() · search_products()",
            shape="box3d", fillcolor="#8E44AD")

with arch.subgraph(name="cluster_sql") as c:
    c.attr(label="SQL DATABASE  (MySQL / SQLite — ACID)", style="rounded,filled",
            fillcolor="#EBF5FB", fontcolor="#1F618D", labeljust="l")
    c.node("sql_tables", "users · orders · order_items ·\npayments · shipping · inventory",
            shape="cylinder", fillcolor="#1F618D")

with arch.subgraph(name="cluster_nosql") as c:
    c.attr(label="NOSQL DATABASE  (MongoDB — flexible schema)", style="rounded,filled",
            fillcolor="#FEF9E7", fontcolor="#B7950B", labeljust="l")
    c.node("nosql_cols", "products · reviews ·\nactivity_logs",
            shape="cylinder", fillcolor="#B7950B")

arch.edge("client", "app", label="requests")
arch.edge("app", "sql_tables", label="ACID reads/writes\n(orders, payments, stock)")
arch.edge("app", "nosql_cols", label="flexible reads/writes\n(catalog, reviews, logs)")
arch.edge("sql_tables", "nosql_cols", label="product_id / user_id\nlogical reference\n(app-enforced, no native FK)",
            style="dashed", dir="both", color="#7B241C", fontcolor="#7B241C")

arch.render(f"{OUT_DIR}/architecture_diagram", cleanup=True)
print("Architecture diagram written")


DROP TABLE IF EXISTS shipping;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id         INTEGER PRIMARY KEY AUTO_INCREMENT,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    password_hash   VARCHAR(255) NOT NULL,
    role            ENUM('customer','admin','vendor') NOT NULL DEFAULT 'customer',
    address_line1   VARCHAR(120),
    address_line2   VARCHAR(120),
    city            VARCHAR(60),
    state           VARCHAR(60),
    postal_code     VARCHAR(20),
    country         VARCHAR(60),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id         INTEGER NOT NULL,
    order_date      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM('pending','confirmed','shipped','delivered','cancelled','returned')
                    NOT NULL DEFAULT 'pending',
    subtotal_amount DECIMAL(10,2) NOT NULL,
    tax_amount      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    shipping_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount    DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_orders_total CHECK (total_amount >= 0)
);


CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER NOT NULL,
    product_id      VARCHAR(24) NOT NULL,   -- references MongoDB products._id
    product_name_snapshot VARCHAR(150) NOT NULL,  -- denormalised for history
    quantity        INTEGER NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    line_total      DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_items_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_items_qty CHECK (quantity > 0)
);


CREATE TABLE payments (
    payment_id      INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER NOT NULL,
    payment_method  ENUM('credit_card','debit_card','upi','net_banking','wallet','cod')
                    NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    status          ENUM('initiated','success','failed','refunded') NOT NULL DEFAULT 'initiated',
    transaction_ref VARCHAR(64) NOT NULL UNIQUE,
    paid_at         DATETIME,
    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE shipping (
    shipping_id     INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER NOT NULL,
    carrier         VARCHAR(60) NOT NULL,
    tracking_number VARCHAR(64) NOT NULL,
    ship_address    VARCHAR(200) NOT NULL,
    status          ENUM('processing','shipped','in_transit','delivered','delayed')
                    NOT NULL DEFAULT 'processing',
    shipped_date    DATETIME,
    estimated_delivery DATETIME,
    delivered_date  DATETIME,
    CONSTRAINT fk_shipping_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE inventory (
    inventory_id    INTEGER PRIMARY KEY AUTO_INCREMENT,
    product_id      VARCHAR(24) NOT NULL,   -- references MongoDB products._id
    warehouse_location VARCHAR(80) NOT NULL,
    stock_quantity  INTEGER NOT NULL DEFAULT 0,
    reorder_level   INTEGER NOT NULL DEFAULT 10,
    last_restocked  DATETIME,
    CONSTRAINT chk_inv_qty CHECK (stock_quantity >= 0),
    UNIQUE KEY uq_product_warehouse (product_id, warehouse_location)
);

CREATE INDEX idx_users_email          ON users(email);
CREATE INDEX idx_users_city           ON users(city);
CREATE INDEX idx_orders_user_id       ON orders(user_id);
CREATE INDEX idx_orders_status_date   ON orders(status, order_date);
CREATE INDEX idx_items_order_id       ON order_items(order_id);
CREATE INDEX idx_items_product_id     ON order_items(product_id);
CREATE INDEX idx_payments_order_id    ON payments(order_id);
CREATE INDEX idx_payments_status      ON payments(status);
CREATE INDEX idx_shipping_order_id    ON shipping(order_id);
CREATE INDEX idx_shipping_tracking    ON shipping(tracking_number);
CREATE INDEX idx_inventory_product_id ON inventory(product_id);

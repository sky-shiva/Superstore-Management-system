-- --------------------------------------------------------------------------------------
-- Database Setup
-- Run this script in MySQL Workbench to create the database and all necessary tables.
-- --------------------------------------------------------------------------------------

-- Create the Database
CREATE DATABASE IF NOT EXISTS superstore_db;
USE superstore_db;

-- 1. Users Table for Login Credentials
-- Roles: 'billing' (for cashiers) and 'admin' (for inventory)
CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Store actual passwords in production for security, but using simple strings here for the CLI example logic.
    role VARCHAR(20) NOT NULL
);

-- 2. Inventory (Products) Table
CREATE TABLE IF NOT EXISTS Inventory (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    price DECIMAL(10, 2) NOT NULL, -- Currency should use DECIMAL for precision
    stock_quantity INT NOT NULL,
    CHECK (price >= 0),
    CHECK (stock_quantity >= 0)
);

-- 3. Customers Table
CREATE TABLE IF NOT EXISTS Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    mobile_number VARCHAR(15) UNIQUE,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Orders Table (To store header/summary of each transaction)
CREATE TABLE IF NOT EXISTS Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Paid',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

-- 5. Order Items Table (To store details of what was purchased in an order)
CREATE TABLE IF NOT EXISTS OrderItems (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_sale DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_id) REFERENCES Inventory(product_id),
    CHECK (quantity > 0)
);

-- --------------------------------------------------------------------------------------
-- Initial Data Population (Credentials and Inventory)
-- --------------------------------------------------------------------------------------

-- Add Initial Users
-- NOTE: In a real system, passwords should be securely hashed (e.g., using SHA256 or bcrypt).
INSERT INTO Users (username, password_hash, role) VALUES
('cashier', 'pass123', 'billing'),
('manager', 'admin456', 'admin');

-- Add Initial Inventory
INSERT INTO Inventory (name, price, stock_quantity) VALUES
('Maggie Noodles', 15.00, 150),
('Sunfeast Biscuit', 25.50, 200),
('SurfExcel Detergent (1kg)', 120.00, 80),
('Pepsi Can (300ml)', 40.00, 300),
('Dairy Milk Chocolate', 10.00, 500);

SELECT * FROM Users;
SELECT * FROM Inventory;

-- Verify setup
SELECT 'Database setup complete!' AS Status;



]

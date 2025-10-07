# Super Store Management System (CLI)

This is a simple Command Line Interface (CLI) application designed to manage the core operations of a small retail superstore, including **billing/point-of-sale** and **inventory management**. It utilizes **Python** for the application logic and **MySQL** for persistent data storage, demonstrating key concepts like database connectivity, transaction management, and role-based authentication.

## ✨ Features

* **Role-Based Access Control:** Separate login portals for `cashier` (billing) and `manager` (admin).
* **Billing/POS System:**
    * Interactive menu to add items to an order.
    * Automatic stock validation.
    * **Transactional Processing:** Ensures the entire order (Order header, Order Items, and Inventory stock update) succeeds or fails as a single unit.
    * Detailed Receipt Generation.
* **Inventory Management (Admin):**
    * Add new products with initial stock.
    * Update stock for existing products.
* **Reporting (Admin):**
    * View current inventory.
    * Calculate and display total store earnings from all historical orders.
* **Customer Tracking:** Records customer details (mobile, email) upon checkout.

## 📦 Project Structure

| File | Description |
| :--- | :--- |
| `project.sql` | **Database setup script** for MySQL. Creates the `superstore_db` database and all necessary tables, including initial users and inventory. |
| `superstore_cli.py` | **Main Python application.** Contains all the CLI functions, database connection logic, authentication, and core business functions (billing, inventory, reports). |

## 🛠️ Setup and Installation

### 1. MySQL Database Setup

1.  **Install MySQL:** Ensure you have a running MySQL Server instance (e.g., using XAMPP, a standalone installation, or Docker).
2.  **Run SQL Script:** Execute the full content of the `project.sql` file in your MySQL client (like MySQL Workbench or the `mysql` CLI). This script will:
    * Create the `superstore_db` database.
    * Create the five core tables: `Users`, `Inventory`, `Customers`, `Orders`, and `OrderItems`.
    * Populate initial data: two users (`cashier`, `manager`) and five inventory items.

### 2. Python Environment Setup

1.  **Install Python:** Make sure you have Python (3.x recommended) installed.
2.  **Install Required Library:** Install the MySQL Connector for Python:

    ```bash
    pip install mysql-connector-python
    ```

### 3. Configure Database Connection

Open the `superstore_cli.py` file and update the `DB_CONFIG` dictionary with your local MySQL credentials.

```python
# superstore_cli.py (Section 1. DATABASE CONFIGURATION)

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',      # <-- CHANGE THIS
    'password': 'your_mysql_password', # <-- CHANGE THIS
    'database': 'superstore_db'
}

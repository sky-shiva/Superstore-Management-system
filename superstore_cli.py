import mysql.connector
from getpass import getpass   # Purpose: Safely take password input from the user without showing it on the screen.
import os
import datetime

# ------------------------------------------------------------------------------
# 1. DATABASE CONFIGURATION (*** CRITICAL: CHANGE THESE VALUES ***)
# ------------------------------------------------------------------------------


# host, user, password, and database are the minimum required to connect to a MySQL database.

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',      
    'password': 'shiva7781', 
    'database': 'superstore_db'
}

'''Key Purpose host MySQL server address (localhost or IP) user Username to 
login password Password for the userdatabase Name of the database to useport Port MySQL is running on (default 3306)
charset	Character set used for connection (optional)
auth_plugin	Authentication plugin (optional, e.g., 'mysql_native_password')'''

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear') # This line clears the terminal screen in a cross-platform way, using 'cls' for Windows and 'clear' for Linux/macOS, chosen based on os.name.

def connect_db():
    """Establishes and returns a database connection."""
    try:
        # Attempt to connect to the database using the configuration
        conn = mysql.connector.connect(**DB_CONFIG)  # mysql.connector.connect(**DB_CONFIG) → This is the key part: it connects to your MySQL database.
        # The ** just unpacks this dictionary into keyword arguments for the function.
        return conn
    except mysql.connector.Error as err:
        print(f"\n--- DATABASE CONNECTION FAILED ---")
        print(f"Error: {err}")
        print("\nEnsure the following:")
        print("1. Your **MySQL Server** is running.")
        print("2. The 'host', 'user', and 'password' in the Python file are **correct**.")
        print("3. The database name **'superstore_db'** exists and is spelled correctly.")
        input("\nPress Enter to return to the main menu...")
        return None

# ------------------------------------------------------------------------------
# 2. LOGIN & AUTHENTICATION
# ------------------------------------------------------------------------------

def authenticate_user(role_required):
    """Handles username and password authentication."""
    conn = connect_db()
    if not conn:
        return False, None
    
    cursor = conn.cursor(dictionary=True)
    print(f"\n--- {role_required.upper()} LOGIN ---")
    username = input("Username: ")
    print("(Note: Password input is hidden for security.)")
    password = getpass("Password: ")
    
    try:
        # Check username, password, and required role
        # IMPORTANT: The 'password_hash' column stores the raw password string for this example
        query = ("SELECT username, role FROM Users WHERE username = %s AND password_hash = %s AND role = %s")
        cursor.execute(query, (username, password, role_required))
        user = cursor.fetchone()
        
        if user:
            print(f"\n--- Login Successful. Welcome, {user['username']} ({user['role']}) ---\n")
            return True, user['username']
        else:
            print("\n!!! Invalid credentials or insufficient role access. !!!")
            input("Press Enter to continue...")
            return False, None
            
    except mysql.connector.Error as err:
        print(f"\n!!! DB Error during authentication: {err} !!!")
        input("Press Enter to continue...")
        return False, None
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ------------------------------------------------------------------------------
# 3. BILLING PORTAL FUNCTIONS
# ------------------------------------------------------------------------------

def get_inventory(conn):
    """Retrieves current inventory for the menu."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT product_id, name, price, stock_quantity FROM Inventory ORDER BY product_id")
    inventory = cursor.fetchall()
    cursor.close()
    
    # CRITICAL FIX: Convert price from Decimal (MySQL's default for DECIMAL types) to float.
    for item in inventory:
        item['price'] = float(item['price'])
        
    return inventory

def generate_receipt(order_id, order_list, total_amount, mobile, customer_name):
    """Generates and prints a detailed receipt."""
    receipt = []
    receipt.append("=============================================")
    receipt.append("          SUPER STORE SALES RECEIPT          ")
    receipt.append("=============================================")
    receipt.append(f"Order ID: {order_id:<20} Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    receipt.append(f"Customer Name: {customer_name}")
    receipt.append(f"Customer Mobile: {mobile}")
    receipt.append("---------------------------------------------")
    receipt.append("Item                    Qty   Price    Total")
    receipt.append("---------------------------------------------")
    
    for item in order_list:
        name = item['name'][:20].ljust(20)
        qty = str(item['quantity']).ljust(3)
        price = f"₹{item['price']:.2f}".ljust(6)
        subtotal = f"₹{item['subtotal']:.2f}"
        receipt.append(f"{name} {qty} {price} {subtotal}")

    receipt.append("---------------------------------------------")
    receipt.append(f"Subtotal:                               ₹{total_amount:.2f}")
    receipt.append(f"TOTAL AMOUNT:                           ₹{total_amount:.2f}")
    receipt.append("=============================================\n")
    
    print('\n'.join(receipt))

def process_billing_transaction(conn, order_list, total_amount):
    """Inserts order, order items, updates inventory, and generates receipt in a transaction."""
    
    # 1. Get Customer Info and Validate
    print("\n--- CUSTOMER DETAILS ---")
    
    name = input("Customer Name (Required): ").strip()
    mobile = input("Customer Mobile Number (10 Digits Required): ").strip()
    email = input("Customer Email (Optional, press Enter): ").strip()
    
    if not name:
        print("!!! TRANSACTION FAILED: Customer name is required. !!!")
        return

    # CRITICAL: Mobile number validation (exactly 10 digits)
    if not mobile or not mobile.isdigit() or len(mobile) != 10:
        print("!!! TRANSACTION FAILED: Mobile number must be exactly 10 digits and contain only numbers. !!!")
        return

    cursor = None
    order_id = None 
    customer_name = name 
    
    try:
        cursor = conn.cursor()

        # FIX: Rollback any hanging transaction state before starting a new one. 
        conn.rollback() 
        conn.start_transaction()

        # 2. Check/Insert Customer
        customer_id = None
        
        # Check by mobile number
        cursor.execute("SELECT customer_id, name FROM Customers WHERE mobile_number = %s", (mobile,))
        customer = cursor.fetchone()

        if customer:
            customer_id = customer[0]
            # Use the name found in the database for the receipt
            customer_name = customer[1] 
        else:
            # Insert new customer, including name (must match CHAR(10) constraint)
            customer_insert_query = "INSERT INTO Customers (name, mobile_number, email) VALUES (%s, %s, %s)"
            # Ensure mobile number is exactly 10 chars, which is guaranteed by the validation above
            cursor.execute(customer_insert_query, (name, mobile, email if email else None))
            customer_id = cursor.lastrowid
            
        # 3. Insert Order
        order_insert_query = "INSERT INTO Orders (customer_id, total_amount) VALUES (%s, %s)"
        cursor.execute(order_insert_query, (customer_id, total_amount))
        order_id = cursor.lastrowid

        # 4. Insert Order Items and Update Inventory Stock
        update_stock_query = "UPDATE Inventory SET stock_quantity = stock_quantity - %s WHERE product_id = %s AND stock_quantity >= %s"
        order_item_insert_query = "INSERT INTO OrderItems (order_id, product_id, quantity, price_at_sale) VALUES (%s, %s, %s, %s)"

        for item in order_list:
            # Check if stock update will be successful
            cursor.execute(update_stock_query, (item['quantity'], item['product_id'], item['quantity']))
            
            if cursor.rowcount == 0:
                raise Exception(f"Insufficient stock or invalid product ID for {item['name']}. Aborting.")

            # Insert into OrderItems
            # item['price'] is float, but MySQL connector handles conversion to DECIMAL
            cursor.execute(order_item_insert_query, (order_id, item['product_id'], item['quantity'], item['price']))

        # 5. Commit Transaction
        conn.commit()
        
        # 6. Generate Receipt (called only on successful commit)
        generate_receipt(order_id, order_list, total_amount, mobile, customer_name)

    except Exception as e:
        # Rollback on any failure
        conn.rollback()
        print(f"\n!!! TRANSACTION FAILED: {e} !!!")
        
    finally:
        # Ensure cursor is closed after transaction attempt
        if cursor:
            cursor.close()


def billing_portal():
    """Main function for the billing section with interactive input."""
    conn = connect_db()
    if not conn: return

    order_list = []
    total_bill = 0.0

    while True:
        try:
            inventory = get_inventory(conn)
        except mysql.connector.Error as e:
            print(f"Error fetching inventory: {e}")
            input("\nPress Enter to continue...")
            break

        clear_screen()
        print("--- CURRENT INVENTORY & BILLING ---")
        print("| No. | Item Name                 | Price (₹) | Stock |")
        print("-----------------------------------------------------")
        
        product_map = {}
        for item in inventory:
            # item['price'] is already a float
            print(f"| {item['product_id']:<3} | {item['name'][:25]:<25} | {item['price']:<9.2f} | {item['stock_quantity']:<5} |")
            product_map[str(item['product_id'])] = item
            
        print("-----------------------------------------------------")

        if order_list:
            print("\n--- CURRENT ORDER ITEMS ---")
            for item in order_list:
                print(f"- {item['name']} x{item['quantity']} (₹{item['subtotal']:.2f})")
            print(f"TOTAL: ₹{total_bill:.2f}\n")
        
        # Clear options for clarity
        print("\nOptions: [ITEM NO.] to add item | [C]heckout | [R]eset | [D] Done | [B]ack (Main Menu)")
        
        # New interactive input logic
        user_input = input("Enter Item No. or Command: ").strip().lower()

        if user_input in ['b', 'back']:
            print("Exiting Billing Portal.")
            break
        
        elif user_input in ['r', 'reset']:
            order_list = []
            total_bill = 0.0
            print("Order reset.")
            input("\nPress Enter to continue...")
            continue

        elif user_input in ['c', 'checkout', 'd', 'done']:
            if order_list:
                process_billing_transaction(conn, order_list, total_bill)
                # Reset order state after transaction attempt
                order_list = []
                total_bill = 0.0
                input("\nPress Enter to continue...")
            else:
                print("!!! Order is empty. Cannot check out. !!!")
                input("\nPress Enter to continue...")
            continue
        
        # Process as Item ID input
        p_id = user_input
        if p_id in product_map:
            item = product_map[p_id]
            
            try:
                qty_input = input(f"Enter quantity for {item['name']} (Stock: {item['stock_quantity']}): ").strip()
                if not qty_input:
                     print("!!! Quantity cannot be empty. !!!")
                     input("\nPress Enter to continue...")
                     continue
                qty = int(qty_input)
                
                if qty <= 0:
                    print("!!! Quantity must be a positive number. !!!")
                    input("\nPress Enter to continue...")
                    continue
                
                if qty > item['stock_quantity']:
                    print(f"!!! Insufficient stock! Only {item['stock_quantity']} available for {item['name']}. !!!")
                    input("\nPress Enter to continue...")
                    continue

                # Calculation uses float values
                subtotal = item['price'] * qty
                total_bill += subtotal
                
                # Check if item is already in order_list to consolidate
                found = False
                for existing_item in order_list:
                    if existing_item['product_id'] == item['product_id']:
                        existing_item['quantity'] += qty
                        existing_item['subtotal'] += subtotal
                        found = True
                        break
                
                if not found:
                    # Store a temporary entry for the current bill
                    order_list.append({
                        'product_id': item['product_id'],
                        'name': item['name'],
                        'quantity': qty,
                        'price': item['price'],
                        'subtotal': subtotal
                    })

                print(f"-> Added {item['name']} x{qty}. Current Total: ₹{total_bill:.2f}")

            except ValueError:
                print("!!! Invalid quantity. Must be a whole number. !!!")
                input("\nPress Enter to continue...")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                input("\nPress Enter to continue...")

        else:
            print(f"!!! Invalid Item Number or Command: {user_input} !!!")
            input("\nPress Enter to continue...")

    if conn and conn.is_connected():
        conn.close()

# ------------------------------------------------------------------------------
# 4. INVENTORY PORTAL FUNCTIONS (Admin Only)
# ------------------------------------------------------------------------------

def get_total_earnings(conn):
    """Calculates and returns the total earnings from all completed orders."""
    cursor = conn.cursor()
    try:
        # SUM(total_amount) from Orders table
        query = "SELECT SUM(total_amount) FROM Orders"
        cursor.execute(query)
        total_earnings = cursor.fetchone()[0]
        # FIX: Explicitly convert Decimal from MySQL to float for consistency.
        return float(total_earnings) if total_earnings is not None else 0.0
    except mysql.connector.Error as err:
        print(f"!!! DB Error fetching total earnings: {err} !!!")
        return 0.0
    finally:
        cursor.close()

def view_reports(conn):
    """Displays key reports like total earnings."""
    clear_screen()
    print("\n--- FINANCIAL REPORTS ---")
    
    total_earnings = get_total_earnings(conn)
    
    print("\n=============================================")
    print(f"💰 TOTAL SUPERSTORE EARNINGS: ₹{total_earnings:.2f}")
    print("=============================================")
    input("\nPress Enter to return to the Inventory Menu...")

def add_new_product(conn):
    """Adds a new unique product to the inventory."""
    print("\n--- ADD NEW PRODUCT ---")
    name = input("Enter new product name: ").strip()
    
    if not name:
        print("!!! Product name cannot be empty. !!!")
        return

    try:
        price = float(input("Enter price (e.g., 12.50): "))
        if price < 0: raise ValueError
    except ValueError:
        print("!!! Invalid price. Must be a non-negative number. !!!")
        return

    try:
        quantity = int(input("Enter initial stock quantity: "))
        if quantity < 0: raise ValueError
    except ValueError:
        print("!!! Invalid quantity. Must be a non-negative integer. !!!")
        return

    cursor = conn.cursor()
    try:
        query = "INSERT INTO Inventory (name, price, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, price, quantity))
        conn.commit()
        print(f"\n-> Successfully added new product: {name} (ID: {cursor.lastrowid})")
    except mysql.connector.IntegrityError:
        print(f"!!! Error: Product named '{name}' already exists. !!!")
    except mysql.connector.Error as err:
        print(f"!!! DB Error: {err} !!!")
    finally:
        cursor.close()

def update_stock(conn):
    """Updates the stock quantity of an existing product."""
    
    inventory = get_inventory(conn)
    if not inventory:
        print("Inventory is empty.")
        return

    print("\n--- UPDATE EXISTING STOCK ---")
    print("| No. | Item Name                 | Stock |")
    print("-----------------------------------------")
    product_map = {}
    for item in inventory:
        print(f"| {item['product_id']:<3} | {item['name'][:25]:<25} | {item['stock_quantity']:<5} |")
        product_map[str(item['product_id'])] = item
    print("-----------------------------------------")

    p_id = input("Enter Item No. to update stock: ").strip()
    if p_id not in product_map:
        print("!!! Invalid Item Number. !!!")
        return

    try:
        add_qty = int(input("Enter quantity to ADD to stock: "))
        if add_qty < 0: raise ValueError
    except ValueError:
        print("!!! Quantity to add must be a positive integer. !!!")
        return

    cursor = conn.cursor()
    try:
        query = "UPDATE Inventory SET stock_quantity = stock_quantity + %s WHERE product_id = %s"
        cursor.execute(query, (add_qty, p_id))
        conn.commit()
        print(f"\n-> Stock updated for {product_map[p_id]['name']}. Added {add_qty} units.")
    except mysql.connector.Error as err:
        print(f"!!! DB Error: {err} !!!")
    finally:
        cursor.close()

def inventory_portal():
    """Main function for the inventory management section."""
    conn = connect_db()
    if not conn: return

    while True:
        clear_screen()
        print("\n--- INVENTORY MANAGEMENT PORTAL ---")
        print("1. Add New Product (Name, Price, Initial Stock)")
        print("2. Update Existing Product Stock")
        print("3. View Current Inventory")
        print("4. View Financial Reports (Total Earnings)")
        print("5. Back to Main Menu")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            add_new_product(conn)
        elif choice == '2':
            update_stock(conn)
        elif choice == '3':
            inventory = get_inventory(conn)
            if inventory:
                print("\n--- CURRENT INVENTORY ---")
                print("| ID | Item Name                 | Price (₹) | Stock |")
                print("-------------------------------------------------")
                for item in inventory:
                    print(f"| {item['product_id']:<2} | {item['name'][:25]:<25} | {item['price']:<9.2f} | {item['stock_quantity']:<5} |")
                print("-------------------------------------------------")
            else:
                print("\nInventory is currently empty.")
        elif choice == '4':
            view_reports(conn)
        elif choice == '5':
            print("Exiting Inventory Portal.")
            break
        else:
            print("!!! Invalid choice. Please select 1-5. !!!")
            
        input("\nPress Enter to continue...")

    if conn and conn.is_connected():
        conn.close()




# ------------------------------------------------------------------------------
# 5. MAIN APPLICATION ENTRY POINT
# ------------------------------------------------------------------------------

def main():
    """Displays the main menu and handles portal access."""
    while True:
        clear_screen()
        print("=============================================")
        print(" SUPER STORE MANAGEMENT SYSTEM (CLI)")
        print("=============================================")
        print("1. Billing Section Login (CASHIER)")
        print("2. Inventory Management Login (MANAGER)")
        print("3. Exit System")
        print("---------------------------------------------")

        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            logged_in, username = authenticate_user('billing')
            if logged_in:
                billing_portal()
        elif choice == '2':
            logged_in, username = authenticate_user('admin')
            if logged_in:
                inventory_portal()
        elif choice == '3':
            print("\nSystem shutting down. Goodbye!")
            break
        else:
            print("!!! Invalid choice. Please select 1, 2, or 3. !!!")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()

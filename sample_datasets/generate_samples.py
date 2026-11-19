import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def create_online_store_orders():
    path = DATA_DIR / "online_store_orders.csv"
    rows = [
        ["order_id", "customer_name", "customer_email", "order_date", "ship_date", "product_category", "unit_price", "quantity", "order_status"],
        ["ORD-1001", "Alice Johnson", "alice.j@example.com", "2026-01-10", "2026-01-12", "Electronics", "199.99", "1", "Delivered"],
        ["ORD-1002", "Bob Smith ", "bob.smith@company.org", "2026-01-11", "2026-01-13", "Home & Kitchen", "49.50", "2", "delivered"],
        ["ORD-1003", "Charlie Davis", "invalid-email-address", "2026-01-12", "2026-01-15", "Electronics", "899.00", "1", "SHIPPED"],
        ["ORD-1004", "Diana Prince", "diana.p@justice.net", "2026-01-14", "2026-01-10", "Beauty", "29.99", "3", "Delivered"], # Temporal inversion!
        ["ORD-1005", "Evan Wright", "evan@wright.io", "2026-01-15", "2026-01-18", "Books", "-15.00", "1", "Delivered"], # Negative price!
        ["ORD-1002", "Bob Smith", "bob.smith@company.org", "2026-01-11", "2026-01-13", "Home & Kitchen", "49.50", "2", "Delivered"], # Duplicate order_id!
        ["ORD-1006", "Fiona Gallagher", "", "2026-01-16", "2026-01-19", "Apparel", "85.00", "2", "Processing"], # Missing email
        ["ORD-1007", "George Miller", "george@madmax.com", "2026-01-17", "2026-01-20", "Electronics", "125000.00", "1", "Delivered"], # Statistical Outlier price!
        ["ORD-1008", "Hannah Abbott", "hannah@hogwarts.edu", "2026/01/18", "2026-01-22", "Books", "19.99", "4", "  Delivered  "], # Untrimmed whitespace
        ["ORD-1009", "Ian Malcolm", "ian.m@chaos.com", "2026-01-19", "2026-01-23", "Electronics", "249.99", "1", "delivered"], # Casing inconsistency
        ["ORD-1010", "Julia Roberts", "julia@nottinghill.com", "2026-01-20", "2026-01-24", "Apparel", "", "1", "Delivered"], # Missing category
        ["ORD-1011", "Kevin Bacon", "kevin@sixdegrees.com", "2026-01-21", "2026-01-25", "Home & Kitchen", "35.00", "2", "Shipped"],
        ["ORD-1011", "Kevin Bacon", "kevin@sixdegrees.com", "2026-01-21", "2026-01-25", "Home & Kitchen", "35.00", "2", "Shipped"], # Exact duplicate row!
        ["ORD-1012", "Laura Croft", "lara@tomb.org", "invalid_date_str", "2026-01-26", "Electronics", "599.99", "1", "Shipped"], # Invalid date format
        ["ORD-1013", "Michael Scott", "michael@dundermifflin.com", "2026-01-23", "2026-01-27", "Office Supplies", "12.50", "10", "Delivered"],
        ["ORD-1014", "Nancy Drew", "nancy@mystery.net", "2026-01-24", "2026-01-28", "Books", "14.95", "1", "Delivered"],
        ["ORD-1015", "Oscar Martinez", "oscar@accounting.org", "2026-01-25", "2026-01-29", "Office Supplies", "45.00", "3", "Delivered"],
        ["ORD-1016", "Pam Beesly", "pam@dunder.com", "2026-01-26", "2026-01-30", "Office Supplies", "8.99", "5", "delivered"],
        ["ORD-1017", "Quinn Fabray", "quinn@mckinley.edu", "2026-01-27", "2026-01-31", "Apparel", "65.00", "1", "Shipped"]
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Created: {path}")

def create_employees_dataset():
    path = DATA_DIR / "employees.csv"
    rows = [
        ["emp_id", "full_name", "work_email", "department", "hire_date", "termination_date", "annual_salary", "performance_rating"],
        ["EMP-001", "Arthur Dent", "arthur.dent@galaxy.org", "Engineering", "2021-03-01", "", "95000", "Exceeds Expectations"],
        ["EMP-002", "Ford Prefect", "ford.prefect@guide.net", "Marketing", "2020-05-15", "", "82000", "Meets Expectations"],
        ["EMP-003", "Trillian Astra", "trillian@deepthought.com", "Engineering", "2019-01-10", "", "145000", "exceeds expectations"],
        ["EMP-004", "Tricia McMillan", "invalid_email", "Product", "2022-08-20", "", "110000", "Meets Expectations"],
        ["EMP-005", "Marvin Android", "marvin@paranoid.com", "Operations", "2023-01-01", "2022-01-01", "70000", "Needs Improvement"], # Temporal inversion!
        ["EMP-006", "Zaphod Beeblebrox", "president@galaxy.gov", "", "2018-11-05", "", "5500000", "Outstanding"], # Outlier salary & missing department
        ["EMP-007", "Slartibartfast", "coastlines@fjords.no", "Design", "2017-04-12", "", "120000", "Exceeds Expectations"],
        ["EMP-008", "Dirk Gently", "dirk@holistic.co.uk", "Legal", "2024-02-14", "", "-45000", "Meets Expectations"], # Negative salary
        ["EMP-002", "Ford Prefect", "ford.prefect@guide.net", "Marketing", "2020-05-15", "", "82000", "Meets Expectations"], # Duplicate ID
        ["EMP-009", "Agrajag", "agrajag@incarnations.net", "Research", "2023-07-01", "", "98000", "  Meets Expectations  "], # Whitespace
        ["EMP-010", "Fenchurch", "fenchurch@skies.org", "Support", "2022-10-10", "", "65000", "Meets Expectations"]
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Created: {path}")

def create_financial_transactions():
    path = DATA_DIR / "financial_transactions.csv"
    rows = [
        ["txn_id", "account_number", "txn_type", "amount", "currency", "txn_timestamp", "status"],
        ["TXN-8801", "ACCT-100234", "DEPOSIT", "1500.00", "USD", "2026-02-01 08:30:00", "COMPLETED"],
        ["TXN-8802", "ACCT-100235", "WITHDRAWAL", "200.00", "USD", "2026-02-01 09:15:00", "completed"],
        ["TXN-8803", "ACCT-100236", "TRANSFER", "-50.00", "USD", "2026-02-01 10:00:00", "COMPLETED"], # Negative amount
        ["TXN-8804", "ACCT-100237", "PAYMENT", "45.90", "USD", "invalid_timestamp", "PENDING"], # Invalid timestamp
        ["TXN-8805", "ACCT-100238", "DEPOSIT", "10000000.00", "USD", "2026-02-01 11:20:00", "COMPLETED"], # Outlier
        ["TXN-8801", "ACCT-100234", "DEPOSIT", "1500.00", "USD", "2026-02-01 08:30:00", "COMPLETED"], # Duplicate txn_id
        ["TXN-8806", "ACCT-100239", "WITHDRAWAL", "", "USD", "2026-02-01 12:45:00", "FAILED"], # Missing amount
        ["TXN-8807", "ACCT-100240", "TRANSFER", "320.00", "USD", "2026-02-01 13:00:00", "Completed"],
        ["TXN-8808", "ACCT-100241", "PAYMENT", "12.00", "USD", "2026-02-01 14:10:00", "  COMPLETED  "]
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Created: {path}")

def create_healthcare_patients():
    path = DATA_DIR / "healthcare_patients.csv"
    rows = [
        ["patient_id", "full_name", "age", "gender", "systolic_bp", "contact_phone", "diagnosis_code", "admission_date"],
        ["PAT-501", "Eleanor Vance", "45", "Female", "120", "+1-555-0192", "I10", "2026-01-05"],
        ["PAT-502", "Luke Sanderson", "-5", "Male", "135", "555-0193", "E11.9", "2026-01-06"], # Impossible age
        ["PAT-503", "Theodora Crain", "32", "female", "118", "not-a-phone-number", "J45.909", "2026-01-07"], # Invalid phone & casing
        ["PAT-504", "Hugh Crain", "250", "Male", "320", "+1-555-0195", "I25.10", "2026-01-08"], # Outlier age & BP
        ["PAT-505", "Nell Crain", "", "Female", "115", "+1-555-0196", "", "2026-01-09"], # Missing age & diagnosis
        ["PAT-506", "Steven Crain", "42", "Male", "128", "+1-555-0197", "K21.9", "2026-01-10"],
        ["PAT-501", "Eleanor Vance", "45", "Female", "120", "+1-555-0192", "I10", "2026-01-05"], # Duplicate patient ID
        ["PAT-507", "Shirley Crain", "39", "Female", "122", "+1-555-0198", "M54.5", "2026-01-11"]
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Created: {path}")

def create_inventory_stock():
    path = DATA_DIR / "inventory_stock.csv"
    rows = [
        ["sku_code", "item_name", "warehouse_zone", "units_in_stock", "reorder_point", "unit_cost", "unit_retail_price"],
        ["SKU-001", "Wireless Ergonomic Mouse", "Zone A", "150", "30", "12.50", "29.99"],
        ["SKU-002", "Mechanical Keyboard", "Zone B", "-10", "25", "45.00", "89.99"], # Negative stock
        ["SKU-003", "4K Ultra HD Monitor", "zone a", "45", "10", "180.00", "299.99"], # Casing inconsistency
        ["SKU-004", "USB-C Hub Multiport", "Zone C", "", "50", "15.00", "34.99"], # Missing units
        ["SKU-005", "Noise Cancelling Headphones", "Zone A", "80", "20", "65.00", "49.99"], # Cost > Price violation!
        ["SKU-006", "Desk Mat Extended", "Zone B", "300", "40", "5.00", "19.99"],
        ["SKU-001", "Wireless Ergonomic Mouse", "Zone A", "150", "30", "12.50", "29.99"] # Duplicate SKU
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Created: {path}")

if __name__ == "__main__":
    create_online_store_orders()
    create_employees_dataset()
    create_financial_transactions()
    create_healthcare_patients()
    create_inventory_stock()


import sqlite3
import random
import calendar
from datetime import date, timedelta

DB_NAME = "cleaning_service.db"
BATCH_TAG = "SAMPLE250"

first_names = [
    "James", "Maria", "John", "Angela", "Mark",
    "Sofia", "Carlo", "Andrea", "Joshua", "Nicole",
    "Miguel", "Patricia", "Daniel", "Ashley", "Kevin",
    "Jasmine", "Christian", "Grace", "Rafael", "Camille",
    "Paolo", "Bianca", "Gabriel", "Alyssa", "Nathan"
]

last_names = [
    "Santos", "Reyes", "Cruz", "Garcia", "Mendoza",
    "Bautista", "Ramos", "Flores", "Gonzales", "Aquino",
    "Castillo", "Rivera", "Torres", "Villanueva", "Fernandez",
    "Dela Cruz", "Navarro", "Lim", "Perez", "Mercado"
]

services = [
    "House Cleaning",
    "Deep Cleaning",
    "Office Cleaning",
    "Move-in Cleaning",
    "Move-out Cleaning"
]

utilities = [
    "Soap",
    "Disinfectant",
    "Floor Wax",
    "Mop",
    "Broom",
    "Dustpan",
    "Sponge",
    "Glass Cleaner",
    "Toilet Cleaner",
    "Bleach",
    "Gloves",
    "Trash Bags"
]

statuses = [
    "Pending",
    "In Progress",
    "Completed",
    "Cancelled"
]

random.seed(42)


def main():

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    try:
        # Check the expected tables exist.
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        required = {"customers", "schedules"}

        if not required.issubset(tables):
            raise RuntimeError(
                "Required tables are missing. Run main.py first."
            )

        # Track this batch so rerunning the script does not
        # add another 250 schedules.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sample_data_batches (
                batch_tag TEXT PRIMARY KEY,
                schedule_count INTEGER NOT NULL
            )
        """)

        cursor.execute(
            "SELECT schedule_count FROM sample_data_batches "
            "WHERE batch_tag = ?",
            (BATCH_TAG,)
        )

        if cursor.fetchone():
            print("Sample batch already exists. No data added.")
            print("Existing records were not changed.")
            return

        # Reuse existing customers where possible.
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]

        # Create additional sample customers if needed.
        existing_count = len(customer_ids)
        target_customers = 50

        for i in range(existing_count, target_customers):

            first = first_names[i % len(first_names)]
            last = last_names[(i // len(first_names)) % len(last_names)]
            name = f"{first} {last} Sample {i + 1}"

            phone = f"09{random.randint(100000000, 999999999)}"
            address = (
                f"Sample Address {i + 1}, "
                f"Cainta, Rizal"
            )

            cursor.execute("""
                INSERT INTO customers (name, phone, address)
                VALUES (?, ?, ?)
            """, (name, phone, address))

            customer_ids.append(cursor.lastrowid)

        if not customer_ids:
            raise RuntimeError("No customer records are available.")

        # Generate 250 schedules spread across several months.
        start_date = date.today() - timedelta(days=90)

        for i in range(250):

            customer_id = random.choice(customer_ids)

            service_day = start_date + timedelta(
                days=random.randint(0, 180)
            )

            service_date = service_day.strftime("%m/%d/%Y")

            hour = random.randint(7, 11)
            minute = random.choice([0, 15, 30, 45])
            period = random.choice(["AM", "PM"])

            service_time = f"{hour:02d}:{minute:02d} {period}"

            service_type = random.choice(services)

            selected_utilities = random.sample(
                utilities,
                k=random.randint(2, 5)
            )
            utilities_used = ", ".join(selected_utilities)

            status = random.choice(statuses)

            cursor.execute("""
                INSERT INTO schedules (
                    customer_id,
                    service_date,
                    service_time,
                    service_type,
                    utilities_used,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                service_date,
                service_time,
                service_type,
                utilities_used,
                status
            ))

        cursor.execute("""
            INSERT INTO sample_data_batches (batch_tag, schedule_count)
            VALUES (?, ?)
        """, (BATCH_TAG, 250))

        connection.commit()

        print("SUCCESS!")
        print("Added 250 sample cleaning schedules.")
        print(f"Customer records available: {len(customer_ids)}")
        print("Existing customer records were preserved.")
        print("You can now open the app and test Search and Dashboard.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()


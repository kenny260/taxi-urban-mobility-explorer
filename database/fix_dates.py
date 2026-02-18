import sqlite3

DB_FILE = "database/nyc_taxi.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("Checking invalid dates...")

cursor.execute("""
    SELECT COUNT(*)
    FROM trips
    WHERE tpep_pickup_datetime < '2019-01-01'
       OR tpep_pickup_datetime >= '2019-02-01';
""")

invalid_count = cursor.fetchone()[0]
print(f"Invalid date rows: {invalid_count:,}")

if invalid_count > 0:
    print("Deleting invalid rows...")
    cursor.execute("""
        DELETE FROM trips
        WHERE tpep_pickup_datetime < '2019-01-01'
           OR tpep_pickup_datetime >= '2019-02-01';
    """)
    conn.commit()
    print("Deletion complete.")

print("Checking new date range...")
cursor.execute("""
    SELECT MIN(tpep_pickup_datetime),
           MAX(tpep_pickup_datetime)
    FROM trips;
""")

date_range = cursor.fetchone()
print(f"New date range: {date_range[0]} to {date_range[1]}")

print("Running VACUUM...")
cursor.execute("VACUUM;")

conn.close()
print("Done.")


import sqlite3
import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "nyc_taxi.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")
ZONES_FILE = os.path.join(BASE_DIR, "..", "data", "raw", "taxi_zone_lookup.csv")
TRIPS_FILE = os.path.join(BASE_DIR, "..", "data", "processed", "yellow_tripdata_2019-01_cleaned.csv")
DUPLICATES_LOG = os.path.join(BASE_DIR, "..", "data", "cleaning_log_duplicates.csv")

BATCH_SIZE = 10000

def create_database():
    print("Creating database...")
    os.makedirs("database", exist_ok=True)
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing database: {DB_FILE}")
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    with open(SCHEMA_FILE, 'r') as f:
        conn.executescript(f.read())
    
    conn.commit()
    print("Database schema created successfully")
    return conn

def load_zones(conn):
    print("Loading zones...")
    cursor = conn.cursor()
    
    with open(ZONES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [(int(row['LocationID']), row['Borough'], row['Zone'], row['service_zone']) for row in reader]
    
    cursor.executemany(
        "INSERT INTO zones (LocationID, Borough, Zone, service_zone) VALUES (?, ?, ?, ?);",
        rows
    )
    conn.commit()
    
    cursor.execute("SELECT LocationID FROM zones")
    valid_ids = set(row[0] for row in cursor.fetchall())
    
    print(f"Loaded {len(rows)} zones")
    print(f"Valid LocationID range: {min(valid_ids)} to {max(valid_ids)}")
    
    return valid_ids

def load_rate_types(conn):
    print("Loading rate types...")
    cursor = conn.cursor()
    
    rate_types = [
        (1, 'Standard rate'),
        (2, 'JFK'),
        (3, 'Newark'),
        (4, 'Nassau or Westchester'),
        (5, 'Negotiated fare'),
        (6, 'Group ride')
    ]
    cursor.executemany(
        "INSERT INTO rate_types (RatecodeID, Description) VALUES (?, ?);",
        rate_types
    )
    conn.commit()
    
    cursor.execute("SELECT RatecodeID FROM rate_types")
    valid_rates = set(row[0] for row in cursor.fetchall())
    
    print(f"Loaded {len(rate_types)} rate types")
    return valid_rates

def is_valid_jan_2019(date_str):
    """Fast string-based validation for January 2019"""
    return '2019-01-01 00:00:00' <= date_str < '2019-02-01 00:00:00'

def load_trips(conn, valid_location_ids, valid_rate_codes):
    print("Loading trips...")

    total_inserted = 0
    total_skipped = 0
    batch = []
    skip_reasons = defaultdict(int)

    seen_trips = set()
    log_duplicates = []

    cursor = conn.cursor()

    with open(TRIPS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=1):
            try:
                pickup_dt = row['tpep_pickup_datetime']
                dropoff_dt = row['tpep_dropoff_datetime']

                if not is_valid_jan_2019(pickup_dt) or not is_valid_jan_2019(dropoff_dt) or dropoff_dt <= pickup_dt:
                    total_skipped += 1
                    skip_reasons["date"] += 1
                    continue

                pu_location = int(row['PULocationID'])
                do_location = int(row['DOLocationID'])
                if pu_location not in valid_location_ids or do_location not in valid_location_ids:
                    total_skipped += 1
                    skip_reasons["location"] += 1
                    continue

                rate_code = int(row.get('RatecodeID') or 1)
                if rate_code not in valid_rate_codes:
                    rate_code = 1
                    skip_reasons["ratecode"] += 1

                trip_key = (
                    row.get('VendorID'), pickup_dt, dropoff_dt,
                    pu_location, do_location,
                    row.get('passenger_count'), row.get('trip_distance'),
                    row.get('fare_amount')
                )

                if trip_key in seen_trips:
                    total_skipped += 1
                    skip_reasons["duplicate"] += 1
                    if len(log_duplicates) < 1000:
                        log_duplicates.append(row)
                    continue
                seen_trips.add(trip_key)

                batch.append((
                    int(row['VendorID']) if row.get('VendorID') else None,
                    pickup_dt,
                    dropoff_dt,
                    int(row['passenger_count']) if row.get('passenger_count') else None,
                    float(row['trip_distance']) if row.get('trip_distance') else None,
                    rate_code,
                    row.get('store_and_fwd_flag'),
                    pu_location,
                    do_location,
                    int(row['payment_type']) if row.get('payment_type') else None,
                    float(row['fare_amount']) if row.get('fare_amount') else None,
                    float(row['extra']) if row.get('extra') else None,
                    float(row['mta_tax']) if row.get('mta_tax') else None,
                    float(row['tip_amount']) if row.get('tip_amount') else None,
                    float(row['tolls_amount']) if row.get('tolls_amount') else None,
                    float(row['improvement_surcharge']) if row.get('improvement_surcharge') else None,
                    float(row['total_amount']) if row.get('total_amount') else None,
                    float(row['congestion_surcharge']) if row.get('congestion_surcharge') else None,
                    float(row['trip_speed_mph']) if row.get('trip_speed_mph') else None,
                    float(row['cost_per_mile']) if row.get('cost_per_mile') else None,
                    row.get('time_category'),
                    float(row['tip_percentage']) if row.get('tip_percentage') else None,
                    float(row['efficiency_score']) if row.get('efficiency_score') else None
                ))

                if len(batch) >= BATCH_SIZE:
                    cursor.executemany("""
                        INSERT INTO trips (
                            VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                            passenger_count, trip_distance, RatecodeID, store_and_fwd_flag,
                            PULocationID, DOLocationID, payment_type, fare_amount, extra,
                            mta_tax, tip_amount, tolls_amount, improvement_surcharge,
                            total_amount, congestion_surcharge, trip_speed_mph, cost_per_mile,
                            time_category, tip_percentage, efficiency_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, batch)
                    conn.commit()
                    total_inserted += len(batch)
                    print(f"Loaded {total_inserted:,} trips (skipped {total_skipped:,})...")
                    batch = []

            except Exception as e:
                total_skipped += 1
                skip_reasons["other"] += 1
                if skip_reasons["other"] <= 5:
                    print(f"Row {row_num} error: {e}")

    if batch:
        cursor.executemany("""
            INSERT INTO trips (
                VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                passenger_count, trip_distance, RatecodeID, store_and_fwd_flag,
                PULocationID, DOLocationID, payment_type, fare_amount, extra,
                mta_tax, tip_amount, tolls_amount, improvement_surcharge,
                total_amount, congestion_surcharge, trip_speed_mph, cost_per_mile,
                time_category, tip_percentage, efficiency_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, batch)
        conn.commit()
        total_inserted += len(batch)

    if log_duplicates:
        print(f"\nSaving {len(log_duplicates)} duplicate samples to log...")
        with open(DUPLICATES_LOG, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=log_duplicates[0].keys())
            writer.writeheader()
            writer.writerows(log_duplicates)

    print(f"\nTotal trips loaded: {total_inserted:,}")
    print(f"Total trips skipped: {total_skipped:,}")
    print("\nSkip reasons:")
    for reason, count in sorted(skip_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason}: {count:,}")

def verify_data(conn):
    print("\nVerifying data...")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM zones")
    print(f"Zones: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(*) FROM rate_types")
    print(f"Rate types: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(*) FROM trips")
    print(f"Trips: {cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT MIN(tpep_pickup_datetime), MAX(tpep_pickup_datetime) FROM trips")
    date_range = cursor.fetchone()
    if date_range[0]:
        print(f"Date range: {date_range[0]} to {date_range[1]}")

def main():
    print("="*70)
    print("NYC TAXI DATABASE SETUP")
    print("="*70 + "\n")
    
    conn = create_database()
    valid_location_ids = load_zones(conn)
    valid_rate_codes = load_rate_types(conn)
    load_trips(conn, valid_location_ids, valid_rate_codes)
    verify_data(conn)
    
    conn.close()
    
    print("\n" + "="*70)
    print("DATABASE SETUP COMPLETE")
    print(f"Database location: {DB_FILE}")
    if os.path.exists(DUPLICATES_LOG):
        print(f"Duplicates log: {DUPLICATES_LOG}")
    print("="*70)

if __name__ == "__main__":
    main()

import csv

# CSV DATA LOADING UTILITIES
# These functions abstract reading CSV files into a list of dictionaries.
# This keeps I/O logic separate from analysis and ensures reusability.

def load_csv(file_path):
    """
    Load a CSV file into a list of dictionaries.

    Each row is represented as a dict with keys corresponding
    to the CSV headers.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        list[dict]: List of records.
    """
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def load_trip_data():
    """
    Load NYC taxi trip data for January 2019.

    Returns:
        list[dict]: Trip records.
    """
    return load_csv("data/raw/yellow_tripdata_2019-01.csv")


def load_zone_lookup():
    """
    Load NYC taxi zone lookup table.

    Returns:
        list[dict]: Zone metadata records.
    """
    return load_csv("data/raw/taxi_zone_lookup.csv")


# BASIC DATA PROFILING
# This function computes null counts and total counts per column
# for the first N rows (default 1000). This is a lightweight
# exploratory step to check data completeness.

def generate_basic_profile(records, num_rows=1000):
    """
    Generate a basic null count profile for each column.

    Args:
        records (list[dict]): List of records to profile.
        num_rows (int): Number of rows to sample for the profile.

    Returns:
        dict: Column-wise profile with 'null_count' and 'total_count'.
    """
    profile = {}
    sample = records[:num_rows]  # Limit profiling to first N rows for speed

    for row in sample:
        for key, value in row.items():
            if key not in profile:
                profile[key] = {"null_count": 0, "total_count": 0}
            profile[key]["total_count"] += 1
            if value == "" or value is None:
                profile[key]["null_count"] += 1

    return profile

# SCRIPT EXECUTION
# Demonstrates how to load and inspect the datasets.
# Prints counts and a basic null profile for the trips dataset.

if __name__ == "__main__":
    # Load raw datasets
    trips = load_trip_data()
    zones = load_zone_lookup()

    # Output basic information
    print("Trips loaded:", len(trips))
    print("Zones loaded:", len(zones))

    # Generate null profile for first 1000 trip records
    print("\nSample trip profile (first 1000 rows):")
    profile = generate_basic_profile(trips)
    for col, stats in profile.items():
        print(f"{col}: nulls={stats['null_count']}, total={stats['total_count']}")


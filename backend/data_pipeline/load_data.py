import csv

def load_csv(file_path):
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def load_trip_data():
    return load_csv("data/raw/yellow_tripdata_2019-01.csv")

def load_zone_lookup():
    return load_csv("data/raw/taxi_zone_lookup.csv")

def generate_basic_profile(records, num_rows=1000):
    profile = {}
    sample = records[:num_rows]
    for row in sample:
        for key, value in row.items():
            if key not in profile:
                profile[key] = {"null_count": 0, "total_count": 0}
            profile[key]["total_count"] += 1
            if value == "" or value is None:
                profile[key]["null_count"] += 1
    return profile

if __name__ == "__main__":
    trips = load_trip_data()
    zones = load_zone_lookup()
    print("Trips loaded:", len(trips))
    print("Zones loaded:", len(zones))
    print("Sample trip profile:")
    print(generate_basic_profile(trips))

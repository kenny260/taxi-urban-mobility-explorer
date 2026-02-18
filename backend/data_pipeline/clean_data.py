import csv
import os
from datetime import datetime


# PATH CONFIGURATION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(BASE_DIR, "../../data/raw/yellow_tripdata_2019-01.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "../../data/processed/yellow_tripdata_2019-01_cleaned.csv")
LOG_FILE = os.path.join(BASE_DIR, "../../data/cleaning_log.txt")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            
# VALIDATION THRESHOLDS (Domain-informed)


THRESHOLDS = {
    "distance_min": 0.1,
    "distance_max": 100,
    "fare_min": 2.5,
    "fare_max": 500,
    "passengers_min": 1,
    "passengers_max": 6,
    "duration_min": 1,
    "duration_max": 480,
    "speed_max": 100,
    "tip_ratio_min": -0.1,
    "tip_ratio_max": 2.0,
}


# VALIDATION FUNCTIONS

def has_missing_critical_fields(row):
    required = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "PULocationID",
        "DOLocationID",
    ]

    for field in required:
        if not row.get(field):
            return True
    return False


def validate_trip(row):
    try:
        distance = float(row["trip_distance"])
        fare = float(row["fare_amount"])
        passengers = int(row["passenger_count"])
        tip = float(row.get("tip_amount", 0))
        total = float(row.get("total_amount", 0))

        pickup = datetime.strptime(row["tpep_pickup_datetime"], "%Y-%m-%d %H:%M:%S")
        dropoff = datetime.strptime(row["tpep_dropoff_datetime"], "%Y-%m-%d %H:%M:%S")

        duration = (dropoff - pickup).total_seconds() / 60

        if dropoff <= pickup:
            return False, "temporal"

        if not (THRESHOLDS["distance_min"] < distance <= THRESHOLDS["distance_max"]):
            return False, "distance"

        if not (THRESHOLDS["fare_min"] <= fare <= THRESHOLDS["fare_max"]):
            return False, "fare"

        if not (THRESHOLDS["passengers_min"] <= passengers <= THRESHOLDS["passengers_max"]):
            return False, "passengers"

        if not (THRESHOLDS["duration_min"] <= duration <= THRESHOLDS["duration_max"]):
            return False, "duration"

        speed = (distance / duration) * 60
        if speed > THRESHOLDS["speed_max"]:
            return False, "speed"

        warnings = 0

        if fare > 0:
            tip_ratio = tip / fare
            if not (THRESHOLDS["tip_ratio_min"] <= tip_ratio <= THRESHOLDS["tip_ratio_max"]):
                warnings += 1

        if abs(total - fare - tip) > 5:
            warnings += 1

        return True, warnings

    except Exception:
        return False, "parsing"


# FEATURE ENGINEERING

def add_derived_features(row):
    pickup = datetime.strptime(row["tpep_pickup_datetime"], "%Y-%m-%d %H:%M:%S")
    dropoff = datetime.strptime(row["tpep_dropoff_datetime"], "%Y-%m-%d %H:%M:%S")

    distance = float(row["trip_distance"])
    fare = float(row["fare_amount"])
    tip = float(row.get("tip_amount", 0))

    duration_minutes = (dropoff - pickup).total_seconds() / 60

    row["trip_speed_mph"] = round((distance / duration_minutes) * 60, 2) if duration_minutes > 0 else 0
    row["cost_per_mile"] = round(fare / distance, 2) if distance > 0 else 0

    hour = pickup.hour
    if 6 <= hour < 10:
        row["time_category"] = "morning_rush"
    elif 10 <= hour < 16:
        row["time_category"] = "midday"
    elif 16 <= hour < 20:
        row["time_category"] = "evening_rush"
    elif 20 <= hour < 24:
        row["time_category"] = "night"
    else:
        row["time_category"] = "late_night"

    row["tip_percentage"] = round((tip / fare) * 100, 2) if fare > 0 else 0

    if distance > 0 and duration_minutes > 0 and fare > 0:
        speed_score = min(row["trip_speed_mph"] / 30, 1) * 40
        cost_score = max(0, 1 - (row["cost_per_mile"] / 10)) * 30
        tip_score = min(row["tip_percentage"] / 20, 1) * 30
        row["efficiency_score"] = round(speed_score + cost_score + tip_score, 2)
    else:
        row["efficiency_score"] = 0

    return row


# MAIN PIPELINE

def clean_data():

    stats = {
        "total": 0,
        "kept": 0,
        "removed": 0,
        "warnings": 0,
        "distance": 0,
        "fare": 0,
        "passengers": 0,
        "duration": 0,
        "speed": 0,
        "temporal": 0,
        "parsing": 0,
        "missing": 0,
    }

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile, \
         open(LOG_FILE, "w", encoding="utf-8") as logfile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + [
            "trip_speed_mph",
            "cost_per_mile",
            "time_category",
            "tip_percentage",
            "efficiency_score",
        ]

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            stats["total"] += 1

            if has_missing_critical_fields(row):
                stats["removed"] += 1
                stats["missing"] += 1
                continue

            valid, result = validate_trip(row)

            if valid:
                row = add_derived_features(row)
                writer.writerow(row)
                stats["kept"] += 1
                stats["warnings"] += result
            else:
                stats["removed"] += 1
                stats[result] += 1

        write_log(logfile, stats)


def write_log(logfile, stats):

    logfile.write("NYC Taxi Data Cleaning Report\n")
    logfile.write("-----------\n\n")
    logfile.write(f"Generated: {datetime.now()}\n\n")

    logfile.write("Summary\n")
    logfile.write("-------\n")
    logfile.write(f"Total Records Processed: {stats['total']:,}\n")
    logfile.write(f"Records Kept: {stats['kept']:,}\n")
    logfile.write(f"Records Removed: {stats['removed']:,}\n")
    logfile.write(f"Warnings Issued: {stats['warnings']:,}\n\n")

    logfile.write("Removal Breakdown\n")
    logfile.write("-----------------\n")

    for key in ["missing", "distance", "fare", "passengers", "duration", "speed", "temporal", "parsing"]:
        logfile.write(f"{key.title()}: {stats[key]:,}\n")

    logfile.write("\nDerived Features Added\n")
    logfile.write("----------------------\n")
    logfile.write("trip_speed_mph\n")
    logfile.write("cost_per_mile\n")
    logfile.write("time_category\n")
    logfile.write("tip_percentage\n")
    logfile.write("efficiency_score\n")


if __name__ == "__main__":
    clean_data()


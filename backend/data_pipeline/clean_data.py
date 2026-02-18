import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/data_pipeline

INPUT_FILE = os.path.join(BASE_DIR, '../../data/raw/yellow_tripdata_2019-01.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, '../../data/processed/yellow_tripdata_2019-01_cleaned.csv')
LOG_FILE = os.path.join(BASE_DIR, '../../data/cleaning_log.txt')


# Create output directory if it doesn't exist
os.makedirs("data/processed", exist_ok=True)

# Validation thresholds
THRESHOLDS = {
    "min_distance": 0.1,
    "max_distance": 100,
    "min_fare": 2.5,
    "max_fare": 500,
    "min_passengers": 1,
    "max_passengers": 6,
    "min_duration": 1,
    "max_duration": 480,
    "max_speed": 100,
    "min_tip_ratio": -0.1,
    "max_tip_ratio": 2.0
}

def is_valid_trip(row, row_number):
    warnings = []
    
    try:
        distance = float(row.get('trip_distance', 0))
        fare = float(row.get('fare_amount', 0))
        passengers = int(row.get('passenger_count', 0))
        tip = float(row.get('tip_amount', 0))
        total = float(row.get('total_amount', 0))
        
        pickup_str = row.get('tpep_pickup_datetime', '')
        dropoff_str = row.get('tpep_dropoff_datetime', '')
        
        pickup = datetime.strptime(pickup_str, "%Y-%m-%d %H:%M:%S")
        dropoff = datetime.strptime(dropoff_str, "%Y-%m-%d %H:%M:%S")
        
        duration = (dropoff - pickup).total_seconds() / 60
        
        if distance <= THRESHOLDS["min_distance"]:
            return False, f"Distance too low: {distance:.2f} miles", warnings
        if distance > THRESHOLDS["max_distance"]:
            return False, f"Distance too high: {distance:.2f} miles", warnings
        
        if fare < THRESHOLDS["min_fare"]:
            return False, f"Fare too low: ${fare:.2f}", warnings
        if fare > THRESHOLDS["max_fare"]:
            return False, f"Fare too high: ${fare:.2f}", warnings
        
        if passengers < THRESHOLDS["min_passengers"]:
            return False, f"Invalid passenger count: {passengers}", warnings
        if passengers > THRESHOLDS["max_passengers"]:
            return False, f"Too many passengers: {passengers}", warnings
        
        if duration < THRESHOLDS["min_duration"]:
            return False, f"Duration too short: {duration:.2f} min", warnings
        if duration > THRESHOLDS["max_duration"]:
            return False, f"Duration too long: {duration:.2f} min", warnings
        
        if dropoff <= pickup:
            return False, "Dropoff time before/equal to pickup time", warnings
        
        speed = (distance / duration) * 60
        if speed > THRESHOLDS["max_speed"]:
            return False, f"Unrealistic speed: {speed:.2f} mph", warnings
        
        if fare > 0:
            tip_ratio = tip / fare
            if tip_ratio < THRESHOLDS["min_tip_ratio"]:
                warnings.append(f"Unusual tip: ${tip:.2f} (ratio: {tip_ratio:.2%})")
            elif tip_ratio > THRESHOLDS["max_tip_ratio"]:
                warnings.append(f"Very high tip: ${tip:.2f} (ratio: {tip_ratio:.2%})")
        
        if abs(total - fare - tip) > 5:
            warnings.append(f"Fare mismatch: fare=${fare:.2f}, tip=${tip:.2f}, total=${total:.2f}")
        
        if speed < 3:
            warnings.append(f"Very slow trip: {speed:.2f} mph")
        
        pu_loc = row.get('PULocationID', '')
        do_loc = row.get('DOLocationID', '')
        if pu_loc == do_loc and distance > 0.5:
            warnings.append(f"Same pickup/dropoff location with distance {distance:.2f} mi")
        
        return True, "", warnings
        
    except ValueError as e:
        return False, f"Parse error: {str(e)}", warnings
    except Exception as e:
        return False, f"Validation error: {str(e)}", warnings

def is_missing_critical_field(row):
    critical_fields = [
        'tpep_pickup_datetime', 
        'tpep_dropoff_datetime',
        'trip_distance',
        'fare_amount',
        'PULocationID',
        'DOLocationID'
    ]
    
    for field in critical_fields:
        if field not in row or row[field] == '' or row[field] is None:
            return True, field
    
    return False, None

def add_derived_features(row):
    try:
        pickup = datetime.strptime(row['tpep_pickup_datetime'], "%Y-%m-%d %H:%M:%S")
        dropoff = datetime.strptime(row['tpep_dropoff_datetime'], "%Y-%m-%d %H:%M:%S")
        distance = float(row['trip_distance'])
        fare = float(row['fare_amount'])
        tip = float(row.get('tip_amount', 0))
        
        duration_minutes = (dropoff - pickup).total_seconds() / 60
        
        if duration_minutes > 0:
            row['trip_speed_mph'] = round((distance / duration_minutes) * 60, 2)
        else:
            row['trip_speed_mph'] = 0
        
        if distance > 0:
            row['cost_per_mile'] = round(fare / distance, 2)
        else:
            row['cost_per_mile'] = 0
        
        hour = pickup.hour
        if 6 <= hour < 10:
            row['time_category'] = 'morning_rush'
        elif 10 <= hour < 16:
            row['time_category'] = 'midday'
        elif 16 <= hour < 20:
            row['time_category'] = 'evening_rush'
        elif 20 <= hour < 24:
            row['time_category'] = 'night'
        else:
            row['time_category'] = 'late_night'
        
        if fare > 0:
            row['tip_percentage'] = round((tip / fare) * 100, 2)
        else:
            row['tip_percentage'] = 0
        
        if distance > 0 and duration_minutes > 0 and fare > 0:
            speed_score = min(float(row['trip_speed_mph']) / 30, 1) * 40
            cost_score = max(0, 1 - (float(row['cost_per_mile']) / 10)) * 30
            tip_score = min(float(row['tip_percentage']) / 20, 1) * 30
            row['efficiency_score'] = round(speed_score + cost_score + tip_score, 2)
        else:
            row['efficiency_score'] = 0
        
        return row
    except Exception as e:
        print(f"Warning: Could not add features - {str(e)}")
        return row

def clean_data():
    print("\n" + "="*70)
    print("STARTING DATA CLEANING PROCESS")
    print("="*70 + "\n")
    
    stats = {
        "total": 0,
        "removed": 0,
        "kept": 0,
        "missing_fields": 0,
        "invalid_distance": 0,
        "invalid_fare": 0,
        "invalid_passengers": 0,
        "invalid_duration": 0,
        "invalid_speed": 0,
        "invalid_temporal": 0,
        "other_errors": 0,
        "warnings": 0
    }
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as infile, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile, \
         open(LOG_FILE, 'w', encoding='utf-8') as log:
        
        reader = csv.DictReader(infile)
        
        new_fieldnames = list(reader.fieldnames) + [
            'trip_speed_mph',
            'cost_per_mile', 
            'time_category',
            'tip_percentage',
            'efficiency_score'
        ]
        
        writer = csv.DictWriter(outfile, fieldnames=new_fieldnames)
        writer.writeheader()
        
        log.write("="*70 + "\n")
        log.write("DATA CLEANING LOG\n")
        log.write(f"Input file: {INPUT_FILE}\n")
        log.write(f"Output file: {OUTPUT_FILE}\n")
        log.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("="*70 + "\n\n")
        log.write("VALIDATION THRESHOLDS:\n")
        for key, value in THRESHOLDS.items():
            log.write(f"  {key}: {value}\n")
        log.write("\n" + "="*70 + "\n\n")
        log.write("REMOVED RECORDS:\n\n")
        
        for row in reader:
            stats["total"] += 1
            
            if stats["total"] % 100000 == 0:
                print(f"Processed {stats['total']:,} rows...")
            
            has_missing, missing_field = is_missing_critical_field(row)
            if has_missing:
                stats["removed"] += 1
                stats["missing_fields"] += 1
                log.write(f"Row {stats['total']}: Missing critical field '{missing_field}'\n")
                continue
            
            valid, reason, warnings = is_valid_trip(row, stats["total"])
            
            if valid:
                row_with_features = add_derived_features(row)
                writer.writerow(row_with_features)
                stats["kept"] += 1
                
                if warnings:
                    stats["warnings"] += len(warnings)
                    for warning in warnings:
                        log.write(f"Row {stats['total']} WARNING: {warning}\n")
            else:
                stats["removed"] += 1
                log.write(f"Row {stats['total']}: REMOVED - {reason}\n")
                
                if "distance" in reason.lower():
                    stats["invalid_distance"] += 1
                elif "fare" in reason.lower():
                    stats["invalid_fare"] += 1
                elif "passenger" in reason.lower():
                    stats["invalid_passengers"] += 1
                elif "duration" in reason.lower():
                    stats["invalid_duration"] += 1
                elif "speed" in reason.lower():
                    stats["invalid_speed"] += 1
                elif "dropoff" in reason.lower() or "pickup" in reason.lower():
                    stats["invalid_temporal"] += 1
                else:
                    stats["other_errors"] += 1
        
        log.write("\n" + "="*70 + "\n")
        log.write("CLEANING SUMMARY\n")
        log.write("="*70 + "\n")
        log.write(f"Total records processed: {stats['total']:,}\n")
        log.write(f"Records kept: {stats['kept']:,} ({stats['kept']/stats['total']*100:.2f}%)\n")
        log.write(f"Records removed: {stats['removed']:,} ({stats['removed']/stats['total']*100:.2f}%)\n")
        log.write(f"Total warnings: {stats['warnings']:,}\n\n")
        log.write("REMOVAL BREAKDOWN:\n")
        log.write(f"  Missing critical fields: {stats['missing_fields']:,}\n")
        log.write(f"  Invalid distance: {stats['invalid_distance']:,}\n")
        log.write(f"  Invalid fare: {stats['invalid_fare']:,}\n")
        log.write(f"  Invalid passengers: {stats['invalid_passengers']:,}\n")
        log.write(f"  Invalid duration: {stats['invalid_duration']:,}\n")
        log.write(f"  Invalid speed: {stats['invalid_speed']:,}\n")
        log.write(f"  Invalid temporal logic: {stats['invalid_temporal']:,}\n")
        log.write(f"  Other errors: {stats['other_errors']:,}\n")
    
    print("\n" + "="*70)
    print("CLEANING COMPLETE")
    print("="*70)
    print(f"Total records processed: {stats['total']:,}")
    print(f"Records kept: {stats['kept']:,} ({stats['kept']/stats['total']*100:.2f}%)")
    print(f"Records removed: {stats['removed']:,} ({stats['removed']/stats['total']*100:.2f}%)")
    print(f"Warnings issued: {stats['warnings']:,}")
    print(f"\nCleaned data saved to: {OUTPUT_FILE}")
    print(f"Cleaning log saved to: {LOG_FILE}")
    print("="*70 + "\n")

if __name__ == "__main__":
    clean_data()

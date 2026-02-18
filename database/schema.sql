CREATE TABLE IF NOT EXISTS zones (
    LocationID INT PRIMARY KEY,
    Borough VARCHAR(50) NOT NULL,
    Zone VARCHAR(100) NOT NULL,
    service_zone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS rate_types (
    RatecodeID INT PRIMARY KEY,
    Description VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorID INT,
    tpep_pickup_datetime TEXT NOT NULL
        CHECK (
            tpep_pickup_datetime >= '2019-01-01 00:00:00'
            AND tpep_pickup_datetime < '2019-02-01 00:00:00'
        ),
    tpep_dropoff_datetime TEXT NOT NULL
        CHECK (
            tpep_dropoff_datetime >= '2019-01-01 00:00:00'
            AND tpep_dropoff_datetime < '2019-02-01 23:59:59'
        ),
    passenger_count INT CHECK (passenger_count >= 1 AND passenger_count <= 6),
    trip_distance FLOAT CHECK (trip_distance >= 0.1 AND trip_distance <= 100),
    RatecodeID INT,
    store_and_fwd_flag TEXT,
    PULocationID INT NOT NULL,
    DOLocationID INT NOT NULL,
    payment_type INT,
    fare_amount FLOAT CHECK (fare_amount >= 2.5 AND fare_amount <= 500),
    extra FLOAT,
    mta_tax FLOAT,
    tip_amount FLOAT,
    tolls_amount FLOAT,
    improvement_surcharge FLOAT,
    total_amount FLOAT,
    congestion_surcharge FLOAT,
    trip_speed_mph FLOAT CHECK (trip_speed_mph >= 0 AND trip_speed_mph <= 100),
    cost_per_mile FLOAT,
    time_category TEXT,
    tip_percentage FLOAT,
    efficiency_score FLOAT,
    CHECK (tpep_dropoff_datetime > tpep_pickup_datetime),
    FOREIGN KEY (PULocationID) REFERENCES zones(LocationID),
    FOREIGN KEY (DOLocationID) REFERENCES zones(LocationID),
    FOREIGN KEY (RatecodeID) REFERENCES rate_types(RatecodeID)
);

CREATE INDEX IF NOT EXISTS idx_trips_pickup_datetime ON trips(tpep_pickup_datetime);
CREATE INDEX IF NOT EXISTS idx_trips_dropoff_datetime ON trips(tpep_dropoff_datetime);
CREATE INDEX IF NOT EXISTS idx_trips_pickup_location ON trips(PULocationID);
CREATE INDEX IF NOT EXISTS idx_trips_dropoff_location ON trips(DOLocationID);
CREATE INDEX IF NOT EXISTS idx_trips_time_category ON trips(time_category);
CREATE INDEX IF NOT EXISTS idx_trips_fare ON trips(fare_amount);
CREATE INDEX IF NOT EXISTS idx_trips_distance ON trips(trip_distance);
CREATE INDEX IF NOT EXISTS idx_trips_pickup_borough ON trips(PULocationID, tpep_pickup_datetime);
CREATE INDEX IF NOT EXISTS idx_trips_time_fare ON trips(tpep_pickup_datetime, fare_amount);

CREATE VIEW IF NOT EXISTS v_trips_enriched AS
SELECT
    t.trip_id,
    t.VendorID,
    t.tpep_pickup_datetime,
    t.tpep_dropoff_datetime,
    DATE(t.tpep_pickup_datetime) AS pickup_date,
    CAST(STRFTIME('%H', t.tpep_pickup_datetime) AS INTEGER) AS pickup_hour,
    CAST(STRFTIME('%w', t.tpep_pickup_datetime) AS INTEGER) AS pickup_weekday,
    t.passenger_count,
    t.trip_distance,
    t.fare_amount,
    t.tip_amount,
    t.total_amount,
    t.trip_speed_mph,
    t.tip_percentage,
    t.time_category,
    pu.Borough AS pickup_borough,
    pu.Zone AS pickup_zone,
    do.Borough AS dropoff_borough,
    do.Zone AS dropoff_zone
FROM trips t
JOIN zones pu ON t.PULocationID = pu.LocationID
JOIN zones do ON t.DOLocationID = do.LocationID;

CREATE VIEW IF NOT EXISTS v_daily_revenue AS
SELECT
    DATE(tpep_pickup_datetime) AS pickup_date,
    COUNT(*) AS total_trips,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(total_amount), 2) AS avg_trip_value,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(trip_speed_mph), 2) AS avg_speed
FROM trips
GROUP BY pickup_date
ORDER BY pickup_date;

CREATE VIEW IF NOT EXISTS v_hourly_demand AS
SELECT
    CAST(STRFTIME('%H', tpep_pickup_datetime) AS INTEGER) AS pickup_hour,
    COUNT(*) AS trip_count,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(trip_speed_mph), 2) AS avg_speed,
    ROUND(AVG(tip_percentage), 2) AS avg_tip_pct
FROM trips
GROUP BY pickup_hour
ORDER BY pickup_hour;

CREATE VIEW IF NOT EXISTS v_borough_revenue AS
SELECT
    z.Borough,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount), 2) AS total_revenue,
    ROUND(AVG(t.total_amount), 2) AS avg_trip_value,
    ROUND(AVG(t.trip_distance), 2) AS avg_distance
FROM trips t
JOIN zones z ON t.PULocationID = z.LocationID
GROUP BY z.Borough
ORDER BY total_revenue DESC;

CREATE VIEW IF NOT EXISTS v_time_category_stats AS
SELECT
    time_category,
    COUNT(*) AS trip_count,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(trip_speed_mph), 2) AS avg_speed,
    ROUND(AVG(tip_percentage), 2) AS avg_tip_pct,
    ROUND(AVG(efficiency_score), 2) AS avg_efficiency
FROM trips
GROUP BY time_category
ORDER BY 
    CASE time_category
        WHEN 'late_night' THEN 1
        WHEN 'morning_rush' THEN 2
        WHEN 'midday' THEN 3
        WHEN 'evening_rush' THEN 4
        WHEN 'night' THEN 5
    END;

CREATE VIEW IF NOT EXISTS v_top_routes AS
SELECT
    pu.Borough || ' -> ' || do.Borough AS route,
    pu.Zone AS pickup_zone,
    do.Zone AS dropoff_zone,
    COUNT(*) AS trip_count,
    ROUND(AVG(t.fare_amount), 2) AS avg_fare,
    ROUND(AVG(t.trip_distance), 2) AS avg_distance,
    ROUND(AVG(t.trip_speed_mph), 2) AS avg_speed
FROM trips t
JOIN zones pu ON t.PULocationID = pu.LocationID
JOIN zones do ON t.DOLocationID = do.LocationID
GROUP BY pu.Borough, do.Borough, pu.Zone, do.Zone
HAVING trip_count > 100
ORDER BY trip_count DESC
LIMIT 50;

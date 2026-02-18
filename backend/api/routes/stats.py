from flask import Blueprint, jsonify
from database import get_connection, cached_query
from algorithm import quicksort_routes

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/summary")
def summary():
    conn = None
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT 
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount),2) AS avg_fare,
                ROUND(SUM(trip_distance),2) AS total_distance,
                ROUND(SUM(total_amount),2) AS total_revenue
            FROM trips
        """).fetchone()
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@stats_bp.route("/hourly-patterns")
def hourly_patterns():
    try:
        return jsonify(cached_query("SELECT * FROM v_hourly_demand"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@stats_bp.route("/fare-distribution")
def fare_distribution():
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT 
                ROUND(fare_amount,0) as fare_bucket,
                COUNT(*) as trip_count
            FROM trips
            GROUP BY fare_bucket
            ORDER BY fare_bucket
        """).fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@stats_bp.route("/top-routes")
def top_routes():
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT 
                pickup_zone,
                dropoff_zone,
                trip_count,
                avg_fare,
                avg_distance,
                avg_speed
            FROM v_top_routes
        """).fetchall()

        routes = [dict(row) for row in rows]

        sorted_routes = quicksort_routes(routes)

        return jsonify(sorted_routes[:10])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()

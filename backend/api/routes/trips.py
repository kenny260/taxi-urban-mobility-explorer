from flask import Blueprint, request, jsonify
from database import get_connection

trips_bp = Blueprint("trips", __name__)

@trips_bp.route("/", methods=["GET"])
def get_trips():
    conn = None
    try:
        conn = get_connection()
        query = "SELECT * FROM v_trips_enriched WHERE 1=1"
        params = []

        # Validate date range
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        if start_date and end_date:
            query += " AND pickup_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])

        # Pickup zone
        pickup_zone = request.args.get("pickup_zone")
        if pickup_zone:
            query += " AND pickup_zone = ?"
            params.append(pickup_zone)

        # Dropoff zone
        dropoff_zone = request.args.get("dropoff_zone")
        if dropoff_zone:
            query += " AND dropoff_zone = ?"
            params.append(dropoff_zone)

        # Fare range
        min_fare = request.args.get("min_fare")
        max_fare = request.args.get("max_fare")

        if min_fare:
            try:
                float(min_fare)
                query += " AND fare_amount >= ?"
                params.append(min_fare)
            except ValueError:
                return jsonify({"error": "min_fare must be numeric"}), 400

        if max_fare:
            try:
                float(max_fare)
                query += " AND fare_amount <= ?"
                params.append(max_fare)
            except ValueError:
                return jsonify({"error": "max_fare must be numeric"}), 400

        # Pagination
        try:
            limit = int(request.args.get("limit", 50))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            return jsonify({"error": "limit and offset must be integers"}), 400

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

        return jsonify([dict(row) for row in rows])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


@trips_bp.route("/<int:trip_id>", methods=["GET"])
def get_trip(trip_id):
    conn = None
    try:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM v_trips_enriched WHERE trip_id = ?",
            (trip_id,)
        ).fetchone()

        if not row:
            return jsonify({"error": "Trip not found"}), 404

        return jsonify(dict(row))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()

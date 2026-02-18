from flask import Blueprint, jsonify
from database import get_connection

zones_bp = Blueprint("zones", __name__)

@zones_bp.route("/", methods=["GET"])
def get_zones():
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM zones").fetchall()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

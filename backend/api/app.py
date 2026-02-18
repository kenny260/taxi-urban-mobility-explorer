from flask import Flask, jsonify
from flask_cors import CORS
from routes.trips import trips_bp
from routes.stats import stats_bp
from routes.zones import zones_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(trips_bp, url_prefix="/api/trips")
app.register_blueprint(stats_bp, url_prefix="/api/stats")
app.register_blueprint(zones_bp, url_prefix="/api/zones")

@app.route("/")
def home():
    return {"message": "NYC Taxi API Running"}

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad Request", "details": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource Not Found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Unexpected Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

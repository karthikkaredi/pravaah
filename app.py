from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://karthikkaredi_db_user:E9VX06dQaGdJxQxi@data.lgrdg1n.mongodb.net/?appName=data")
client = MongoClient(MONGO_URI)
db = client["esp_data"]
collection = db["values"]

@app.route('/')
def home():
    return jsonify({"message": "✅ Flask API is running locally on port 5000"})

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400
    
    data["timestamp"] = datetime.utcnow()
    try:
        result = collection.insert_one(data)
        return jsonify({"status": "success", "inserted_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/latest', methods=['GET'])
def latest_data():
    latest = collection.find_one(sort=[("timestamp", -1)])
    if latest:
        return jsonify({
            "steps": latest.get("steps", 0),
            "energy": latest.get("energy", 0),
            "power": latest.get("power", 0),
            "status": latest.get("status", "Unknown")
        })
    else:
        return jsonify({"message": "No data found"}), 404

if __name__ == "__main__":
    # Run Flask locally, accessible on LAN
    app.run(host="0.0.0.0", port=5000, debug=True)

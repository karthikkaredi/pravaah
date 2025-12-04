# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Allow dashboard & ESP32 from any origin

# === CONFIGURATION ===
MONGO_URI = "mongodb+srv://karedikarthik_db_user:Pravaah@esp32.iyujee8.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "esp"
COLLECTION_NAME = "values"

# Keep only recent logs (optional cleanup)
MAX_LOGS = 200
DELETE_OLDEST = 100

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    client.server_info()  # Test connection
    print("Connected to MongoDB Atlas")
except Exception as e:
    print("MongoDB connection failed:", e)

@app.route('/api/sensor-data', methods=['GET'])
def get_latest():
    try:
        doc = collection.find_one(sort=[("timestamp", -1)])
        total = doc["total_steps_count"] if doc else 0
        return jsonify({"total_steps": total}), 200
    except Exception as e:
        return jsonify({"total_steps": 0, "error": str(e)}), 500

@app.route('/api/sensor-data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json(silent=True) or {}
        left = int(data.get("left_tile", 0))
        right = int(data.get("right_tile", 0))

        if left not in (0,1) or right not in (0,1):
            return jsonify({"error": "Values must be 0 or 1"}), 400

        # Get previous state
        last = collection.find_one(sort=[("timestamp", -1)])
        prev_left = last["left_tile_state"] if last else 0
        prev_right = last["right_tile_state"] if last else 0
        prev_total = last["total_steps_count"] if last else 0

        # Detect rising edge → new step
        new_steps = 0
        if prev_left == 0 and left == 1:
            new_steps += 1
        if prev_right == 0 and right == 1:
            new_steps += 1

        total_steps = prev_total + new_steps

        # Auto cleanup old logs
        if collection.count_documents({}) > MAX_LOGS:
            oldest = list(collection.find().sort("timestamp", 1).limit(DELETE_OLDEST))
            ids = [doc["_id"] for doc in oldest]
            collection.delete_many({"_id": {"$in": ids}})

        # Save new record
        doc = {
            "left_tile_state": left,
            "right_tile_state": right,
            "total_steps_count": total_steps,
            "new_steps_added": new_steps,
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(doc)

        print(f"Steps: +{new_steps} | Total: {total_steps}")
        return jsonify({"total_steps": total_steps}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # CRITICAL: Listen on 0.0.0.0 so ESP32 & phones can reach it
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)

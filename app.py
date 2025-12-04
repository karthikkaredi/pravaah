from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

MONGO_URI = "mongodb+srv://karedikarthik_db_user:Pravaah@esp32.iyujee8.mongodb.net/?appName=esp32"
DB_NAME = 'esp'
COLLECTION_NAME = 'values'

# Updated limits:
MAX_LOGS = 100      # keep up to 100 documents
DELETE_COUNT = 50   # when limit reached, delete oldest 50

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("Connected successfully to MongoDB Atlas")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    pass


@app.route('/api/sensor-data', methods=['GET'])
def get_latest_sensor_data():
    try:
        latest_doc = collection.find_one(sort=[("timestamp", -1)])
        if not latest_doc:
            return jsonify({"total_steps": 0}), 200

        total_steps = latest_doc.get("total_steps_count", 0)
        return jsonify({"total_steps": total_steps}), 200

    except Exception as e:
        print(f"Error fetching latest sensor data: {e}")
        return jsonify({"error": "Failed to fetch latest sensor data"}), 500


@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()

    if not data or 'left_tile' not in data or 'right_tile' not in data:
        return jsonify({
            "error": "Invalid data format. Expected {'left_tile': 0 or 1, 'right_tile': 0 or 1}"
        }), 400

    try:
        curr_left = int(data['left_tile'])
        curr_right = int(data['right_tile'])
        if curr_left not in (0, 1) or curr_right not in (0, 1):
            return jsonify({"error": "Tile values must be 0 or 1."}), 400
    except ValueError:
        return jsonify({"error": "Tile values must be integers (0 or 1)."}), 400

    previous_total_steps = 0
    prev_left = 0
    prev_right = 0

    # Get last document to continue step count and tile states
    try:
        latest_doc_cursor = collection.find().sort("timestamp", -1).limit(1)
        latest_doc = next(latest_doc_cursor, None)
        if latest_doc:
            previous_total_steps = latest_doc.get('total_steps_count', 0)
            prev_left = latest_doc.get('left_tile_state', 0)
            prev_right = latest_doc.get('right_tile_state', 0)
    except Exception as e:
        print(f"Warning: Could not retrieve previous step count or states: {e}")

    # Count new steps from rising edges
    new_steps = 0
    if prev_left == 0 and curr_left == 1:
        new_steps += 1
    if prev_right == 0 and curr_right == 1:
        new_steps += 1

    new_total_steps = previous_total_steps + new_steps

    # Cleanup old logs when hitting limit
    try:
        current_log_count = collection.count_documents({})
        if current_log_count >= MAX_LOGS:
            oldest_logs = collection.find().sort("timestamp", 1).limit(DELETE_COUNT)
            oldest_ids = [doc['_id'] for doc in oldest_logs]

            if oldest_ids:
                delete_result = collection.delete_many({"_id": {"$in": oldest_ids}})
                print(f"Deleted {delete_result.deleted_count} oldest documents to maintain log size.")

    except Exception as e:
        print(f"Warning: Failed during log cleanup: {e}")

    sensor_document = {
        "left_tile_state": curr_left,
        "right_tile_state": curr_right,
        "total_steps_count": new_total_steps,
        "new_steps_added": new_steps,
        "timestamp": datetime.now()
    }

    try:
        result = collection.insert_one(sensor_document)
        print(
            f"Document inserted with _id: {result.inserted_id}. "
            f"New steps added: {new_steps}. Total: {new_total_steps}"
        )
        return jsonify({
            "message": "Sensor data stored successfully and log limits checked",
            "id": str(result.inserted_id),
            "total_steps": new_total_steps
        }), 201
    except Exception as e:
        print(f"Error storing data in MongoDB: {e}")
        return jsonify({"error": "Failed to store sensor data"}), 500


if __name__ == '__main__':
    app.run(host='10.198.243.1', port=3000, debug=True)

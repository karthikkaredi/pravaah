from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

MONGO_URI = "mongodb+srv://karedikarthik_db_user:Pravaah@esp32.iyujee8.mongodb.net/?appName=esp32"
DB_NAME = 'esp'
COLLECTION_NAME = 'values'

# We will use a unique identifier for the single document storing the state
# This allows us to find and update the same document every time.
DOCUMENT_ID_FILTER = {"_id": "sensor_state_tracker"}

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("Connected successfully to MongoDB Atlas")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    pass

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()

    if not data or 'left_tile' not in data or 'right_tile' not in data:
        return jsonify({"error": "Invalid data format. Expected {'left_tile': number, 'right_tile': number}"}), 400

    try:
        left_val = int(data['left_tile'])
        right_val = int(data['right_tile'])
    except ValueError:
        return jsonify({"error": "Tile values must be integers (1 or 0)."}), 400

    # Ensure inputs are 0 or 1
    if left_val not in (0, 1) or right_val not in (0, 1):
        return jsonify({"error": "Tile values must be 0 or 1."}), 400

    try:
        # 1. Fetch the current state document
        current_state = collection.find_one(DOCUMENT_ID_FILTER)

        # 2. Determine initial total steps if document doesn't exist
        total_steps = current_state.get('total_steps', 0) if current_state else 0
        
        # 3. Calculate new total steps (add current detections)
        steps_detected_now = left_val + right_val
        new_total_steps = total_steps + steps_detected_now

        # 4. Prepare the updated fields
        update_fields = {
            "$set": {
                "left_tile": left_val,
                "right_tile": right_val,
                "timestamp": datetime.now()
            },
            "$set": {
                "total_steps": new_total_steps
            }
        }
        
        # 5. Update the document (or create it if it doesn't exist - upsert=True)
        result = collection.update_one(
            DOCUMENT_ID_FILTER,
            {
                "$set": {
                    "left_tile": left_val,
                    "right_tile": right_val,
                    "timestamp": datetime.now(),
                    "total_steps": new_total_steps
                }
            },
            upsert=True
        )

        print(f"Total steps updated to: {new_total_steps}")
        return jsonify({
            "message": "State and step count updated successfully",
            "left_tile": left_val,
            "right_tile": right_val,
            "total_steps": new_total_steps
        }), 200

    except Exception as e:
        print(f"Error processing data in MongoDB: {e}")
        return jsonify({"error": "Failed to process sensor data"}), 500

if __name__ == '__main__':
    app.run(host='192.168.0.107', port=3000, debug=True)

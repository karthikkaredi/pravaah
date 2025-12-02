from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

MONGO_URI = "mongodb+srv://karedikarthik_db_user:Pravaah@esp32.iyujee8.mongodb.net/?appName=esp32"
DB_NAME = 'esp'
COLLECTION_NAME = 'values'

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

    # Checking for the new keys: 'left_tile' and 'right_tile'
    if not data or 'left_tile' not in data or 'right_tile' not in data:
        # Update the error message to reflect the new expected keys
        return jsonify({"error": "Invalid data format. Expected {'left_tile': number, 'right_tile': number}"}), 400

    try:
        # Accessing data using the new keys
        left_val = float(data['left_tile'])
        right_val = float(data['right_tile'])
    except ValueError:
        return jsonify({"error": "Sensor values must be numbers."}), 400

    # 1. DELETE ALL EXISTING DATA
    try:
        delete_result = collection.delete_many({})
        print(f"Deleted {delete_result.deleted_count} previous documents.")
    except Exception as e:
        print(f"Warning: Failed to delete previous documents: {e}") 

    # 2. PREPARE NEW DOCUMENT
    sensor_document = {
        # Using the new keys for the database fields for consistency
        "left_tile_proximity": left_val,
        "right_tile_proximity": right_val,
        "timestamp": datetime.now()
    }

    # 3. INSERT NEW DOCUMENT
    try:
        result = collection.insert_one(sensor_document)
        print(f"Document inserted with _id: {result.inserted_id}")
        return jsonify({
            "message": "Current sensor data stored successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        print(f"Error storing data in MongoDB: {e}")
        return jsonify({"error": "Failed to store sensor data"}), 500

if __name__ == '__main__':
    app.run(host='192.168.0.107', port=3000, debug=True)
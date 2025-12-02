from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

MONGO_URI = "mongodb+srv://karedikarthik_db_user:Pravaah@esp32.iyujee8.mongodb.net/?appName=esp32"
DB_NAME = 'esp'
COLLECTION_NAME = 'values'

MAX_LOGS = 20
DELETE_COUNT = 10

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

    if not data or 'left_tile' not in data or 'right_tile' not in data or 'total_steps_count' not in data:
        return jsonify({"error": "Invalid data format. Expected {'left_tile': number, 'right_tile': number, 'total_steps_count': number}"}), 400

    try:
        left_val = float(data['left_tile'])
        right_val = float(data['right_tile'])
        total_steps = int(data['total_steps_count'])
    except ValueError:
        return jsonify({"error": "Sensor values and step count must be numbers."}), 400

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
        "left_tile_proximity": left_val,
        "right_tile_proximity": right_val,
        "total_steps_count": total_steps,
        "timestamp": datetime.now()
    }

    try:
        result = collection.insert_one(sensor_document)
        print(f"Document inserted with _id: {result.inserted_id}")
        return jsonify({
            "message": "Sensor data stored successfully and log limits checked",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        print(f"Error storing data in MongoDB: {e}")
        return jsonify({"error": "Failed to store sensor data"}), 500

if __name__ == '__main__':
    app.run(host='192.168.0.107', port=3000, debug=True)

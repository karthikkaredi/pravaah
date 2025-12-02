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
    if not data or 'left' not in data or 'right' not in data:
        return jsonify({"error": "Invalid data format. Expected {'left': number, 'right': number}"}), 400
    try:
        left_val = float(data['left'])
        right_val = float(data['right'])
    except ValueError:
        return jsonify({"error": "Sensor values must be numbers."}), 400
    sensor_document = {
        "left_proximity": left_val,
        "right_proximity": right_val,
        "timestamp": datetime.now()
    }
    try:
        result = collection.insert_one(sensor_document)
        print(f"Document inserted with _id: {result.inserted_id}")
        return jsonify({
            "message": "Sensor data stored successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        print(f"Error storing data in MongoDB: {e}")
        return jsonify({"error": "Failed to store sensor data"}), 500

if __name__ == '__main__':
    app.run(host='192.168.0.107', port=3000, debug=True)
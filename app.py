from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import sys

app = Flask(__name__)
CORS(app) 

MONGO_URI = "mongodb+srv://karthikkaredi_db_user:JGXzcXrRFRRauPG8@esp.xxsagkg.mongodb.net/esp_data?appName=esp"
DB_NAME = "esp_data"         
COLLECTION_NAME = "values"   

MAX_LOGS = 50    
DELETE_OLDEST = 25 

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    client.server_info() 
except Exception as e:
    sys.exit(1) 

@app.route('/api/sensor-data', methods=['GET'])
def get_latest():
    try:
        doc = collection.find_one(sort=[("timestamp", -1)])
        total_steps = doc.get("total_steps_count", 0) if doc else 0
        
        return jsonify({"total_steps": total_steps}), 200
        
    except Exception as e:
        return jsonify({"total_steps": 0, "error": str(e)}), 500

@app.route('/api/sensor-data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json(silent=True) or {}
        left = int(data.get("left_tile", 0))
        right = int(data.get("right_tile", 0))

        if left not in (0, 1) or right not in (0, 1):
            return jsonify({"error": "Tile values must be 0 or 1"}), 400

        new_steps = left + right 

        last = collection.find_one(sort=[("timestamp", -1)])
        prev_total = last.get("total_steps_count", 0) if last else 0

        total_steps = prev_total + new_steps

        if collection.count_documents({}) > MAX_LOGS:
            oldest = list(collection.find().sort("timestamp", 1).limit(DELETE_OLDEST))
            ids = [doc["_id"] for doc in oldest]
            collection.delete_many({"_id": {"$in": ids}})

        doc = {
            "left_tile": left,      
            "right_tile": right,      
            "total_steps_count": total_steps,
            "new_steps_added": new_steps,
            "timestamp": datetime.utcnow()
        }
        collection.insert_one(doc)

        return jsonify({"total_steps": total_steps}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)

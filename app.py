from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import sys

app = Flask(__name__)
CORS(app)

# ---- CONFIG ----
MONGO_URI = (
    "mongodb+srv://karthikkaredi_db_user:RVFM0Jc635YbvdvA"
    "@cluster0.skyzscl.mongodb.net/?appName=Cluster0"
)

DB_NAME = "values"      # database name
COLLECTION_NAME = "esp" # collection name

MAX_LOGS = 50
DELETE_OLDEST = 25

print("🚀 Starting app.py...")

# ---- MONGO CONNECT ----
try:
    print("🔌 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    # Force connection test
    client.server_info()
    print(f"✅ Connected to MongoDB (DB='{DB_NAME}', Collection='{COLLECTION_NAME}')")
except Exception as e:
    print("❌ MongoDB connection error:", e)
    sys.exit(1)


# ---- GET: latest total steps ----
@app.route('/api/sensor-data', methods=['GET'])
def get_latest():
    try:
        # Get the most recent document by timestamp
        doc = collection.find_one(sort=[("timestamp", -1)])
        total_steps = doc.get("total_steps_count", 0) if doc else 0

        return jsonify({"total_steps": total_steps}), 200

    except Exception as e:
        print("❌ Error in GET /api/sensor-data:", e)
        return jsonify({"total_steps": 0, "error": str(e)}), 500


# ---- POST: receive left/right, update total ----
@app.route('/api/sensor-data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json(silent=True) or {}

        # Expecting: { "left_tile": 0/1, "right_tile": 0/1 }
        left = int(data.get("left_tile", 0))
        right = int(data.get("right_tile", 0))

        if left not in (0, 1) or right not in (0, 1):
            return jsonify({"error": "Tile values must be 0 or 1"}), 400

        # New steps in this reading
        new_steps = left + right

        # Get previous total from latest document
        last = collection.find_one(sort=[("timestamp", -1)])
        prev_total = last.get("total_steps_count", 0) if last else 0

        total_steps = prev_total + new_steps

        # Log rotation: keep only recent docs
        if collection.count_documents({}) > MAX_LOGS:
            oldest = list(collection.find().sort("timestamp", 1).limit(DELETE_OLDEST))
            ids = [doc["_id"] for doc in oldest]
            collection.delete_many({"_id": {"$in": ids}})

        # Insert new document
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
        print("❌ Error in POST /api/sensor-data:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🌐 Running Flask on 0.0.0.0:3000 ...")
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)

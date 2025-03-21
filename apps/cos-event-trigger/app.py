#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Equivalent to EventStats in Go
class EventStats:
    def __init__(self):
        self.by_bucket = {}
        self.by_type = {}
        self.by_object = {}
    
    def to_dict(self):
        return {
            "by_bucket": self.by_bucket,
            "by_type": self.by_type,
            "by_object": self.by_object
        }

# Global stats object
stats = EventStats()

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(stats.to_dict())

@app.route('/', methods=['POST'])
def handle_event():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = request.data.decode('utf-8')
    
    # Parse the event data
    event = json.loads(body)
    
    # Update stats
    bucket = event.get('bucket', 'unknown')
    operation = event.get('operation', 'unknown')
    key = event.get('key', 'unknown')
    
    stats.by_bucket[bucket] = stats.by_bucket.get(bucket, 0) + 1
    stats.by_type[operation] = stats.by_type.get(operation, 0) + 1
    stats.by_object[key] = stats.by_object.get(key, 0) + 1
    
    print(f"{current_time} - Received:")
    print(f"\nBody: {body}")
    
    return "OK"

if __name__ == '__main__':
    print("Listening on port 8080")
    app.run(host='0.0.0.0', port=8080)
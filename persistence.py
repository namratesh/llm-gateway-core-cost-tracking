# persistence.py
import json
import os
from datetime import datetime

LOG_FILE = os.getenv("LOG_FILE", "request_logs.jsonl")

def append_log(log_entry: dict):
    """
    Appends a dictionary as a JSON line to the log file.
    """
    # Add timestamp if missing
    if "timestamp" not in log_entry:
        log_entry["timestamp"] = datetime.utcnow().isoformat()
        
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"FAILED TO WRITE LOG: {e}")
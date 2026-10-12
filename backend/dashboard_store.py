import json
import os
import uuid

# Saved dashboards ko store karne ke liye folder
DATA_DIR = "saved_dashboards"
os.makedirs(DATA_DIR, exist_ok=True)

def save_dashboard(state_data, dashboard_name):
    """Dashboard state ko JSON file mein save karta hai aur unique ID return karta hai"""
    clean_name = "".join([c if c.isalnum() else "-" for c in dashboard_name.lower()])
    unique_id = f"{clean_name}-{str(uuid.uuid4())[:8]}"
    file_path = os.path.join(DATA_DIR, f"{unique_id}.json")
    
    with open(file_path, "w") as f:
        json.dump(state_data, f)
        
    return unique_id

def load_dashboard(dashboard_id):
    """Unique ID ke base par saved dashboard state load karta hai"""
    file_path = os.path.join(DATA_DIR, f"{dashboard_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None
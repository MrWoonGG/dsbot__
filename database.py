import json
import os

DB_FILE = 'db.json'

def new_db():
    save_db({
        'channel_id': 0,
        'admin_role_id': 0,
        'workers_role_id': 0,
        "orders_counter": 0,
        'orders': {}
    })

def load_db():
    if not os.path.exists(DB_FILE):
        new_db()

    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.decoder.JSONDecodeError, OSError):
        new_db()
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

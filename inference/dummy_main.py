import random
import requests
from datetime import datetime
import psycopg2

# Connect to Postgres to fetch products
conn = psycopg2.connect(
    dbname="birmas",
    user="birmas_user",
    password="B1rm4sC4m3r4",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Pull all products
cur.execute("SELECT product_brand, product_name FROM product;")
products = cur.fetchall()
conn.close()

API_URL = "http://127.0.0.1:8000/api/events"

def post_event(event):
    r = requests.post(API_URL, json=event)
    print("POST status:", r.status_code)
    print("Response:", r.json())

def get_events(camera_id):
    r = requests.get(API_URL, params={"camera_id": camera_id})
    print("GET status:", r.status_code)
    print("Events for", camera_id, ":", r.json())

if __name__ == "__main__":
    # Pick a random product
    brand, name = random.choice(products)

    # Build dummy event
    dummy_event = {
        "camera_id": "cam1",
        "ts": datetime.utcnow().isoformat(),
        "product_brand": brand,
        "product_name": name,
        "confidence": round(random.uniform(0.7, 0.99), 2)
    }

    # Insert into events table via API
    post_event(dummy_event)

    # Fetch events for cam1
    get_events("cam1")

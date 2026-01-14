import os
import time
import requests
import random

# API endpoint for posting events
API_ENDPOINT ="http://localhost:8000/events"

# Some dummy labels to simulate detections
DUMMY_LABELS = ["person", "car", "dog", "cat", "bottle", "chair", "tv"]

def generate_dummy_event():
    """Generate a fake detection event."""
    label = random.choice(DUMMY_LABELS)
    confidence = round(random.uniform(0.5, 0.99), 2)
    bbox = [
        random.randint(0, 100),   # x1
        random.randint(0, 100),   # y1
        random.randint(100, 200), # x2
        random.randint(100, 200), # y2
    ]
    ev = {
        "camera_id": "cam1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "label": label,
        "confidence": confidence,
        "bbox": bbox,
    }
    return ev

def main():
    print("=== Dummy Inference Service Started ===")
    print(f"Posting to API endpoint: {API_ENDPOINT}")

    while True:
        ev = generate_dummy_event()
        print("Generated dummy event:", ev)
        try:
            r = requests.post(API_ENDPOINT, json=ev, timeout=2)
            print("Posted event:", r.status_code, r.text)
        except Exception as e:
            print("Failed to post event:", e)
        time.sleep(2)  # send every 2 seconds

if __name__ == "__main__":
    main()

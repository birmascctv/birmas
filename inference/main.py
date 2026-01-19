import os, time, cv2, requests
from ultralytics import YOLO
from tracker import ProductTracker   # 👈 ADD THIS

RTSP_URL = "rtsp://100.87.93.95:8554/cam1?tcp"
API_ENDPOINT = "http://localhost:8000/api/events"
MODEL_PATH = "best.pt"

LOG_TTL = 10  # seconds

def open_stream(url):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("ERROR: Could not open RTSP stream")
        return None
    print("RTSP stream opened successfully")
    return cap

cap = open_stream(RTSP_URL)

# -------------------------
# Load YOLO
# -------------------------
try:
    model = YOLO(MODEL_PATH)
    print("Model loaded successfully")
    print("Model classes:", model.names)
except Exception as e:
    print("Model load failed:", e)
    exit(1)

# -------------------------
# Initialize ByteTrack
# -------------------------
tracker = ProductTracker(fps=30)
seen_tracks = {}   # track_id -> last_seen_time

# -------------------------
# Main loop
# -------------------------
while True:
    if cap is None or not cap.isOpened():
        cap = open_stream(RTSP_URL)
        time.sleep(2)
        continue

    ok, frame = cap.read()
    if not ok:
        cap.release()
        cap = open_stream(RTSP_URL)
        time.sleep(0.5)
        continue

    try:
        # ==========================================================
        # 4.1 YOLO → detections (convert format)
        # ==========================================================
        res = model.predict(
            frame,
            imgsz=768,
            conf=0.3,
            iou=0.45,
            verbose=False
        )[0]

        detections = []
        for b in res.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            score = float(b.conf)
            class_id = int(b.cls)

            detections.append([
                x1, y1, x2, y2, score, class_id
            ])

        # ==========================================================
        # 4.2 ByteTrack → assign IDs
        # ==========================================================
        tracked_objects = tracker.update(detections, frame.shape)

        now = time.time()

        # ==========================================================
        # 4.3 Log ONLY new track_ids
        # ==========================================================
        for obj in tracked_objects:
            tid = obj["track_id"]

            if tid not in seen_tracks:
                # Map class_id → label
                class_id = obj.get("class_id", None)
                label = "unknown"
                if class_id is not None:
                    label = model.names[class_id]

                ev = {
                    "camera_id": "cam1",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "label": label,
                    "track_id": tid,
                    "bbox": obj["bbox"]
                }

                try:
                    r = requests.post(API_ENDPOINT, json=ev, timeout=2)
                    print(f"Logged {label} (ID {tid}) → {r.status_code}")
                except Exception as e:
                    print("Failed to post event:", e)

                seen_tracks[tid] = now
            else:
                seen_tracks[tid] = now

        # Cleanup old IDs
        for tid in list(seen_tracks.keys()):
            if now - seen_tracks[tid] > LOG_TTL:
                del seen_tracks[tid]

    except Exception as e:
        print("Inference error:", e)
        time.sleep(1)

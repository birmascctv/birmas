import time, cv2, requests
from ultralytics import YOLO
from tracker import ProductTracker

STREAM_URL = "rtmp://100.87.93.95:1935/cam1"
API_ENDPOINT = "http://192.168.68.101:8000/api/events"
MODEL_PATH = "models/best.pt"

IMG_SIZE = 640
FRAME_SKIP = 2
LOG_TTL = 8

def open_stream(url):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[ERROR] Unable to open stream: {url}")
        return None
    print(f"[INFO] Stream opened successfully: {url}")
    return cap

cap = open_stream(STREAM_URL)

# ---------------- LOAD MODEL ----------------
model = YOLO(MODEL_PATH)
model.model.eval()
print("Model loaded:", model.names)

# ---------------- INIT TRACKER ----------------
tracker = ProductTracker(fps=30)

# track_id -> {last_seen, label}
seen_tracks = {}

frame_count = 0
def open_stream(url):
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[ERROR] Unable to open RTSP stream: {url}")
        return None
    print(f"[INFO] RTSP stream opened successfully: {url}")
    return cap

cap = open_stream(STREAM_URL)

# ---------------- MAIN LOOP ----------------
while True:
    if cap is None or not cap.isOpened():
        print("[WARN] Stream not opened, retrying...")
        cap = open_stream(STREAM_URL)
        time.sleep(1)
        continue

    ok, frame = cap.read()
    if not ok:
        print("[WARN] Failed to read frame, reconnecting...")
        cap.release()
        cap = open_stream(STREAM_URL)
        continue

    # Log once when the first frame is successfully read
    if frame_count == 0:
        print("[INFO] First frame received from RTSP stream")

    frame_count += 1
    if frame_count % FRAME_SKIP != 0:
        continue

    now = time.time()

    try:
        # -------- YOLO --------
        res = model.predict(
            frame,
            imgsz=IMG_SIZE,
            conf=0.35,
            iou=0.45,
            verbose=False
        )[0]

        detections = []
        for b in res.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            detections.append([
                x1, y1, x2, y2,
                float(b.conf),
                int(b.cls)
            ])

        # -------- BYTETRACK --------
        tracked = tracker.update(detections, frame.shape)

        # -------- PRODUCT ADDED --------
        for obj in tracked:
            tid = obj["track_id"]
            label = model.names[obj["class_id"]] if obj["class_id"] is not None else "unknown"

            if tid not in seen_tracks:
                payload = {
                    "camera_id": "cam1",
                    "event_type": "PRODUCT_ADDED",
                    "label": label,
                    "track_id": tid
                }

                requests.post(API_ENDPOINT, json=payload, timeout=2)
                print(f"+ ADDED {label} (ID {tid})")

                seen_tracks[tid] = {
                    "last_seen": now,
                    "label": label
                }
            else:
                seen_tracks[tid]["last_seen"] = now

        # -------- PRODUCT REMOVED --------
        for tid in list(seen_tracks.keys()):
            if now - seen_tracks[tid]["last_seen"] > LOG_TTL:
                payload = {
                    "camera_id": "cam1",
                    "event_type": "PRODUCT_REMOVED",
                    "label": seen_tracks[tid]["label"],
                    "track_id": tid
                }

                requests.post(API_ENDPOINT, json=payload, timeout=2)
                print(f"- REMOVED {seen_tracks[tid]['label']} (ID {tid})")

                del seen_tracks[tid]

    except Exception as e:
        print("Error:", e)
        time.sleep(1)

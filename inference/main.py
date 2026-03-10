import sys, os
import time, cv2, requests
import threading
from ultralytics import YOLO
from tracker import ProductTracker
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

print(f"[DEBUG] Running file: {__file__}")
print(f"[DEBUG] Python executable: {sys.executable}")

# Jakarta timezone (WIB = UTC+7)
WIB = timezone(timedelta(hours=7))

def now_wib():
    """Current naive datetime in Jakarta local time (WIB, UTC+7)."""
    return datetime.now(WIB).replace(tzinfo=None)

# ---------------- CONFIG ----------------
STREAM_URL     = os.getenv("STREAM_URL", "")
API_ENDPOINT   = os.getenv("API_ENDPOINT", "")
MODEL_PATH     = os.getenv("MODEL_PATH", "models/best.pt")
INFER_INTERVAL = float(os.getenv("INFER_INTERVAL", "1"))  # min seconds between inferences
LOG_TTL        = float(os.getenv("LOG_TTL", "10"))         # seconds before product marked sold
STARTUP_GRACE  = 60.0  # first 60s: all new tracks are "added" (not "restock")

print(f"[DEBUG] STREAM_URL={STREAM_URL}")
print(f"[DEBUG] API_ENDPOINT={API_ENDPOINT}")
print(f"[DEBUG] MODEL_PATH={MODEL_PATH}")
print(f"[DEBUG] INFER_INTERVAL={INFER_INTERVAL}s  LOG_TTL={LOG_TTL}s")

IMG_SIZE = 640
# ----------------------------------------

# ---------- LIVE FRAME READER THREAD ----------
# Runs in background, continuously reads the camera stream.
# Only keeps the very latest frame — inference always gets a current snapshot.
_latest_frame = None
_frame_lock   = threading.Lock()

def _stream_reader(url):
    global _latest_frame
    cap = None
    while True:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                print("[WARN] Reader: stream unavailable, retrying in 3s...")
                cap = None
                time.sleep(3)
                continue
            print("[INFO] Reader: stream connected")

        ok, frame = cap.read()
        if ok:
            with _frame_lock:
                _latest_frame = frame
        else:
            print("[WARN] Reader: read failed, reconnecting...")
            cap.release()
            cap = None
            time.sleep(1)

threading.Thread(target=_stream_reader, args=(STREAM_URL,), daemon=True).start()
# -----------------------------------------------

# ---------------- LOAD MODEL ----------------
model = YOLO(MODEL_PATH)
model.model.eval()
print("Model loaded:", model.names)

# ---------------- INIT TRACKER ----------------
tracker     = ProductTracker(fps=30)
seen_tracks = {}   # {track_id: {"last_seen": float, "label": str}}
frame_count = 0
start_time  = time.time()

def post_event(event_type: str, label: str, bbox: str, confidence: float):
    payload = {
        "camera_id":  "cam1",
        "ts":         now_wib().isoformat(),
        "label":      label,
        "bbox":       bbox,
        "confidence": confidence,
        "event_type": event_type,
    }
    try:
        requests.post(API_ENDPOINT, json=payload, timeout=2)
    except Exception as e:
        print(f"[ERROR] post {event_type} for {label}: {e}")

# Wait for first frame before starting inference
print("[INFO] Waiting for first frame from stream...")
while _latest_frame is None:
    time.sleep(0.2)
print("[INFO] Stream ready — starting inference loop")

# ---------------- MAIN INFERENCE LOOP ----------------
while True:
    loop_start = time.time()

    # Grab the latest decoded frame from the reader thread
    with _frame_lock:
        frame = _latest_frame.copy()

    frame_count += 1
    if frame_count == 1:
        cv2.imwrite("debug_first_frame.jpg", frame)
        print("[INFO] Saved debug_first_frame.jpg")

    try:
        # -------- YOLO --------
        res = model.predict(frame, imgsz=IMG_SIZE, conf=0.35, iou=0.45, verbose=False)[0]

        detections = []
        for b in res.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            detections.append([x1, y1, x2, y2, float(b.conf), int(b.cls)])

        print(f"[DEBUG] Frame {frame_count}: {len(detections)} detections")

        # -------- BYTETRACK --------
        tracked    = tracker.update(detections, frame.shape)
        now        = time.time()
        in_startup = (now - start_time) < STARTUP_GRACE

        # -------- PRODUCT ADDED / RESTOCK --------
        for obj in tracked:
            tid      = obj["track_id"]
            class_id = obj["class_id"]
            label    = model.names[class_id] if class_id is not None else "unknown"
            bbox     = (f"{obj['bbox'][0]:.1f},{obj['bbox'][1]:.1f},"
                        f"{obj['bbox'][2]:.1f},{obj['bbox'][3]:.1f}")

            if tid not in seen_tracks:
                same_class_active = any(v["label"] == label for v in seen_tracks.values())
                event_type = "added" if (in_startup or not same_class_active) else "restock"
                post_event(event_type, label, bbox, float(obj["confidence"]))
                print(f"[{event_type.upper()}] {label} (track {tid})")
                seen_tracks[tid] = {"last_seen": now, "label": label}
            else:
                seen_tracks[tid]["last_seen"] = now

        # -------- PRODUCT SOLD --------
        for tid in list(seen_tracks.keys()):
            if now - seen_tracks[tid]["last_seen"] > LOG_TTL:
                label = seen_tracks[tid]["label"]
                post_event("sold", label, "", 0.0)
                print(f"[SOLD] {label} (track {tid})")
                del seen_tracks[tid]

    except Exception as e:
        print(f"[ERROR] {e}")

    # Sleep only the remaining time to hit INFER_INTERVAL.
    # If YOLO took longer than INFER_INTERVAL (e.g. throttled Pi), no sleep — runs immediately.
    elapsed    = time.time() - loop_start
    sleep_time = max(0.0, INFER_INTERVAL - elapsed)
    if sleep_time > 0:
        time.sleep(sleep_time)


import sys, os
import os, time, cv2, requests, base64
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
INFER_INTERVAL = float(os.getenv("INFER_INTERVAL", "0"))  # min seconds between inferences (0 = max speed)
LOG_TTL        = float(os.getenv("LOG_TTL", "10"))         # seconds before product marked sold

# ── Model validation ──
if not os.path.isfile(MODEL_PATH):
    print(f"[FATAL] Model not found: {MODEL_PATH}")
    print(f"[FATAL] Working dir: {os.getcwd()}")
    sys.exit(1)
else:
    model_size = os.path.getsize(MODEL_PATH) / (1024*1024)
    print(f"[INFO] Model OK: {MODEL_PATH} ({model_size:.1f} MB)")

if not STREAM_URL:
    print("[FATAL] STREAM_URL not set")
    sys.exit(1)

if not API_ENDPOINT:
    print("[FATAL] API_ENDPOINT not set")
    sys.exit(1)
STARTUP_GRACE  = 60.0  # first 60s: all new tracks are "added" (not "restock")

def _parse_zone(env_val):
    """Parse 'x1,y1,x2,y2' string into tuple or None."""
    if not env_val:
        return None
    try:
        x1, y1, x2, y2 = map(float, env_val.split(","))
        return (x1, y1, x2, y2)
    except Exception:
        print(f"[WARN] Invalid zone format: {env_val!r} — expected 'x1,y1,x2,y2'")
        return None

def _in_zone(bbox, zone):
    """Return True if bbox center is inside the zone rectangle."""
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    return zone[0] <= cx <= zone[2] and zone[1] <= cy <= zone[3]

# Zone where products originate FROM the fridge (customer taking product).
# Bounding box center inside this zone on first detection → event_type="added".
# Outside this zone → event_type="restock" (product came from outside the fridge).
# Set FRIDGE_ZONE="" to disable zone detection and fall back to same-class logic.
FRIDGE_ZONE = _parse_zone(os.getenv("FRIDGE_ZONE", "560,0,780,230"))

print(f"[DEBUG] STREAM_URL={STREAM_URL}")
print(f"[DEBUG] API_ENDPOINT={API_ENDPOINT}")
print(f"[DEBUG] MODEL_PATH={MODEL_PATH}")
print(f"[DEBUG] INFER_INTERVAL={INFER_INTERVAL}s  LOG_TTL={LOG_TTL}s  FRIDGE_ZONE={FRIDGE_ZONE}")

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

FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "frames")
os.makedirs(FRAMES_DIR, exist_ok=True)

# Color map: BGR for cv2
_COLORS = {"sold": (0, 200, 0), "restock": (200, 120, 0), "added": (0, 0, 220)}

def post_event(event_type: str, label: str, bbox: str, confidence: float,
               frame_img=None):
    ts_str = now_wib().isoformat()
    payload = {
        "camera_id":  "cam1",
        "ts":         ts_str,
        "label":      label,
        "bbox":       bbox,
        "confidence": confidence,
        "event_type": event_type,
    }
    # Draw bbox on a copy and save locally + encode for server
    annotated = None
    if frame_img is not None:
        try:
            annotated = frame_img.copy()
            if bbox and bbox.strip():
                coords = list(map(float, bbox.split(",")))
                if len(coords) == 4:
                    x1, y1, x2, y2 = map(int, coords)
                    color = _COLORS.get(event_type, (0, 0, 220))
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                    txt = f"{label} {confidence:.0%}"
                    (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
                    cv2.putText(annotated, txt, (x1 + 2, y1 - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        except Exception as e:
            print(f"[WARN] bbox draw: {e}")
            annotated = frame_img

    # Save annotated frame locally
    if annotated is not None:
        try:
            ts_file = now_wib().strftime("%Y%m%d_%H%M%S")
            fname = f"{ts_file}_{event_type}_{label}.jpg"
            cv2.imwrite(os.path.join(FRAMES_DIR, fname), annotated,
                        [cv2.IMWRITE_JPEG_QUALITY, 85])
        except Exception as e:
            print(f"[WARN] frame save: {e}")

    # Encode annotated frame for server (with bbox drawn)
    if annotated is not None:
        try:
            ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                payload["frame"] = base64.b64encode(buf.tobytes()).decode("ascii")
        except Exception:
            pass
    try:
        requests.post(API_ENDPOINT, json=payload, timeout=5)
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
                if in_startup:
                    event_type = "added"
                elif FRIDGE_ZONE is not None:
                    # Zone-based: product appeared from fridge area = customer taking product
                    # Product appeared from outside fridge = restock
                    event_type = "added" if _in_zone(obj["bbox"], FRIDGE_ZONE) else "restock"
                else:
                    # Fallback: first of this class = added, duplicate class = restock
                    same_class_active = any(v["label"] == label for v in seen_tracks.values())
                    event_type = "added" if not same_class_active else "restock"
                post_event(event_type, label, bbox, float(obj["confidence"]), frame_img=frame)
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


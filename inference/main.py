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

# LOG_TTL: seconds of continuous absence before a tracked product is marked
# "sold". Must be comfortably larger than REID_WINDOW below — otherwise a
# product that's only briefly occluded (a customer's hand, someone leaning
# over the table, etc.) would get marked sold before the tracker even has a
# chance to re-identify it as the same item. Bumped from 10s -> 20s for the
# dine-in area, where drinks sit in/out of camera view much longer than a
# quick fridge grab-and-go would.
LOG_TTL        = float(os.getenv("LOG_TTL", "20"))

# REID_WINDOW: seconds a lost track is kept around for re-identification by
# ProductTracker before being permanently forgotten. Prevents a momentary
# occlusion from being reported as "sold" + a new "added" for the same
# physical item seconds later (the main cause of timeline dot spam in a
# dine-in setting where people sit with their drink for a while).
REID_WINDOW    = float(os.getenv("REID_WINDOW", "10"))

# CONFIRM_SECONDS: a new track must be seen continuously for at least this
# long before an "added"/"restock" event is actually posted. Filters out
# one-off flicker/false-positive detections (a single bad frame) so they
# never reach the timeline at all — instead of posting immediately on the
# very first frame a track is seen.
CONFIRM_SECONDS = float(os.getenv("CONFIRM_SECONDS", "1.5"))

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

# Zone where products originate FROM the fridge/chiller (customer taking product).
# Bounding box center inside this zone on first detection → event_type="added".
# Outside this zone → event_type="restock" (product came from outside the fridge,
# e.g. staff placing it on the counter/bar for restocking).
# Coordinates measured from the actual 1280x720 camera frame (2026-08-03):
# the chiller/door area occupies the right ~43% of the frame, the counter/bar
# staging area (where staff restock) occupies the left ~55%. See
# training_results/frame/sudirman_chiller.jpg and sudirman_bar.jpg for reference.
# Set FRIDGE_ZONE="" to disable zone detection and fall back to same-class logic.
FRIDGE_ZONE = _parse_zone(os.getenv("FRIDGE_ZONE", "741,0,1280,348"))

# RESTOCK_COOLDOWN: minimum seconds between two "restock" events of the same
# class. During an actual restocking session, staff handle several bottles
# of the same product on the counter in quick succession — each bottle is a
# genuinely distinct track, but posting a separate timeline dot per bottle
# is noise; one dot per stocking session is what matters to the business.
RESTOCK_COOLDOWN = float(os.getenv("RESTOCK_COOLDOWN", "120"))

# ---------------- PEOPLE / OCCUPANCY DETECTION (optional) ----------------
# Detects people crossing the door (in/out) and posts a periodic "activity"
# heartbeat, used by the dashboard to show hourly foot traffic and a
# store-open/closed indicator. Disabled by default — requires a second,
# generic COCO-pretrained model (yolov8n.pt has a "person" class; the
# product model does not) to be present at PERSON_MODEL_PATH.
ENABLE_PEOPLE_DETECTION = os.getenv("ENABLE_PEOPLE_DETECTION", "false").lower() == "true"
PERSON_MODEL_PATH       = os.getenv("PERSON_MODEL_PATH", "models/yolov8n.pt")
PEOPLE_API_ENDPOINT     = os.getenv("PEOPLE_API_ENDPOINT", API_ENDPOINT.replace("/events", "/people-events"))

# DOOR_ZONE: re-calibrated 2026-08-04 against training_results/frame/sudirman.jpg
# with a pixel grid overlay. The PREVIOUS box (950,0,1200,300) was actually
# sitting on the product storage/box shelf behind the door, not the door
# itself — it fully overlapped FRIDGE_ZONE, so a customer merely browsing/
# lingering at the chiller could trigger spurious door in/out events, and
# short PERSON_LOG_TTL track drops there biased "out" far above "in". The
# corrected box (745,0,945,330) sits directly on the visible glass door
# frame/panels, to the LEFT of the storage shelf, confirmed against the
# frame by the user. A person track that FIRST appears here = walked in
# ("in"). A person track that DISAPPEARS while last seen here = walked out
# ("out").
DOOR_ZONE = _parse_zone(os.getenv("DOOR_ZONE", "745,0,945,330"))

PERSON_INTERVAL        = float(os.getenv("PERSON_INTERVAL", "1.0"))   # run person model at most this often (seconds) — separate, slower cadence than product inference to limit CPU load on the Pi
PERSON_CONFIRM_SECONDS = float(os.getenv("PERSON_CONFIRM_SECONDS", "0.5"))
PERSON_LOG_TTL         = float(os.getenv("PERSON_LOG_TTL", "5.0"))    # people move faster than products — a shorter disappearance timeout than LOG_TTL, but bumped from 3.0 to 5.0 (2026-08-04) to reduce spurious track fragmentation from brief occlusion near the door
ACTIVITY_BUCKET_SECONDS = float(os.getenv("ACTIVITY_BUCKET_SECONDS", "300"))  # throttle "activity" heartbeat to once per 5 min

print(f"[DEBUG] STREAM_URL={STREAM_URL}")
print(f"[DEBUG] API_ENDPOINT={API_ENDPOINT}")
print(f"[DEBUG] MODEL_PATH={MODEL_PATH}")
print(f"[DEBUG] INFER_INTERVAL={INFER_INTERVAL}s  LOG_TTL={LOG_TTL}s  "
      f"REID_WINDOW={REID_WINDOW}s  CONFIRM_SECONDS={CONFIRM_SECONDS}s  FRIDGE_ZONE={FRIDGE_ZONE}  "
      f"RESTOCK_COOLDOWN={RESTOCK_COOLDOWN}s")
print(f"[DEBUG] ENABLE_PEOPLE_DETECTION={ENABLE_PEOPLE_DETECTION}  PERSON_MODEL_PATH={PERSON_MODEL_PATH}  "
      f"DOOR_ZONE={DOOR_ZONE}  PERSON_INTERVAL={PERSON_INTERVAL}s  PERSON_LOG_TTL={PERSON_LOG_TTL}s")

# Tracks the last time a "restock" event was posted for each class_id, so
# repeated handling of the same product during one stocking session doesn't
# flood the timeline with duplicate dots.
last_restock_ts = {}

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

# ---------------- LOAD PEOPLE MODEL (optional) ----------------
person_model = None
if ENABLE_PEOPLE_DETECTION:
    if os.path.isfile(PERSON_MODEL_PATH):
        person_model = YOLO(PERSON_MODEL_PATH)
        person_model.model.eval()
        print(f"[INFO] People-detection model loaded: {PERSON_MODEL_PATH}")
    else:
        print(f"[WARN] ENABLE_PEOPLE_DETECTION=true but {PERSON_MODEL_PATH} "
              f"not found — people detection disabled until the model is deployed.")

# ---------------- INIT TRACKER ----------------
tracker     = ProductTracker(lost_ttl=REID_WINDOW)
# seen_tracks[track_id] = {
#   "label": str, "first_seen": float, "last_seen": float,
#   "posted": bool,           -- has an added/restock event actually been sent?
#   "event_type": str,        -- "added" | "restock" — set once posted, used to decide whether "sold" should fire
#   "origin_bbox": str,       -- bbox at first detection, used for the zone check
#   "bbox": str,              -- most recent bbox, used to annotate the "sold" frame
#   "frame": np.ndarray,      -- most recent frame, used to annotate the "sold" frame
# }
seen_tracks = {}
frame_count = 0
start_time  = time.time()

# People/occupancy tracker + state (only used if person_model loaded)
people_tracker      = ProductTracker(match_iou=0.2, lost_ttl=PERSON_LOG_TTL, reid_iou=0.1, reid_dist_frac=0.2)
seen_people         = {}
last_person_infer   = 0.0
last_activity_post  = 0.0

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

def post_people_event(event_type: str, confidence: float = 0.0):
    """event_type: 'in' | 'out' | 'activity'"""
    payload = {
        "camera_id":  "cam1",
        "ts":         now_wib().isoformat(),
        "event_type": event_type,
        "confidence": confidence,
    }
    try:
        requests.post(PEOPLE_API_ENDPOINT, json=payload, timeout=5)
    except Exception as e:
        print(f"[ERROR] post people-event {event_type}: {e}")

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
                # New track — don't post yet. Wait for CONFIRM_SECONDS of
                # continuous tracking so a single flicker/false-positive
                # frame never reaches the dashboard timeline.
                seen_tracks[tid] = {
                    "label":       label,
                    "first_seen":  now,
                    "last_seen":   now,
                    "posted":      False,
                    "origin_bbox": bbox,
                    "bbox":        bbox,
                    "frame":       frame,
                }
            else:
                seen_tracks[tid]["last_seen"] = now
                seen_tracks[tid]["bbox"]      = bbox
                seen_tracks[tid]["frame"]     = frame

            tr = seen_tracks[tid]
            if not tr["posted"] and (now - tr["first_seen"]) >= CONFIRM_SECONDS:
                if in_startup:
                    event_type = "added"
                elif FRIDGE_ZONE is not None:
                    # Zone-based: product appeared from fridge area = customer taking product
                    # Product appeared from outside fridge = restock
                    origin_coords = list(map(float, tr["origin_bbox"].split(",")))
                    event_type = "added" if _in_zone(origin_coords, FRIDGE_ZONE) else "restock"
                else:
                    # Fallback: first of this class = added, duplicate class = restock
                    same_class_active = any(
                        v["label"] == label and v["posted"] for v in seen_tracks.values()
                    )
                    event_type = "added" if not same_class_active else "restock"

                if event_type == "restock":
                    # De-dupe: skip posting if this class was already logged as
                    # restocked within RESTOCK_COOLDOWN seconds — staff handling
                    # several bottles of the same product in one stocking pass
                    # would otherwise spam the timeline with one dot per bottle.
                    last_ts = last_restock_ts.get(class_id, 0)
                    if now - last_ts < RESTOCK_COOLDOWN:
                        tr["posted"]     = True
                        tr["event_type"] = "restock"
                        continue
                    last_restock_ts[class_id] = now

                post_event(event_type, label, tr["origin_bbox"], float(obj["confidence"]), frame_img=tr["frame"])
                print(f"[{event_type.upper()}] {label} (track {tid})")
                tr["posted"]     = True
                tr["event_type"] = event_type

        # -------- PRODUCT SOLD --------
        for tid in list(seen_tracks.keys()):
            tr = seen_tracks[tid]
            if now - tr["last_seen"] > LOG_TTL:
                # Only report "sold" for tracks that were actually confirmed
                # AND classified as "added" (a customer taking the product
                # from the chiller). Tracks classified as "restock" are staff
                # placing stock on the counter/shelf — their disappearance
                # from view just means the item was put away, not sold, so no
                # "sold" event is posted for those (this was previously firing
                # a false "sold" for every restocked item, doubling noise).
                if tr["posted"] and tr.get("event_type") == "added":
                    post_event("sold", tr["label"], tr["bbox"], 0.0, frame_img=tr["frame"])
                    print(f"[SOLD] {tr['label']} (track {tid})")
                del seen_tracks[tid]

    except Exception as e:
        print(f"[ERROR] {e}")

    # -------- PEOPLE / OCCUPANCY (optional, separate cadence) --------
    if person_model is not None and (time.time() - last_person_infer) >= PERSON_INTERVAL:
        last_person_infer = time.time()
        try:
            now = time.time()
            pres = person_model.predict(frame, imgsz=IMG_SIZE, conf=0.4, iou=0.45,
                                         classes=[0], verbose=False)[0]  # class 0 = person (COCO)
            pdetections = []
            for b in pres.boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                pdetections.append([x1, y1, x2, y2, float(b.conf), 0])

            ptracked = people_tracker.update(pdetections, frame.shape)

            if ptracked and (now - last_activity_post) >= ACTIVITY_BUCKET_SECONDS:
                post_people_event("activity", confidence=max(o["confidence"] for o in ptracked))
                last_activity_post = now

            for obj in ptracked:
                tid  = obj["track_id"]
                bbox = obj["bbox"]
                if tid not in seen_people:
                    seen_people[tid] = {
                        "first_seen":  now, "last_seen": now,
                        "posted_in":   False, "origin_bbox": bbox, "bbox": bbox,
                        "confidence":  obj["confidence"],
                    }
                else:
                    seen_people[tid]["last_seen"]  = now
                    seen_people[tid]["bbox"]       = bbox
                    seen_people[tid]["confidence"] = obj["confidence"]

                pt = seen_people[tid]
                if not pt["posted_in"] and (now - pt["first_seen"]) >= PERSON_CONFIRM_SECONDS:
                    if DOOR_ZONE is not None and _in_zone(pt["origin_bbox"], DOOR_ZONE):
                        post_people_event("in", confidence=pt["confidence"])
                        print(f"[PEOPLE IN] track {tid}")
                    pt["posted_in"] = True

            for tid in list(seen_people.keys()):
                pt = seen_people[tid]
                if now - pt["last_seen"] > PERSON_LOG_TTL:
                    if DOOR_ZONE is not None and _in_zone(pt["bbox"], DOOR_ZONE):
                        post_people_event("out", confidence=pt["confidence"])
                        print(f"[PEOPLE OUT] track {tid}")
                    del seen_people[tid]
        except Exception as e:
            print(f"[ERROR] people-detection: {e}")

    # Sleep only the remaining time to hit INFER_INTERVAL.
    # If YOLO took longer than INFER_INTERVAL (e.g. throttled Pi), no sleep — runs immediately.
    elapsed    = time.time() - loop_start
    sleep_time = max(0.0, INFER_INTERVAL - elapsed)
    if sleep_time > 0:
        time.sleep(sleep_time)


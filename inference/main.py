import os, time, cv2, requests
from ultralytics import YOLO

RTSP_URL = os.getenv("RTSP_URL", "rtsp://100.87.93.95:8554/cam1")
API_ENDPOINT = os.getenv("API_ENDPOINT", "http://backend:8000/events")
MODEL_PATH = os.getenv("MODEL_PATH", "./best.pt")

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(RTSP_URL)

while True:
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.5); continue
    res = model.predict(frame, imgsz=768, conf=0.3, iou=0.45, verbose=False)[0]
    for b in res.boxes:
        ev = {
            "camera_id": "cam1", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "label": model.names[int(b.cls)], "confidence": float(b.conf),
            "bbox": [float(x) for x in b.xyxy.tolist()[0]]
        }
        try: requests.post(API_ENDPOINT, json=ev, timeout=2)
        except Exception: pass
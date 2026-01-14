import os, time, cv2, requests
from ultralytics import YOLO

#RTSP_URL = os.getenv("RTSP_URL", "rtsp://100.87.93.95:8554/cam1")
#API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:8000/events")
#MODEL_PATH = os.getenv("MODEL_PATH", "./best.pt")


RTSP_URL = "rtsp://100.87.93.95:8554/cam1"
API_ENDPOINT = "http://localhost:8000/events"
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "models", "best.pt")

#MODEL_PATH = "models/best.pt"
#model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(RTSP_URL)

try:
    model = YOLO(model_path)
    print("Model loaded successfully")
    print("Model classes:", model.names)
    import numpy as np
    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
    res = model.predict(dummy, imgsz=640, verbose=False)[0]
    print("Dry run inference completed, boxes:", len(res.boxes))
except Exception as e:
    print("Model load failed:", e)
    model = None

while True:
    if not cap.isOpened():
        print("RTSP stream not opened — check URL or network")
        time.sleep(2)
        continue
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.5)
        print("Failed to read frame from RTSP")
        continue
    else:
        print("Succeed to read frame from RTSP")

    try:
        res = model.predict(frame, imgsz=768, conf=0.3, iou=0.45, verbose=False)[0]
        for b in res.boxes:
            label = model.names[int(b.cls)]
            conf = float(b.conf)
            print(f"Detected {label} with {conf:.2f} confidence")
            ev = { 
                "camera_id": "cam1", 
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), 
                "label": label, 
                "confidence": conf, 
                "bbox": [float(x) for x in b.xyxy.tolist()[0]] 
            } 
            try: 
                r = requests.post(API_ENDPOINT, json=ev, timeout=2) 
                print("Posted event:", r.status_code) 
            except Exception as e: 
                print("Failed to post event:", e) 
    except Exception as e: 
        print("Inference error:", e) 
        time.sleep(1)
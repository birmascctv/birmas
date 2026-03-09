import numpy as np
from types import SimpleNamespace
from yolox_tracker.tracker.byte_tracker import BYTETracker

def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter)

class ProductTracker:
    def __init__(self, fps=30):
        args = SimpleNamespace(
            track_thresh=0.5,
            match_thresh=0.8,
            track_buffer=30,
            conf_thresh=0.7,
        )
        self.tracker = BYTETracker(args, frame_rate=fps)

    def update(self, detections, frame_shape):
        if len(detections) == 0:
            return []

        dets_np = np.array([
            [d[0], d[1], d[2], d[3], d[4]]
            for d in detections
        ])

        tracks = self.tracker.update(
            dets_np,
            img_info=(frame_shape[0], frame_shape[1]),
            img_size=(640, 640)
        )

        results = []
        for t in tracks:
            x, y, w, h = t.tlwh
            track_box = [x, y, x + w, y + h]

            # Match track to original detection by highest IoU
            best_iou, best_cid, best_conf = 0.0, None
            for d in detections:
                iou = _iou(track_box, d[:4])
                if iou > best_iou:
                    best_iou, best_cid, best_conf = iou, d[5], d[4]

            results.append({
                "track_id": t.track_id,
                "class_id": best_cid,
                "confidence": best_conf,
                "bbox": track_box
            })

        return results

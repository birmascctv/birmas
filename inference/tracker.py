import numpy as np


def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


class ProductTracker:
    def __init__(self, fps=30):
        self.track_buffer = max(int(fps), 30)
        self.match_thresh = 0.3
        self.next_track_id = 1
        self.tracks = {}

    def update(self, detections, frame_shape):
        if len(detections) == 0:
            for tid in list(self.tracks):
                self.tracks[tid]["missed"] += 1
                if self.tracks[tid]["missed"] > self.track_buffer:
                    del self.tracks[tid]
            return []

        unmatched = set(range(len(detections)))
        results = []

        for tid, track in list(self.tracks.items()):
            best_idx = None
            best_iou = 0.0
            for idx in unmatched:
                det = detections[idx]
                if track["class_id"] is not None and det[5] != track["class_id"]:
                    continue
                iou = _iou(track["bbox"], det[:4])
                if iou > best_iou:
                    best_iou = iou
                    best_idx = idx

            if best_idx is None or best_iou < self.match_thresh:
                track["missed"] += 1
                if track["missed"] > self.track_buffer:
                    del self.tracks[tid]
                continue

            det = detections[best_idx]
            track.update({
                "bbox": det[:4],
                "class_id": det[5],
                "confidence": float(det[4]),
                "missed": 0,
            })
            unmatched.remove(best_idx)
            results.append({
                "track_id": tid,
                "class_id": track["class_id"],
                "confidence": track["confidence"],
                "bbox": track["bbox"],
            })

        for idx in sorted(unmatched):
            det = detections[idx]
            tid = self.next_track_id
            self.next_track_id += 1
            self.tracks[tid] = {
                "bbox": det[:4],
                "class_id": det[5],
                "confidence": float(det[4]),
                "missed": 0,
            }
            results.append({
                "track_id": tid,
                "class_id": det[5],
                "confidence": float(det[4]),
                "bbox": det[:4],
            })

        return results

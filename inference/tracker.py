import time
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


def _center(bbox):
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def _dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


class ProductTracker:
    """
    Lightweight IoU-based tracker with a short-term re-identification
    ("lost pool") window.

    Why the lost pool exists: in a dine-in setting, a customer sitting with
    a drink causes frequent brief occlusions (a hand, another customer, or
    body movement blocking the camera's view of the bottle/can for a
    second or two). A naive tracker would drop the track the instant IoU
    match fails and assign a brand-new track_id when the product reappears
    — which upstream (inference/main.py) looks exactly like the old item
    being "sold" and a new one "added" seconds later, even though it's the
    same physical item the whole time. To avoid that spam, tracks that
    briefly fail to match are kept in `self.lost` for `lost_ttl` seconds
    and matched against new detections of the *same class* using a relaxed
    IoU-or-proximity check before falling back to allocating a new ID.
    """

    def __init__(self, match_iou=0.3, lost_ttl=10.0, reid_iou=0.15,
                 reid_dist_frac=0.12):
        self.match_iou      = match_iou       # IoU required to keep matching an ACTIVE track
        self.lost_ttl        = lost_ttl         # seconds a lost track may be re-identified before being forgotten
        self.reid_iou        = reid_iou         # relaxed IoU accepted when re-attaching a lost track
        self.reid_dist_frac  = reid_dist_frac   # or: center-distance below this fraction of the frame diagonal
        self.next_track_id  = 1
        self.tracks = {}   # active this-frame-or-recently tracks: tid -> {bbox, class_id, confidence}
        self.lost   = {}   # recently-lost tracks pending re-identification: tid -> {..., "lost_at": ts}

    def update(self, detections, frame_shape):
        now = time.time()
        h, w = frame_shape[0], frame_shape[1]
        diag = (w ** 2 + h ** 2) ** 0.5 or 1.0

        # Forget tracks that have been unmatched for too long.
        for tid in list(self.lost):
            if now - self.lost[tid]["lost_at"] > self.lost_ttl:
                del self.lost[tid]

        if len(detections) == 0:
            for tid, tr in list(self.tracks.items()):
                self.lost[tid] = {**tr, "lost_at": now}
            self.tracks = {}
            return []

        unmatched = set(range(len(detections)))
        results = []

        # 1. Strict match against currently active tracks.
        for tid, track in list(self.tracks.items()):
            best_idx, best_iou = None, 0.0
            for idx in unmatched:
                det = detections[idx]
                if det[5] != track["class_id"]:
                    continue
                iou = _iou(track["bbox"], det[:4])
                if iou > best_iou:
                    best_iou, best_idx = iou, idx

            if best_idx is None or best_iou < self.match_iou:
                # Didn't match this frame — move to the lost pool instead of
                # deleting outright, so a brief occlusion can still resolve
                # back to this same track_id below.
                self.lost[tid] = {**track, "lost_at": now}
                del self.tracks[tid]
                continue

            det = detections[best_idx]
            track.update({"bbox": det[:4], "class_id": det[5], "confidence": float(det[4])})
            unmatched.remove(best_idx)
            results.append({
                "track_id": tid, "class_id": track["class_id"],
                "confidence": track["confidence"], "bbox": track["bbox"],
            })

        # 2. Try to re-identify remaining detections against recently-lost tracks
        #    (same class + relaxed IoU or close proximity) before minting new IDs.
        for idx in sorted(unmatched):
            det = detections[idx]
            best_tid, best_score = None, -1.0
            for tid, tr in self.lost.items():
                if tr["class_id"] != det[5]:
                    continue
                iou  = _iou(tr["bbox"], det[:4])
                dist = _dist(_center(tr["bbox"]), _center(det[:4]))
                dist_ok = dist < self.reid_dist_frac * diag
                if iou >= self.reid_iou or dist_ok:
                    score = iou - (dist / diag)
                    if score > best_score:
                        best_score, best_tid = score, tid
            if best_tid is not None:
                tr = self.lost.pop(best_tid)
                tr.update({"bbox": det[:4], "class_id": det[5], "confidence": float(det[4])})
                self.tracks[best_tid] = tr
                unmatched.discard(idx)
                results.append({
                    "track_id": best_tid, "class_id": tr["class_id"],
                    "confidence": tr["confidence"], "bbox": tr["bbox"],
                })

        # 3. Anything still unmatched is a genuinely new track.
        for idx in sorted(unmatched):
            det = detections[idx]
            tid = self.next_track_id
            self.next_track_id += 1
            self.tracks[tid] = {"bbox": det[:4], "class_id": det[5], "confidence": float(det[4])}
            results.append({
                "track_id": tid, "class_id": det[5],
                "confidence": float(det[4]), "bbox": det[:4],
            })

        return results

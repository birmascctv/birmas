import numpy as np
from yolox.tracker.byte_tracker import BYTETracker


class ProductTracker:
    def __init__(self, fps=30):
        self.tracker = BYTETracker(
            track_thresh=0.5,
            track_buffer=30,
            match_thresh=0.8,
            frame_rate=fps
        )

    def update(self, detections, frame_shape):
        """
        detections: list of [x1, y1, x2, y2, score, class_id]
        frame_shape: frame.shape
        """

        if len(detections) == 0:
            return []

        dets = np.array([
            [d[0], d[1], d[2], d[3], d[4]]
            for d in detections
        ])

        online_targets = self.tracker.update(
            dets,
            img_info=(frame_shape[0], frame_shape[1]),
            img_size=(640, 640)
        )

        results = []
        for t in online_targets:
            x, y, w, h = t.tlwh
            results.append({
                "track_id": t.track_id,
                "bbox": [x, y, x + w, y + h]
            })

        return results

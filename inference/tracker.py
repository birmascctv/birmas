# tracker.py
# Placeholder for integrating DeepSORT or BYTETrack

class DummyTracker:
    def __init__(self):
        self.counter = 0

    def update(self, detections):
        # Assign fake IDs for now
        results = []
        for det in detections:
            self.counter += 1
            det['id'] = self.counter
            results.append(det)
        return results

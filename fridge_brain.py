import cv2
import time
import threading
import os
from ultralytics import YOLO
from collections import deque, Counter

# --- CONFIGURATION ---
STREAM_URL = "http://10.19.130.119:81/stream"
LOG_DIR = "run_logs"

# HYSTERESIS SETTINGS
CONF_HIGH = 0.35      # Confidence needed to START seeing an object
CONF_LOW = 0.15       # Confidence needed to KEEP seeing an object
HYSTERESIS_FRAMES = 8 # Memory length
MIN_STABLE_COUNT = 3  # Frames required to confirm presence

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

start_time_str = time.strftime("%Y%m%d_%H%M%S")
CURRENT_LOG_FILE = os.path.join(LOG_DIR, f"run_{start_time_str}.log")

# --- ML SETUP ---
print(f"Loading Smart Food Model (YOLOv8m)...")
model = YOLO('yolov8m.pt') 

CORE_FOODS = ['banana', 'carrot', 'hot dog', 'apple', 'orange', 'broccoli', 'pizza', 'sandwich', 'cake', 'bottle', 'cup']

class FreshFrame:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.ret = False
        self.frame = None
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                self.cap.open(STREAM_URL)
                time.sleep(1)

    def get_frame(self):
        return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()

def run_fridge_monitor():
    camera = FreshFrame(STREAM_URL)
    last_log_time = 0
    
    # Stores raw detections for the last X frames
    detection_history = deque(maxlen=HYSTERESIS_FRAMES)
    
    # Keep track of which items are currently "Active" in the fridge
    active_inventory = set()

    print(f"Monitoring with Confidence Hysteresis... Logs: {CURRENT_LOG_FILE}")

    while True:
        ret, frame = camera.get_frame()
        if not ret or frame is None:
            continue

        # We run the model at a very low threshold (CONF_LOW) to catch everything
        results = model(frame, stream=True, conf=CONF_LOW, verbose=False)

        current_frame_data = [] # List of (label, confidence)
        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                if label in CORE_FOODS:
                    current_frame_data.append((label, conf))
            
            annotated_frame = r.plot()

        # Update History with just the labels from this frame
        current_labels = [item[0] for item in current_frame_data]
        detection_history.append(current_labels)

        # --- HYSTERESIS LOGIC ---
        all_recent_labels = [label for frame_list in detection_history for label in frame_list]
        counts = Counter(all_recent_labels)
        
        # 1. ADD: If item appears > MIN_STABLE_COUNT times AND reached CONF_HIGH at least once
        new_stable_list = []
        for label, count in counts.items():
            # Find max confidence for this label in the current frame data
            max_conf_now = max([c for l, c in current_frame_data if l == label], default=0)
            
            if count >= MIN_STABLE_COUNT:
                # If it's already active, it just needs to stay above MIN_STABLE_COUNT
                if label in active_inventory:
                    new_stable_list.append(label)
                # If it's NOT active, it needs one "strong" sighting to start
                elif max_conf_now >= CONF_HIGH:
                    active_inventory.add(label)
                    new_stable_list.append(label)

        # 2. REMOVE: If item is in active_inventory but disappeared from history entirely
        active_inventory = {label for label in active_inventory if counts[label] >= 1}

        # Log once per second
        if time.time() - last_log_time >= 1.0:
            timestamp = time.strftime("%H:%M:%S")
            if active_inventory:
                summary = ", ".join([f"{list(active_inventory).count(x)} {x}" for x in set(active_inventory)])
                log_entry = f"[{timestamp}] Stable Inventory: {summary}"
            else:
                log_entry = f"[{timestamp}] Scanning..."
            
            print(log_entry)
            with open(CURRENT_LOG_FILE, "a") as f:
                f.write(log_entry + "\n")
            last_log_time = time.time()

        cv2.imshow("Hysteresis + Persistence Monitor", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            camera.stop()
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_fridge_monitor()
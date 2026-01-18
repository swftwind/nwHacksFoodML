import cv2
import time
import threading
import os
from ultralytics import YOLO

# --- CONFIGURATION ---
STREAM_URL = "http://10.19.130.119:81/stream"
LOG_DIR = "run_logs"

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generate a unique log file name based on the current start time
start_time_str = time.strftime("%Y%m%d_%H%M%S")
CURRENT_LOG_FILE = os.path.join(LOG_DIR, f"run_{start_time_str}.log")

# --- ML SETUP ---
print(f"Loading Smart Food Model (YOLOv8m)...")
model = YOLO('yolov8m.pt') 

# Expanded core foods to include 'sandwich' for your burgers
CORE_FOODS = ['banana', 'carrot', 'hot dog', 'apple', 'orange', 'broccoli', 'pizza', 'sandwich', 'cake']

# --- BUFFER CLEARING LOGIC ---
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
                # Attempt to reconnect if the stream drops
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
    
    # Initialize the new log file
    with open(CURRENT_LOG_FILE, "w") as f:
        f.write(f"--- Fridge Session Started: {time.ctime()} ---\n")

    print(f"Monitoring... Logs being saved to: {CURRENT_LOG_FILE}")

    while True:
        ret, frame = camera.get_frame()
        if not ret or frame is None:
            continue

        # Run AI (YOLOv8m)
        results = model(frame, stream=True, conf=0.25, verbose=False)

        for r in results:
            # Filter detections
            detections = [model.names[int(box.cls[0])] for box in r.boxes 
                          if model.names[int(box.cls[0])] in CORE_FOODS or 
                          model.names[int(box.cls[0])] in ['bottle', 'cup']]
            
            annotated_frame = r.plot()

            # Log once per second
            if time.time() - last_log_time >= 1.0:
                timestamp = time.strftime("%H:%M:%S")
                if detections:
                    counts = {x: detections.count(x) for x in set(detections)}
                    summary = ", ".join([f"{count} {name}" for name, count in counts.items()])
                    log_entry = f"[{timestamp}] Seen: {summary}"
                else:
                    log_entry = f"[{timestamp}] Scanning... (No specific food detected)"
                
                print(log_entry)
                with open(CURRENT_LOG_FILE, "a") as f:
                    f.write(log_entry + "\n")
                
                last_log_time = time.time()

        cv2.imshow("Lag-Free Fridge Monitor", annotated_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            camera.stop()
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_fridge_monitor()
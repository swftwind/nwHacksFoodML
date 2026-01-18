import cv2
import time
from ultralytics import YOLO

# --- CONFIGURATION ---
STREAM_URL = "http://172.20.10.2:81/stream"
LOG_FILE = "fridge_inventory.log"

# --- ML SETUP ---
print("Loading Multi-Object Food Model...")
# This model is specialized for 100+ common food/grocery items
model = YOLO('yolov8n.pt') # We use the base model, but we will filter for food classes

# A list of COCO classes that are food/drink related
FOOD_IDS = [39, 41, 42, 43, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55] 
# (These represent: bottle, cup, fork, knife, spoon, bowl, banana, apple, 
# sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake)

def run_multi_food_monitor():
    cap = cv2.VideoCapture(STREAM_URL)
    last_log_time = 0

    print(f"Monitoring... Logging to {LOG_FILE}")

    while True:
        ret, frame = cap.read()
        if not ret: continue

        # Run detection
        results = model(frame, stream=True, conf=0.20)

        for r in results:
            # Filter detections to ONLY show the food IDs listed above
            # This prevents it from labeling your fridge as a 'refrigerator'
            detections = []
            for box in r.boxes:
                class_id = int(box.cls[0])
                if class_id in FOOD_IDS:
                    detections.append(model.names[class_id])
            
            # Draw the boxes
            annotated_frame = r.plot() 

            # Log once per second
            if time.time() - last_log_time >= 1.0:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                if detections:
                    # Create a summary: "2 apples, 1 bottle"
                    summary = ", ".join([f"{detections.count(x)} {x}" for x in set(detections)])
                    log_entry = f"[{timestamp}] In Fridge: {summary}"
                    print(log_entry)
                    with open(LOG_FILE, "a") as f:
                        f.write(log_entry + "\n")
                last_log_time = time.time()

        cv2.imshow("Multi-Object Fridge Monitor", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_multi_food_monitor()
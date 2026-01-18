import cv2
import time
from ultralytics import YOLO

# --- CONFIGURATION ---
STREAM_URL = "http://172.20.10.2:81/stream"
LOG_FILE = "fridge_inventory.log"

# --- ML SETUP ---
print("Loading Smart Food Model (YOLOv8m)...")
# Using the 'medium' model for better accuracy with items like corn/carrots
model = YOLO('yolov8m.pt') 

# Your specific list mapped to the closest categories the model knows
# Note: Standard YOLO lacks 'corn' and 'cabbage', so it may label them as 'broccoli' or 'vegetable'
CORE_FOODS = ['banana', 'carrot', 'hot dog', 'apple', 'orange', 'broccoli', 'pizza', 'sandwich', 'cake']
# 'sandwich' often covers burgers; 'broccoli' often covers cabbage/corn in general models.

def run_fridge_monitor():
    cap = cv2.VideoCapture(STREAM_URL)
    last_log_time = 0

    print(f"Monitoring... Logging to {LOG_FILE}")

    while True:
        ret, frame = cap.read()
        if not ret: continue

        # Run detection with a slightly lower confidence to catch smaller items
        results = model(frame, stream=True, conf=0.25)

        for r in results:
            detections = []
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                
                # Check if it's a food-related item
                # This includes your list AND common extras like bottles/cups
                if label in CORE_FOODS or label in ['bottle', 'cup', 'bowl', 'donut']:
                    detections.append(label)
            
            # Draw boxes on the frame
            annotated_frame = r.plot() 

            # Log to console and file every 1 second
            if time.time() - last_log_time >= 1.0:
                timestamp = time.strftime("%H:%M:%S")
                if detections:
                    # Count occurrences: "2 banana, 1 hot dog"
                    counts = {x: detections.count(x) for x in set(detections)}
                    summary = ", ".join([f"{count} {name}" for name, count in counts.items()])
                    
                    output = f"[{timestamp}] Seen: {summary}"
                    print(output)
                    with open(LOG_FILE, "a") as f:
                        f.write(output + "\n")
                else:
                    print(f"[{timestamp}] Scanning... (No food detected)")
                
                last_log_time = time.time()

        cv2.imshow("Fridge Monitor (Core Food Focus)", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_fridge_monitor()
import cv2
import torch
import requests
import time
import numpy as np
from ultralytics import YOLO
from io import BytesIO
from PIL import Image

# --- CONFIGURATION ---
ESP32_IP = "172.20.10.2"
STREAM_URL = f"http://{ESP32_IP}:81/stream"
CAPTURE_URL = f"http://{ESP32_IP}/capture"
MOTION_THRESHOLD = 400000 

# --- ML SETUP (YOLOv8) ---
print("Loading YOLOv8 Model...")
# 'yolov8n.pt' is the 'nano' version - fast enough to run on your CPU
model = YOLO('yolov8n.pt') 

# ImageNet/COCO food-related classes for filtering
FOOD_CLASSES = ['apple', 'banana', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'bottle']

def get_fridge_inventory():
    try:
        resp = requests.get(CAPTURE_URL, timeout=5)
        img = Image.open(BytesIO(resp.content))
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # SAVE THE IMAGE for you to inspect manually
        cv2.imwrite("debug_capture.jpg", img_cv)
        
        # LOWER THE CONFIDENCE: We tell YOLO to be "braver" (0.10 instead of 0.25)
        results = model(img_cv, conf=0.10, verbose=True)
        
        found_items = []
        for r in results:
            # This prints EVERY object YOLO sees to your console, even if not food
            print(f"DEBUG: YOLO found raw classes: {[model.names[int(b.cls[0])] for b in r.boxes]}")
            
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                found_items.append(label)
        
        return found_items, results[0].plot()
    except Exception as e:
        print(f"Capture failed: {e}")
        return [], None

# --- MAIN LOOP ---
def run_fridge_monitor():
    cap = cv2.VideoCapture(STREAM_URL)
    last_frame = None
    state = "PASSIVE"
    
    print(f"System Ready. Current State: {state}")

    while True:
        ret, frame = cap.read()
        if not ret: continue

        # 1. Motion Detection Logic
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if last_frame is None:
            last_frame = gray
            continue

        delta = cv2.absdiff(last_frame, gray)
        motion_level = np.sum(cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1])

        # 2. State Machine
        if state == "PASSIVE" and motion_level > MOTION_THRESHOLD:
            state = "MOTION"
            print("\n[EVENT] Door opened/Motion detected.")
        
        elif state == "MOTION" and motion_level < (MOTION_THRESHOLD / 2):
            print("[EVENT] Settle period... capturing final inventory.")
            time.sleep(1.5) 
            
            items, annotated_img = get_fridge_inventory()
            
            if items:
                print(f">>> FRIDGE CONTENTS: {items}")
                # Show the "Beauty Shot" with boxes for 3 seconds
                if annotated_img is not None:
                    cv2.imshow("Detected Items", annotated_img)
                    cv2.waitKey(3000) 
            else:
                print(">>> FRIDGE LOG: No food recognized.")
                
            state = "PASSIVE"
            print(f"Returning to {state}...\n")

        last_frame = gray
        cv2.imshow("Live Fridge Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

run_fridge_monitor()
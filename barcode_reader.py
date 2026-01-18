import cv2
import threading
import queue
import time
import requests
import os
import numpy as np
from google import genai
from google.genai import types

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyBFwUxAkepnIV1y26HdT5UVZBtI5DOEXkc"
STREAM_URL = "http://10.19.134.188:81/stream"

# Thresholds
FOCUS_THRESHOLD = 50.0      # Sharpness
STABILITY_THRESHOLD = 40.0   # Lower is more still
STABILITY_DURATION = 3.0    # Must be still for 3 seconds
COOLDOWN_DURATION = 3.0     # Wait 3 seconds after a success
MIN_PROXIMITY_SCORE = 20.0  # Ignore background

SAVE_DIR = "captured_barcodes"
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-2.0-flash"

class FreshFrameReader:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.q = queue.Queue(maxsize=1)
        self.stopped = False
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret: break
            if not self.q.empty():
                try: self.q.get_nowait()
                except queue.Empty: pass
            self.q.put(frame)

    def get_frame(self): return self.q.get()
    def stop(self): self.stopped = True

def lookup_food(barcode):
    """Searches Open Food Facts for the product details."""
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                p = data["product"]
                return f"{p.get('product_name', 'Unknown')} [{p.get('brands', 'No Brand')}]"
        return "Product Not Found"
    except Exception:
        return "API Error"

# --- GLOBAL TRACKING ---
reader = FreshFrameReader(STREAM_URL)
prev_gray = None
stable_start_time = None
last_capture_time = 0

print(f"System Initialized. Waiting for object...")

try:
    while True:
        frame = reader.get_frame()
        if frame is None: continue
        
        current_time = time.time()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Calculate Metrics
        focus = cv2.Laplacian(gray, cv2.CV_64F).var()
        motion = 0
        if prev_gray is not None:
            motion = np.mean(cv2.absdiff(gray, prev_gray))
        prev_gray = gray.copy()

        # 2. Check Conditions
        is_cooldown = (current_time - last_capture_time) < COOLDOWN_DURATION
        is_near = focus > MIN_PROXIMITY_SCORE 
        is_sharp = focus >= FOCUS_THRESHOLD
        is_still = motion <= STABILITY_THRESHOLD

        # 3. Handle Stability Timer
        if is_near and is_sharp and is_still and not is_cooldown:
            if stable_start_time is None:
                stable_start_time = current_time
            hold_duration = current_time - stable_start_time
        else:
            stable_start_time = None
            hold_duration = 0

        # --- UI OVERLAY ---
        overlay_color = (0, 0, 255) # Red
        if is_cooldown:
            status_txt = f"COOLDOWN ({int(COOLDOWN_DURATION - (current_time-last_capture_time))}s)"
        elif not is_near:
            status_txt = "PASSIVE - WAITING FOR OBJECT"
        elif not is_sharp:
            status_txt = "ADJUST FOCUS"
        elif not is_still:
            status_txt = "HOLD STILL"
        else:
            overlay_color = (0, 255, 255) # Yellow
            status_txt = f"HOLDING... {hold_duration:.1f}/3.0s"
            if hold_duration >= STABILITY_DURATION:
                overlay_color = (0, 255, 0) # Green
                status_txt = "CAPTURING!"

        cv2.putText(frame, f"Focus: {int(focus)} | Motion: {motion:.1f}", (20, 30), 1, 1.2, (255,255,255), 2)
        cv2.putText(frame, status_txt, (20, 70), 1, 1.8, overlay_color, 3)

        # 4. TRIGGER CAPTURE
        if hold_duration >= STABILITY_DURATION:
            cv2.rectangle(frame, (0,0), (frame.shape[1], frame.shape[0]), (255, 0, 0), 20)
            cv2.imshow("Smart Scanner", frame)
            cv2.waitKey(1)

            success, buffer = cv2.imencode('.jpg', frame)
            try:
                # Gemini identification
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=["Read the numbers just below the barcode. return only the standard 12 north american digits without any extra text. The leading number will always be a 0, followed by 11 digits. Ensure you return exactly 12 digits.", 
                              types.Part.from_bytes(data=buffer.tobytes(), mime_type='image/jpeg')]
                )
                barcode = "".join(filter(str.isdigit, response.text))
                
                if barcode:
                    # Database Identification
                    product_info = lookup_food(barcode)
                    
                    filename = f"{SAVE_DIR}/{barcode}_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    
                    # Display Results
                    print(f"Captured: {barcode} | ID: {product_info}")
                    cv2.putText(frame, f"CODE: {barcode}", (20, 130), 1, 2, (255, 255, 255), 2)
                    cv2.putText(frame, product_info[:35], (20, 170), 1, 1.5, (0, 255, 0), 2)
                    
                    last_capture_time = time.time()
                    stable_start_time = None
                    cv2.imshow("Smart Scanner", frame)
                    cv2.waitKey(3000) # Freeze for 3s as requested
            except Exception as e:
                print(f"Error: {e}")
                last_capture_time = time.time()

        cv2.imshow("Smart Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

finally:
    reader.stop()
    cv2.destroyAllWindows()
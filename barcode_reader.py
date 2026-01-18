import cv2
import numpy as np
import requests
from pyzbar.pyzbar import decode
import datetime
import time

# --- CONFIGURATION ---
STREAM_URL = "http://10.19.134.188:81/stream"
LOG_FILE = "barcode_log_file.txt"

def log_to_file(code, info):
    """Writes the results to the console and the log file with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] | Barcode: {code} | Product: {info}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def fetch_product_details(upc):
    """Searches the Open Food Facts database for the product name."""
    api_url = f"https://world.openfoodfacts.org/api/v2/product/{upc}.json"
    try:
        r = requests.get(api_url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == 1:
                product = data["product"]
                name = product.get('product_name', 'Unknown Name')
                brand = product.get('brands', 'No Brand')
                return f"{name} [{brand}]"
        return "Product Not Found in Database"
    except Exception:
        return "API Lookup Error"

# Setup session for the MJPEG stream
session = requests.Session()
try:
    print(f"Connecting to MJPEG stream: {STREAM_URL}...")
    stream = session.get(STREAM_URL, stream=True, timeout=10)
except Exception as e:
    print(f"FAILED TO CONNECT: {e}")
    exit()

bytes_data = bytes()
last_logged_code = None

print("Monitor Active. Press 'q' in the video window to exit.")
print("---")

try:
    for chunk in stream.iter_content(chunk_size=1024):
        bytes_data += chunk
        
        # Identify the start and end of a JPEG frame
        a = bytes_data.find(b'\xff\xd8')
        b = bytes_data.find(b'\xff\xd9')
        
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            
            if not jpg:
                continue

            try:
                # Decode the raw bytes into an image
                nparr = np.frombuffer(jpg, dtype=np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # OPTIONAL: Convert to grayscale to improve detection rate
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # SCAN: Attempt to find barcodes
                    detected_barcodes = decode(gray_frame)
                    
                    for barcode in detected_barcodes:
                        # Draw a bounding box around the barcode for visual feedback
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        
                        code_data = barcode.data.decode('utf-8')
                        
                        # Only log if it's a new scan (prevents spamming the log)
                        if code_data != last_logged_code:
                            product_info = fetch_product_details(code_data)
                            log_to_file(code_data, product_info)
                            last_logged_code = code_data
                    
                    # Display the live feed with the green tracking boxes
                    cv2.imshow('Barcode Scanner Diagnostic', frame)
                    
                # Exit loop if user presses 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            except Exception as e:
                # If a frame is corrupt, just skip it and move to the next
                continue

except KeyboardInterrupt:
    print("\nUser stopped the monitor.")
finally:
    cv2.destroyAllWindows()
    print(f"Session ended. Check {LOG_FILE} for results.")
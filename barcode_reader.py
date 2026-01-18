import cv2
from pyzbar.pyzbar import decode
import requests

def extract_and_lookup(image_path):
    # Load the image
    img = cv2.imread(image_path)
    
    # 1. EXTRACT: Find barcodes in the image
    barcodes = decode(img)
    
    if not barcodes:
        return "No barcode detected. Check lighting and focus!"

    for barcode in barcodes:
        # Clean the barcode data
        code_number = barcode.data.decode('utf-8')
        print(f"Detected Barcode: {code_number}")

        # 2. SEARCH: Look up on Open Food Facts (Free API)
        url = f"https://world.openfoodfacts.org/api/v2/product/{code_number}.json"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1:
                product = data['product']
                name = product.get('product_name', 'Unknown Product')
                brand = product.get('brands', 'Unknown Brand')
                return f"Found it! {name} by {brand}"
            else:
                return "Barcode found, but not in the grocery catalog."
        else:
            return "Connection error to the product database."

# Example usage:
print(extract_and_lookup("barcode-images/Screenshot 2026-01-18 040811.png"))
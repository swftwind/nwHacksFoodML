import requests
import json

def test_barcode_lookup(barcode_digit_string):
    """
    Simulates the identification step of your scanner.
    Open Food Facts API doesn't require an API Key for GET requests,
    but it does require a descriptive 'User-Agent'.
    """
    
    # 1. Normalize the barcode
    # North American UPCs are often 12 digits, but OFF likes 13-digit EAN format.
    # We pad with a leading zero if it's 12 digits.
    test_code = barcode_digit_string.strip()
    if len(test_code) == 12:
        test_code = "0" + test_code
        
    print(f"--- Testing Barcode: {test_code} ---")
    
    # 2. Setup the Request
    url = f"https://world.openfoodfacts.org/api/v2/product/{test_code}.json"
    headers = {
        'User-Agent': 'MySmartScanner/1.0 (Contact: your@email.com)' 
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("status") == 1:
                product = data.get("product", {})
                name = product.get("product_name", "Unknown Name")
                brand = product.get("brands", "No Brand Found")
                category = product.get("categories", "No Category")
                
                print(f"✅ SUCCESS: Product Found!")
                print(f"   Name:  {name}")
                print(f"   Brand: {brand}")
                print(f"   Type:  {category.split(',')[0]}") # Show main category
            else:
                print(f"❌ NOT FOUND: {data.get('status_verbose', 'Unknown error')}")
                print("   Tip: Try a common item like a soda or snack.")
        else:
            print(f"⚠️ SERVER ERROR: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"‼️ CONNECTION ERROR: {e}")

# --- RUN THE TEST ---
# Standard 12-digit UPC for Oreos: 044000032029
# test_barcode_lookup("034856003762") 

# Now try entering one from your jerky package:
green_water = "068493427186"
test_barcode_lookup(green_water)

blue_water = "096619321841"
test_barcode_lookup(blue_water)
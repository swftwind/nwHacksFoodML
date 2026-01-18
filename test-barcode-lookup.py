import requests
import json

def lookup_barcode(barcode_number):
    """
    Takes a string of numbers and finds the product in the 
    Open Food Facts database.
    """
    # Clean the input (remove spaces or dashes)
    barcode_number = str(barcode_number).strip().replace(" ", "").replace("-", "")
    
    print(f"Searching for: {barcode_number}...")
    
    # Open Food Facts API Endpoint
    # We use 'world' to ensure it searches the global database
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode_number}.json"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Status 1 means the product was found
            if data.get("status") == 1:
                product = data["product"]
                
                # Extract key details
                name = product.get("product_name", "Unknown Name")
                brand = product.get("brands", "Unknown Brand")
                quantity = product.get("quantity", "Unknown Weight")
                ingredients = product.get("ingredients_text", "No ingredients listed.")
                
                print("-" * 30)
                print(f"SUCCESS: Product Found!")
                print(f"Name:     {name}")
                print(f"Brand:    {brand}")
                print(f"Size:     {quantity}")
                print(f"Ingredients: {ingredients[:100]}...") # Truncated for readability
                print("-" * 30)
                
            else:
                print(f"Result: Barcode {barcode_number} not found in this database.")
        else:
            print(f"Error: API returned status code {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")

# --- EXECUTION ---
# Using the numbers you provided from the Soo Jerky package
my_barcode = "060410020197"
lookup_barcode(my_barcode)
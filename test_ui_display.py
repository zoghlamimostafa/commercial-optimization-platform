import requests
import json
import sys

# Test the UI display of the delivery optimization page

def test_delivery_optimize_api(commercial_code="1300", date="2023-06-15", with_products=False):
    """Test the delivery optimization API endpoint"""
    url = 'http://127.0.0.1:5000/api/delivery/optimize'
    
    # Create test data
    data = {
        "commercial_code": commercial_code,
        "delivery_date": date
    }
    
    # Add product filter if requested
    if with_products:
        data["product_codes"] = ["NP010301", "NP010302"]
        print(f"Testing with product filter: {data['product_codes']}")
    
    # Make the request
    try:
        print(f"Sending request to {url} with data: {json.dumps(data, indent=2)}")
        response = requests.post(url, json=data)
        
        print(f"Status code: {response.status_code}")
        
        # Check response format
        if response.status_code == 200:
            result = response.json()
            
            # Check if packing list is present and has items
            if 'packing_list' in result and result['packing_list']:
                print(f"✅ Packing list present with {len(result['packing_list'])} items")
            else:
                print("❌ Packing list is missing or empty")
            
            # Check if route is present and has items
            if 'route' in result and result['route']:
                print(f"✅ Route present with {len(result['route'])} stops")
                
                # Check if predicted products are present in route stops
                has_predictions = False
                for stop in result['route']:
                    if 'predicted_products' in stop and stop['predicted_products']:
                        has_predictions = True
                        print(f"✅ Found predictions for stop {stop['client_code']} ({stop['client_name']})")
                        break
                
                if not has_predictions:
                    print("❌ No stops have predicted products")
            else:
                print("❌ Route is missing or empty")
                
            # Return a summarized version of the response for debugging
            summary = {
                "commercial_name": result.get("commercial_name"),
                "delivery_date": result.get("delivery_date"),
                "total_distance": result.get("total_distance"),
                "route_count": len(result.get("route", [])),
                "packing_list_count": len(result.get("packing_list", {})),
                "has_predictions": has_predictions
            }
            print(f"\nResponse summary: {json.dumps(summary, indent=2)}")
            
        else:
            print(f"❌ Request failed with status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error during request: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    commercial_code = "1300"  # Default commercial code
    date = "2023-06-15"  # Default date
    with_products = False
    
    # Parse arguments
    if len(sys.argv) > 1:
        commercial_code = sys.argv[1]
    if len(sys.argv) > 2:
        date = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3].lower() in ["true", "1", "yes"]:
        with_products = True
    
    # Run test
    test_delivery_optimize_api(commercial_code, date, with_products)

import requests
import json

def test_delivery_optimization_api():
    try:
        # Test data for the API call
        test_data = {
            "commercial_code": "1300",  # Use a valid commercial code from your database
            "delivery_date": "2023-06-15"
        }
        
        # Try to call the delivery optimization API
        response = requests.post(
            'http://127.0.0.1:5000/api/delivery/optimize',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! The API returned a valid response.")
            # Print a summary of the response
            data = response.json()
            print(f"\nDelivery plan for commercial {data.get('commercial_code')}:")
            print(f"Delivery date: {data.get('delivery_date')}")
            print(f"Total distance: {data.get('total_distance')} km")
            print(f"Number of stops: {len(data.get('route', []))}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_delivery_optimization_api()

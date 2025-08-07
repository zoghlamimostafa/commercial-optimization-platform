import requests

def test_delivery_optimization():
    try:
        # Try to access the delivery_optimization page
        response = requests.get('http://127.0.0.1:5000/delivery_optimization')
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success! The page is accessible.")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_delivery_optimization()

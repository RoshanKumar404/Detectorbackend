import requests
import os

def test_prediction(image_path):
    url = "http://127.0.0.1:5000/api/predict/"
    
    if not os.path.exists(image_path):
        print(f"Error: File not found at {image_path}")
        return

    with open(image_path, 'rb') as img:
        files = {'image': img}
        try:
            print(f"Sending {image_path} to {url}...")
            response = requests.post(url, files=files)
            print(f"Status Code: {response.status_code}")
            print("Response JSON:")
            print(response.json())
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    # Test with a waterlogged image
    test_image = "dataset/train/waterlogged/WhatsApp Image 2026-03-24 at 10.00.41 PM.jpeg"
    test_prediction(test_image)

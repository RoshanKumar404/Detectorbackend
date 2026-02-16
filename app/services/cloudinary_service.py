import cloudinary
import cloudinary.uploader
import os

class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key = os.getenv('CLOUDINARY_API_KEY'),
            api_secret = os.getenv('CLOUDINARY_API_SECRET')
        )

    def upload_image(self, file, folder="reports"):
        try:
            upload_result = cloudinary.uploader.upload(file, folder=folder)
            return upload_result.get('secure_url')
        except Exception as e:
            print(f"Cloudinary upload error: {e}")
            return None

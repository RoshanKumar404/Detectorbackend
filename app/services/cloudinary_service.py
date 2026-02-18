import cloudinary
import cloudinary.uploader
import os

class CloudinaryService:
    def __init__(self):
        cloudinary_url = os.getenv('CLOUDINARY_URL')
        if cloudinary_url:
            cloudinary.config(cloudinary_url=cloudinary_url)
        else:
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
            return None

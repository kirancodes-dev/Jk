import os
import shutil
import uuid
from typing import Optional
from fastapi import UploadFile
from backend.app.core.config import settings

class StorageService:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, subfolder: str = "media") -> str:
        target_dir = os.path.join(self.upload_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        
        # Unique filename
        ext = os.path.splitext(file.filename)[1] if file.filename else ".bin"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(target_dir, unique_name)
        
        if self.storage_type == "s3" and settings.AWS_ACCESS_KEY_ID:
            try:
                # Pluggable S3 client
                import boto3
                s3 = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                s3.upload_fileobj(file.file, settings.S3_BUCKET_NAME, f"{subfolder}/{unique_name}")
                return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{subfolder}/{unique_name}"
            except Exception as e:
                # Graceful fallback to local storage
                pass

        # Local storage fallback
        file.file.seek(0)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return f"/uploads/{subfolder}/{unique_name}"

storage_service = StorageService()

# app/services/storage_service.py
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from typing import Optional, Dict, BinaryIO
from fastapi import HTTPException, UploadFile
import mimetypes
import uuid
from app.config import settings
from app.utils.appwrite_client import get_client


class StorageService:
    def __init__(self):
        self.client = get_client()
        self.storage = Storage(self.client)
        self.bucket_id = settings.APPWRITE_BUCKET_ID

    def _generate_file_url(self, file_id: str) -> str:
        """
        Generates public URL for file access with additional query parameters.
        """
        project_id = settings.APPWRITE_PROJECT_ID  # Replace with your Appwrite project ID
        return (
            f"{settings.APPWRITE_ENDPOINT}/storage/buckets/{self.bucket_id}/files/{file_id}/view"
            f"?project={project_id}&mode=admin"
        )


    async def upload_image(self, file: UploadFile) -> Dict[str, str]:
        try:
            # Validate file type
            if not self._is_valid_image(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only images (jpg, jpeg, png) are allowed."
                )

            # Generate unique ID
            unique_id = str(uuid.uuid4()).replace('-', '')[:36]
            
            # Read file content
            file_data = await file.read()

            # Upload to Appwrite
            result = self.storage.create_file(
                bucket_id=self.bucket_id,
                file_id=unique_id,
                file=InputFile.from_bytes(
                    file_data,
                    file.filename,
                    mime_type=file.content_type  # Add mime type
                ),
                permissions=['read("any")']
            )

            print(f"File uploaded with mime type: {file.content_type}")  # Debug print

            return {
                "file_id": result['$id'],
                "file_url": self._generate_file_url(result['$id'])
            }

        except Exception as e:
            print(f"Upload error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading file: {str(e)}"
            )

    def _is_valid_image(self, filename: str) -> bool:
        """
        Validates image file type.
        """
        allowed_types = ['.jpg', '.jpeg', '.png']  # Removed gif, added explicit types
        return any(filename.lower().endswith(ext) for ext in allowed_types)

    async def delete_image(self, file_id: str) -> bool:
        """
        Deletes an image from storage.
        """
        try:
            await self.storage.delete_file(
                bucket_id=self.bucket_id,
                file_id=file_id
            )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting file: {str(e)}"
            )

    async def get_image_url(self, file_id: str) -> str:
        """
        Gets the URL for an image.
        """
        try:
            file = await self.storage.get_file(
                bucket_id=self.bucket_id,
                file_id=file_id
            )
            return self._generate_file_url(file_id)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail="Image not found"
            )

    def _is_valid_image(self, filename: str) -> bool:
        """
        Validates image file type.
        """
        allowed_types = ['.jpg', '.jpeg', '.png', '.gif']
        return any(filename.lower().endswith(ext) for ext in allowed_types)

    async def create_thumbnail(self, file_id: str) -> Optional[str]:
        """
        Creates a thumbnail version of the image.
        """
        try:
            # Get original file
            original = await self.storage.get_file(
                bucket_id=self.bucket_id,
                file_id=file_id
            )

            # Generate thumbnail ID
            thumbnail_id = f"thumb_{file_id}"

            # Create preview
            # Note: Appwrite handles image transformations
            preview_url = f"{settings.APPWRITE_ENDPOINT}/storage/buckets/{self.bucket_id}/files/{file_id}/preview?width=200&height=200"

            return preview_url

        except Exception as e:
            return None

    async def cleanup_old_files(self, days: int = 30) -> None:
        """
        Cleans up files older than specified days.
        """
        try:
            files = await self.storage.list_files(
                bucket_id=self.bucket_id
            )

            for file in files['files']:
                # Add cleanup logic based on file creation date
                pass

        except Exception as e:
            print(f"Error in cleanup: {str(e)}")

    async def get_storage_stats(self) -> Dict[str, int]:
        """
        Gets storage usage statistics.
        """
        try:
            files = await self.storage.list_files(
                bucket_id=self.bucket_id
            )

            total_size = sum(file['size'] for file in files['files'])
            file_count = len(files['files'])

            return {
                "total_size_bytes": total_size,
                "file_count": file_count
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Error fetching storage stats"
            )

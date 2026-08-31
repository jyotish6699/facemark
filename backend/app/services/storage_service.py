import os
import uuid
import hashlib
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
from app.config import settings

class StorageService:
    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    async def save_upload_image(
        file: UploadFile, 
        destination_dir: Path
    ) -> Tuple[str, str, int, str]:
        """
        Validates and saves an uploaded image file safely.
        Returns (relative_storage_key, filename, file_size_bytes, sha256_hash).
        """
        # Validate MIME type from content-type header
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file.content_type}'. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )

        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # Validate image decoding via Pillow to prevent arbitrary file upload vulnerabilities
        try:
            image = Image.open(io.BytesIO(content))
            image.verify() # Verify image integrity
            # Reopen to check dimensions (verify closes the file)
            image = Image.open(io.BytesIO(content))
            width, height = image.size
            if width < 50 or height < 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions too small to detect faces accurately (minimum 50x50)."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image content: {str(e)}"
            )

        # Calculate content hash
        file_hash = StorageService.calculate_file_hash(content)

        # Generate safe storage filename
        extension = Path(file.filename or "image.jpg").suffix.lower()
        if not extension or extension not in [".jpg", ".jpeg", ".png", ".webp"]:
            extension = ".jpg"
            
        safe_filename = f"{uuid.uuid4()}{extension}"
        destination_dir.mkdir(parents=True, exist_ok=True)
        file_path = destination_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative storage key
        storage_key = str(file_path.relative_to(settings.BASE_DIR)).replace("\\", "/")
        return storage_key, file.filename or safe_filename, file_size, file_hash

    @staticmethod
    def get_absolute_path(storage_key: str) -> Path:
        """Resolve storage key to absolute Path."""
        return settings.BASE_DIR / storage_key

storage_service = StorageService()

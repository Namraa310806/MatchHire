import os
import uuid


class ResumeStorageService:
    """
    Service for handling resume file storage.
    Designed for future S3 migration - storage logic is abstracted here.
    """
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        Generate a unique filename for storage.
        Never trust the uploaded filename.
        
        Args:
            original_filename: The original filename from the upload
            
        Returns:
            A unique filename with preserved extension
        """
        # Get the file extension
        _, ext = os.path.splitext(original_filename.lower())
        
        # Generate a unique identifier
        unique_id = str(uuid.uuid4())
        
        # Combine to create unique filename
        return f"{unique_id}{ext}"

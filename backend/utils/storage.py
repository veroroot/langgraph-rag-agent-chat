"""File storage abstraction (local or S3)."""
import os
import shutil
from pathlib import Path
from typing import Optional
from backend.core.config import settings
from backend.core.logging import logger


class Storage:
    """Storage abstraction for file operations."""
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        if self.storage_type == "local":
            self.base_path = Path(settings.UPLOAD_DIR)
            self.base_path.mkdir(parents=True, exist_ok=True)
        elif self.storage_type == "s3":
            # TODO: Initialize S3 client
            logger.warning("S3 storage not yet implemented")
    
    def save_file(self, file_content: bytes, file_path: str, user_id: int) -> str:
        """Save file to storage.
        
        Args:
            file_content: File content as bytes
            file_path: Relative path where file should be saved
            user_id: User ID for organizing files
        
        Returns:
            Full path where file was saved
        """
        if self.storage_type == "local":
            return self._save_local(file_content, file_path, user_id)
        elif self.storage_type == "s3":
            # TODO: Implement S3 save
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unknown storage type: {self.storage_type}")
    
    def _save_local(self, file_content: bytes, file_path: str, user_id: int) -> str:
        """Save file to local filesystem."""
        user_dir = self.base_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        full_path = user_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        return str(full_path)
    
    def get_file(self, file_path: str) -> bytes:
        """Get file content from storage.
        
        Args:
            file_path: Path to file
        
        Returns:
            File content as bytes
        """
        if self.storage_type == "local":
            with open(file_path, "rb") as f:
                return f.read()
        elif self.storage_type == "s3":
            # TODO: Implement S3 get
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unknown storage type: {self.storage_type}")
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if deleted, False otherwise
        """
        if self.storage_type == "local":
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                return False
        elif self.storage_type == "s3":
            # TODO: Implement S3 delete
            raise NotImplementedError("S3 storage not yet implemented")
        else:
            raise ValueError(f"Unknown storage type: {self.storage_type}")


storage = Storage()




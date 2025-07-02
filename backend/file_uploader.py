"""
File uploader utility for uploading CSV files to OpenAI.
Called on startup; uploads each CSV once & returns file_id.
"""

from openai import OpenAI
import os
import pathlib
import json
import logging

logger = logging.getLogger(__name__)

def upload_if_needed(path: str) -> str:
    """
    Upload a CSV file to OpenAI if not already uploaded.
    
    Args:
        path: Path to the CSV file
        
    Returns:
        file_id: OpenAI file ID for the uploaded file
    """
    client = OpenAI()
    meta_path = pathlib.Path(path + ".meta.json")
    
    # Check if file was already uploaded
    if meta_path.exists():
        try:
            meta_data = json.loads(meta_path.read_text())
            logger.info(f"Using existing upload for {path}: {meta_data['file_id']}")
            return meta_data["file_id"]
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Invalid meta file for {path}, re-uploading...")

    # Upload the file
    logger.info(f"Uploading {path} to OpenAI...")
    with open(path, "rb") as f:
        file = client.files.create(file=f, purpose="assistants")
    
    # Save metadata
    meta_path.write_text(json.dumps({"file_id": file.id, "filename": os.path.basename(path)}))
    logger.info(f"Successfully uploaded {path} with file_id: {file.id}")
    
    return file.id 
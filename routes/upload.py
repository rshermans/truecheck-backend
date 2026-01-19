import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import uuid
from pathlib import Path

from routes.auth import verify_token

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "video": {".mp4", ".webm", ".mov"},
    "pdf": {".pdf"}
}

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    type: str = "image", # image, video, pdf
    user: dict = Depends(verify_token)
):
    """Upload a file and return its URL"""
    
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if type in ALLOWED_EXTENSIONS and ext not in ALLOWED_EXTENSIONS[type]:
        raise HTTPException(status_code=400, detail=f"Invalid file type for {type}. Allowed: {ALLOWED_EXTENSIONS[type]}")
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / filename
    
    try:
        # Use async read to avoid blocking event loop
        contents = await file.read()
        with file_path.open("wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
    file_size_bytes = file_path.stat().st_size
    
    # Format size
    if file_size_bytes < 1024:
        size_str = f"{file_size_bytes} B"
    elif file_size_bytes < 1024 * 1024:
        size_str = f"{file_size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"

    # Return URL (relative to server root, handled by StaticFiles)
    # Assuming static files are mounted at /static
    return {"url": f"/static/uploads/{filename}", "size": size_str}

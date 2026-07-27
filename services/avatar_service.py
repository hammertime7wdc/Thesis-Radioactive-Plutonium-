"""
Cloudinary avatar upload service. Extracted out of ui_account.py so the
Cloudinary config and upload logic live alongside the other service
modules (session_manager, supabase_client, email_service, etc.) instead
of inside a UI screen.
"""

import os
import uuid

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not all([CLOUD_NAME, API_KEY, API_SECRET]):
    print("WARNING: Cloudinary credentials not found in .env file")
    print("Required: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
)


def is_configured() -> bool:
    return all([CLOUD_NAME, API_KEY, API_SECRET])


def upload_avatar_image(file_path: str, user_id: str) -> str:
    """
    Upload an avatar image to Cloudinary, cropped/resized to a 200x200
    square focused on the face. Returns the resulting secure URL.

    Raises Exception with a user-facing message on failure, so callers can
    show ex.args[0] (or str(ex)) directly in the UI.
    """
    if not is_configured():
        raise Exception("Cloudinary not configured. Check .env file.")

    upload_result = cloudinary.uploader.upload(
        file_path,
        folder="avatars",
        public_id=f"{user_id}_{uuid.uuid4().hex}",
        overwrite=True,
        resource_type="image",
        transformation=[{"width": 200, "height": 200, "crop": "fill", "gravity": "face"}],
    )

    avatar_url = upload_result.get("secure_url")
    if not avatar_url:
        raise Exception("No URL returned from Cloudinary")

    return avatar_url

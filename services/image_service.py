"""
THABZO EVENTS - Image Service
"""
import os
import uuid
from PIL import Image
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def get_upload_folder(subdir=''):
    """Get the upload folder path"""
    base_folder = current_app.config.get('UPLOAD_FOLDER')
    if not base_folder:
        base_folder = os.path.join(current_app.root_path, 'static', 'uploads')

    if subdir:
        folder = os.path.join(base_folder, subdir)
    else:
        folder = base_folder

    # Create directory if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    return folder


def save_image(file, subdir='gallery', resize=None):
    """Save an image file and return the filename"""
    if not file or not file.filename:
        return None

    try:
        # Get file extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'

        # Generate unique filename
        filename = f"{uuid.uuid4().hex[:12]}.{ext}"

        # Get upload folder
        upload_folder = get_upload_folder(subdir)
        filepath = os.path.join(upload_folder, filename)

        # Save file
        file.save(filepath)

        # Resize if needed
        if resize:
            try:
                img = Image.open(filepath)
                img.thumbnail(resize, Image.Resampling.LANCZOS)
                img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                logger.warning(f"Resize failed: {e}")

        logger.info(f"Image saved: {filename} in {subdir}")
        return filename

    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None


def delete_image(filename, subdir='gallery'):
    """Delete an image file"""
    if not filename:
        return

    try:
        upload_folder = get_upload_folder(subdir)
        filepath = os.path.join(upload_folder, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Image deleted: {filename}")
        else:
            logger.warning(f"Image not found: {filename}")

    except Exception as e:
        logger.error(f"Error deleting image: {e}")


def get_image_url(filename, subdir='gallery'):
    """Get the URL for an image"""
    if not filename:
        return None
    return f"/static/uploads/{subdir}/{filename}"
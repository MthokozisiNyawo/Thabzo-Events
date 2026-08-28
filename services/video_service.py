"""
THABZO EVENTS - Video Service
Handles video upload, deletion, and management
"""
import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename


def get_upload_path(subdir=''):
    """Get the full upload path for a subdirectory"""
    base_path = current_app.config.get('UPLOAD_FOLDER')

    if not base_path:
        # Fallback: construct path relative to app root
        base_path = os.path.join(current_app.root_path, 'static', 'uploads')

    if subdir:
        subdirs = current_app.config.get('UPLOAD_SUBDIRS', {})
        if subdir in subdirs:
            path = subdirs[subdir]
        else:
            path = os.path.join(base_path, subdir)
    else:
        path = base_path

    os.makedirs(path, exist_ok=True)
    return path


def get_file_extension(filename):
    """Get the file extension from a filename"""
    return os.path.splitext(filename)[1].lower()


def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving extension"""
    ext = get_file_extension(original_filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    secure_name = secure_filename(original_filename).replace(' ', '_')
    name_without_ext = os.path.splitext(secure_name)[0]
    # Truncate long names
    if len(name_without_ext) > 50:
        name_without_ext = name_without_ext[:50]
    return f"{name_without_ext}_{timestamp}_{unique_id}{ext}"


def is_allowed_video(filename):
    """Check if the file is an allowed video type"""
    allowed_extensions = current_app.config.get('ALLOWED_VIDEO_EXTENSIONS',
                                                {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'm4v', '3gp'})
    ext = get_file_extension(filename).lower().replace('.', '')
    return ext in allowed_extensions


def save_video(file, subdir='videos'):
    """Save a video file"""
    if not file or not file.filename:
        return None

    if not is_allowed_video(file.filename):
        current_app.logger.warning(f"Video type not allowed: {file.filename}")
        return None

    upload_path = get_upload_path(subdir)
    filename = generate_unique_filename(file.filename)
    filepath = os.path.join(upload_path, filename)

    try:
        file.save(filepath)
        current_app.logger.info(f"Video saved: {filepath}")
        print(f"✅ Video saved: {filepath}")
        return filename

    except Exception as e:
        current_app.logger.error(f"Error saving video: {str(e)}")
        print(f"❌ Error saving video: {str(e)}")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return None


def delete_video(filename, subdir='videos'):
    """Delete a video file"""
    if not filename:
        return False

    upload_path = get_upload_path(subdir)
    filepath = os.path.join(upload_path, filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info(f"Deleted video: {filepath}")
            return True
        else:
            current_app.logger.warning(f"Video not found: {filepath}")
            return False
    except Exception as e:
        current_app.logger.error(f"Error deleting video {filename}: {str(e)}")
        return False


def save_thumbnail(file, subdir='video-thumbnails'):
    """Save a thumbnail image for a video"""
    if not file or not file.filename:
        return None

    from thabzo.services.image_service import save_image
    return save_image(file, subdir=subdir, resize=(320, 180))


def delete_thumbnail(filename, subdir='video-thumbnails'):
    """Delete a thumbnail image"""
    if not filename:
        return False

    from thabzo.services.image_service import delete_image
    return delete_image(filename, subdir=subdir)


def get_video_url(filename, subdir='videos'):
    """Get the URL for a video file"""
    if not filename:
        return None
    # Return just the filename (not the full path)
    return filename
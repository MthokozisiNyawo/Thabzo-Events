"""
THABZO EVENTS - Gallery Routes
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from thabzo.models import GalleryImage, EventAlbum, db
import logging

gallery_bp = Blueprint('gallery', __name__)
logger = logging.getLogger(__name__)


@gallery_bp.route('/')
def gallery_index():
    """Gallery page - displays albums"""
    try:
        category = request.args.get('category')
        page = request.args.get('page', 1, type=int)
        per_page = 12

        query = EventAlbum.query.filter_by(is_active=True)

        if category and category != 'all':
            query = query.filter_by(event_type=category)

        albums = query.order_by(EventAlbum.display_order).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Get unique categories from albums
        categories = EventAlbum.query.filter_by(is_active=True).distinct(EventAlbum.event_type).all()
        category_list = [c.event_type for c in categories if c.event_type]

        return render_template('gallery.html',
                               albums=albums,
                               categories=category_list,
                               current_category=category,
                               pagination=True)
    except Exception as e:
        logger.error(f"Error in gallery_index: {str(e)}")
        flash('An error occurred loading the gallery.', 'danger')
        return render_template('gallery.html', albums=[], categories=[])


@gallery_bp.route('/album/<int:id>')
def album_detail(id):
    """Album detail page"""
    try:
        album = EventAlbum.query.get_or_404(id)
        images = GalleryImage.query.filter_by(album_id=id).order_by(GalleryImage.display_order).all()
        return render_template('gallery_detail.html', album=album, images=images)
    except Exception as e:
        logger.error(f"Error in album_detail for id {id}: {str(e)}")
        flash('Album not found.', 'danger')
        return redirect(url_for('gallery.gallery_index'))


@gallery_bp.route('/api/images')
def api_images():
    """JSON API for gallery images"""
    try:
        category = request.args.get('category')
        query = GalleryImage.query

        if category and category != 'all':
            query = query.filter_by(category=category)

        images = query.order_by(GalleryImage.display_order).all()

        return jsonify([{
            'id': img.id,
            'title': img.title,
            'description': img.description,
            'filename': img.filename,
            'filepath': img.filepath,
            'category': img.category,
            'category_display': img.get_category_display() if hasattr(img, 'get_category_display') else None,
            'is_featured': img.is_featured
        } for img in images])
    except Exception as e:
        logger.error(f"Error in api_images: {str(e)}")
        return jsonify({'error': str(e)}), 500


@gallery_bp.route('/api/categories')
def api_categories():
    """JSON API for gallery categories"""
    try:
        categories = EventAlbum.query.filter_by(is_active=True).distinct(EventAlbum.event_type).all()
        category_list = [{'value': c.event_type, 'label': c.event_type} for c in categories if c.event_type]
        return jsonify(category_list)
    except Exception as e:
        logger.error(f"Error in api_categories: {str(e)}")
        return jsonify({'error': str(e)}), 500
"""
THABZO EVENTS - REST API Routes
"""
from flask import Blueprint, jsonify, request, current_app
from thabzo.models import GalleryImage, Testimonial, Service, Inquiry, EventAlbum, db
from thabzo.services.email_service import send_inquiry_email
from thabzo.services.quote_service import QuoteService
from flask_login import login_required
from datetime import datetime, timedelta
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


# ==================== PUBLIC API ====================

@api_bp.route('/gallery', methods=['GET'])
def get_gallery():
    """Get gallery images"""
    category = request.args.get('category')
    limit = request.args.get('limit', default=50, type=int)

    query = GalleryImage.query
    if category:
        query = query.filter_by(category=category)

    images = query.order_by(GalleryImage.display_order).limit(limit).all()

    return jsonify([{
        'id': img.id,
        'title': img.title,
        'description': img.description,
        'filename': img.filename,
        'filepath': img.filepath,
        'category': img.category,
        'category_display': img.get_category_display(),
        'is_featured': img.is_featured,
        'url': f'/static/{img.filepath}'
    } for img in images])


@api_bp.route('/albums', methods=['GET'])
def get_albums():
    """Get all albums"""
    albums = EventAlbum.query.filter_by(is_active=True).order_by(EventAlbum.display_order).all()

    return jsonify([{
        'id': album.id,
        'name': album.name,
        'slug': album.slug,
        'description': album.description,
        'event_type': album.event_type,
        'category_display': album.get_category_display(),
        'cover_url': album.get_cover_url(),
        'image_count': len(album.images),
        'is_featured': album.is_featured
    } for album in albums])


@api_bp.route('/albums/<int:id>/images', methods=['GET'])
def get_album_images(id):
    """Get images in an album"""
    album = EventAlbum.query.get_or_404(id)
    images = GalleryImage.query.filter_by(album_id=id).order_by(GalleryImage.display_order).all()

    return jsonify([{
        'id': img.id,
        'title': img.title,
        'description': img.description,
        'filepath': img.filepath,
        'url': f'/static/{img.filepath}',
        'is_featured': img.is_featured
    } for img in images])


@api_bp.route('/testimonials', methods=['GET'])
def get_testimonials():
    """Get approved testimonials"""
    limit = request.args.get('limit', default=20, type=int)

    testimonials = Testimonial.query.filter_by(
        is_approved=True
    ).order_by(Testimonial.created_at.desc()).limit(limit).all()

    return jsonify([{
        'id': t.id,
        'client_name': t.client_name,
        'event_type': t.event_type,
        'content': t.content,
        'rating': t.rating,
        'created_at': t.created_at.isoformat() if t.created_at else None
    } for t in testimonials])


@api_bp.route('/services', methods=['GET'])
def get_services():
    """Get active services"""
    services = Service.query.filter_by(is_active=True).order_by(
        Service.display_order
    ).all()

    return jsonify([{
        'id': s.id,
        'name': s.name,
        'slug': s.slug,
        'description': s.description,
        'icon': s.icon,
        'starting_price': s.starting_price,
        'price_display': f'R{s.starting_price:,.2f}'.replace('.00', '') if s.starting_price else None
    } for s in services])


@api_bp.route('/estimate', methods=['POST'])
def get_estimate():
    """Get quick estimate"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        guest_count = data.get('guest_count')
        complexity = data.get('complexity', 'medium')

        if not event_type:
            return jsonify({'error': 'Event type is required'}), 400

        estimate = QuoteService.estimate_price(event_type, guest_count, complexity)
        price_range = QuoteService.get_price_range(event_type)

        return jsonify({
            'estimate': estimate,
            'estimate_display': f'R{estimate:,.2f}'.replace('.00', ''),
            'price_range_min': price_range[0],
            'price_range_max': price_range[1],
            'price_range_display': f'R{price_range[0]:,.2f} - R{price_range[1]:,.2f}'.replace('.00', '')
        })

    except Exception as e:
        logger.error(f'Estimate API error: {e}')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/inquiry', methods=['POST'])
def submit_inquiry():
    """Submit inquiry via API"""
    try:
        data = request.get_json()

        required = ['name', 'email', 'phone', 'event_type']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        inquiry = Inquiry(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            event_type=data.get('event_type'),
            event_date=datetime.strptime(data.get('event_date'), '%Y-%m-%d').date() if data.get('event_date') else None,
            budget_range=data.get('budget_range'),
            message=data.get('message'),
            status='new'
        )
        db.session.add(inquiry)
        db.session.commit()

        try:
            send_inquiry_email(inquiry)
        except Exception as e:
            logger.error(f'Email notification failed: {e}')

        return jsonify({
            'success': True,
            'message': 'Inquiry submitted successfully',
            'inquiry_id': inquiry.id
        }), 201

    except Exception as e:
        logger.error(f'Inquiry API error: {e}')
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN API ====================

@api_bp.route('/admin/stats', methods=['GET'])
@login_required
def admin_stats():
    """Get admin dashboard statistics"""
    try:
        period = request.args.get('period', '30')
        days = int(period) if period.isdigit() else 30

        since = datetime.utcnow() - timedelta(days=days)

        total_inquiries = Inquiry.query.filter(
            Inquiry.created_at >= since
        ).count()

        new_inquiries = Inquiry.query.filter(
            Inquiry.status == 'new',
            Inquiry.created_at >= since
        ).count()

        booked_inquiries = Inquiry.query.filter(
            Inquiry.status == 'booked',
            Inquiry.created_at >= since
        ).count()

        new_testimonials = Testimonial.query.filter(
            Testimonial.created_at >= since
        ).count()

        daily_data = []
        for i in range(days - 1, -1, -1):
            date = datetime.utcnow().date() - timedelta(days=i)
            count = Inquiry.query.filter(
                db.func.date(Inquiry.created_at) == date.isoformat()
            ).count()
            daily_data.append({
                'date': date.isoformat(),
                'count': count
            })

        return jsonify({
            'period': days,
            'total_inquiries': total_inquiries,
            'new_inquiries': new_inquiries,
            'booked_inquiries': booked_inquiries,
            'new_testimonials': new_testimonials,
            'daily_data': daily_data
        })

    except Exception as e:
        logger.error(f'Admin stats API error: {e}')
        return jsonify({'error': str(e)}), 500


@api_bp.route('/admin/inquiries/recent', methods=['GET'])
@login_required
def recent_inquiries():
    """Get recent inquiries"""
    limit = request.args.get('limit', default=10, type=int)

    inquiries = Inquiry.query.order_by(
        Inquiry.created_at.desc()
    ).limit(limit).all()

    return jsonify([{
        'id': i.id,
        'name': i.name,
        'email': i.email,
        'phone': i.phone,
        'event_type': i.get_event_type_display(),
        'status': i.status,
        'status_display': i.get_status_display(),
        'created_at': i.created_at.isoformat() if i.created_at else None
    } for i in inquiries])


@api_bp.route('/admin/inquiries/counts', methods=['GET'])
@login_required
def inquiry_counts():
    """Get inquiry counts by status"""
    counts = {
        'total': Inquiry.query.count(),
        'new': Inquiry.query.filter_by(status='new').count(),
        'contacted': Inquiry.query.filter_by(status='contacted').count(),
        'booked': Inquiry.query.filter_by(status='booked').count(),
        'archived': Inquiry.query.filter_by(status='archived').count()
    }
    return jsonify(counts)
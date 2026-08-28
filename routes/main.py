"""
THABZO EVENTS - Main Public Routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, \
    send_from_directory
from thabzo.models import (
    Service, GalleryImage, Testimonial, SiteSetting, Inquiry,
    TeamMember, EventAlbum, BlogPost, FAQ, Subscriber, Booking, db
)
from thabzo.forms import BookingForm, NewsletterForm
from datetime import datetime
import logging
import os

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


# ==================== STATIC FILE SERVING ====================

@main_bp.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files from static/uploads folder"""
    # Security: Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return '', 404

    # Get the upload folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')

    # Check if file exists in any subdirectory
    subdirs = ['team', 'gallery', 'albums', 'blog', 'videos', 'video-thumbnails', 'services']

    for subdir in subdirs:
        file_path = os.path.join(upload_folder, subdir, filename)
        if os.path.exists(file_path):
            return send_from_directory(os.path.join(upload_folder, subdir), filename)

    # If not found in any subdirectory, try the main upload folder
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path):
        return send_from_directory(upload_folder, filename)

    # Return a default image if file doesn't exist
    default_image = os.path.join(current_app.root_path, 'static', 'images', 'default-avatar.png')
    if os.path.exists(default_image):
        return send_from_directory(
            os.path.join(current_app.root_path, 'static', 'images'),
            'default-avatar.png'
        )

    return '', 404


@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


# ==================== PUBLIC ROUTES ====================

@main_bp.route('/')
def index():
    """Homepage"""
    try:
        featured_albums = EventAlbum.query.filter_by(
            is_featured=True,
            is_active=True
        ).order_by(EventAlbum.display_order).limit(6).all()

        if len(featured_albums) < 6:
            extra = EventAlbum.query.filter_by(
                is_active=True
            ).filter(EventAlbum.is_featured == False).order_by(
                EventAlbum.display_order
            ).limit(6 - len(featured_albums)).all()
            featured_albums.extend(extra)

        services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
        testimonials = Testimonial.query.filter_by(is_approved=True).limit(6).all()
        blog_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(3).all()

        settings = SiteSetting.query.all()
        settings_dict = {s.key: s.value for s in settings}
        hero_title = settings_dict.get('hero_title')
        hero_subtitle = settings_dict.get('hero_subtitle')

        total_events = EventAlbum.query.filter_by(is_active=True).count()
        total_testimonials = Testimonial.query.filter_by(is_approved=True).count()
        total_services = Service.query.filter_by(is_active=True).count()

        return render_template('main/index.html',
                               featured_albums=featured_albums,
                               services=services,
                               testimonials=testimonials,
                               blog_posts=blog_posts,
                               hero_title=hero_title,
                               hero_subtitle=hero_subtitle,
                               total_events=total_events,
                               total_testimonials=total_testimonials,
                               total_services=total_services)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('main/index.html')


@main_bp.route('/about')
def about():
    """About page"""
    try:
        settings = SiteSetting.query.filter_by(key='about_content').first()
        about_content = settings.value if settings else None

        team_members = TeamMember.query.filter_by(is_active=True).order_by(TeamMember.display_order).all()

        total_events = EventAlbum.query.filter_by(is_active=True).count()
        total_testimonials = Testimonial.query.filter_by(is_approved=True).count()
        total_team = TeamMember.query.filter_by(is_active=True).count()

        return render_template('main/about.html',
                               about_content=about_content,
                               team_members=team_members,
                               total_events=total_events,
                               total_testimonials=total_testimonials,
                               total_team=total_team)
    except Exception as e:
        logger.error(f"Error in about route: {str(e)}")
        return render_template('main/about.html')


@main_bp.route('/services')
def services():
    """Services page"""
    try:
        all_services = Service.query.filter_by(is_active=True).order_by(Service.display_order).all()
        return render_template('main/services.html', services=all_services)
    except Exception as e:
        logger.error(f"Error in services route: {str(e)}")
        return render_template('main/services.html', services=[])


@main_bp.route('/gallery')
def gallery():
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

        categories = EventAlbum.query.filter_by(is_active=True).distinct(EventAlbum.event_type).all()
        category_list = [c.event_type for c in categories if c.event_type]

        return render_template('main/gallery.html',
                               albums=albums,
                               categories=category_list,
                               current_category=category,
                               pagination=True)
    except Exception as e:
        logger.error(f"Error in gallery route: {str(e)}")
        return render_template('main/gallery.html', albums=[], categories=[])


@main_bp.route('/gallery/<int:id>')
def gallery_detail(id):
    """Album detail page - displays images in an album"""
    try:
        album = EventAlbum.query.get_or_404(id)
        images = GalleryImage.query.filter_by(album_id=id).order_by(GalleryImage.display_order).all()
        return render_template('main/gallery_detail.html', album=album, images=images)
    except Exception as e:
        logger.error(f"Error in gallery_detail route for id {id}: {str(e)}")
        return redirect(url_for('main.gallery'))


@main_bp.route('/testimonials')
def testimonials():
    """Testimonials page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9

        testimonials = Testimonial.query.filter_by(is_approved=True).order_by(
            Testimonial.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return render_template('main/testimonials.html', testimonials=testimonials, pagination=True)
    except Exception as e:
        logger.error(f"Error in testimonials route: {str(e)}")
        return render_template('main/testimonials.html', testimonials=[])


@main_bp.route('/blog')
def blog_index():
    """Blog listing page with search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9
        category = request.args.get('category')
        search = request.args.get('search')

        query = BlogPost.query.filter_by(is_published=True)

        if category:
            query = query.filter_by(category=category)

        if search:
            query = query.filter(
                db.or_(
                    BlogPost.title.ilike(f'%{search}%'),
                    BlogPost.content.ilike(f'%{search}%'),
                    BlogPost.excerpt.ilike(f'%{search}%')
                )
            )

        posts = query.order_by(BlogPost.published_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        categories = BlogPost.query.filter_by(is_published=True).distinct(BlogPost.category).all()
        recent_posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.published_at.desc()).limit(5).all()

        return render_template('blog/index.html',
                               posts=posts,
                               categories=categories,
                               recent_posts=recent_posts,
                               current_category=category,
                               search=search,
                               pagination=True)
    except Exception as e:
        logger.error(f"Error in blog_index route: {str(e)}")
        return render_template('blog/index.html', posts=[])


@main_bp.route('/blog/<slug>')
def blog_detail(slug):
    """Blog post detail page"""
    try:
        post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()

        # Increment view count
        post.views += 1
        db.session.commit()

        related_posts = BlogPost.query.filter(
            BlogPost.id != post.id,
            BlogPost.category == post.category,
            BlogPost.is_published == True
        ).order_by(BlogPost.published_at.desc()).limit(3).all()

        return render_template('blog/detail.html', post=post, related_posts=related_posts)
    except Exception as e:
        logger.error(f"Error in blog_detail route for slug {slug}: {str(e)}")
        return redirect(url_for('blog.blog_index'))


@main_bp.route('/faq')
def faq():
    """FAQ page with search functionality"""
    try:
        # Get search query
        search_query = request.args.get('search', '').strip()

        # Define default categories
        default_categories = ['General', 'Services', 'Pricing', 'Bookings', 'Other']
        faqs_by_category = {}

        # Base query for FAQs
        faq_query = FAQ.query.filter_by(is_active=True)

        # If search query exists, filter FAQs
        if search_query:
            faq_query = faq_query.filter(
                db.or_(
                    FAQ.question.ilike(f'%{search_query}%'),
                    FAQ.answer.ilike(f'%{search_query}%'),
                    FAQ.category.ilike(f'%{search_query}%')
                )
            )
            # For search results, group all results into "Search Results" category
            search_results = faq_query.order_by(FAQ.display_order).all()
            if search_results:
                faqs_by_category['Search Results'] = search_results
        else:
            # No search - group by category
            for category in default_categories:
                faqs = faq_query.filter_by(category=category).order_by(FAQ.display_order).all()
                if faqs:
                    faqs_by_category[category] = faqs

            # If no FAQs found in default categories, try to get all FAQs
            if not faqs_by_category:
                all_faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.display_order).all()
                if all_faqs:
                    # Group by category
                    for faq in all_faqs:
                        cat = faq.category or 'General'
                        if cat not in faqs_by_category:
                            faqs_by_category[cat] = []
                        faqs_by_category[cat].append(faq)

        # Get list of categories that actually have FAQs
        categories = list(faqs_by_category.keys())
        if not categories:
            categories = default_categories

        return render_template('main/faq.html',
                               faqs_by_category=faqs_by_category,
                               categories=categories,
                               search_query=search_query)
    except Exception as e:
        logger.error(f"Error in faq route: {str(e)}")
        return render_template('main/faq.html', faqs_by_category={}, categories=[], search_query='')


@main_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('main/privacy.html')


@main_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('main/terms.html')


@main_bp.route('/cookies')
def cookies():
    """Cookie Policy page"""
    return render_template('main/cookies.html')


@main_bp.route('/booking', methods=['GET', 'POST'])
def booking():
    """Online booking page"""
    form = BookingForm()

    if form.validate_on_submit():
        try:
            booking = Booking(
                client_name=form.client_name.data,
                client_email=form.client_email.data,
                client_phone=form.client_phone.data,
                event_type=form.event_type.data,
                event_date=form.event_date.data,
                event_time=form.event_time.data.strftime('%H:%M') if form.event_time.data else None,
                number_of_guests=form.guest_count.data,
                event_location=form.venue.data,
                special_requests=form.message.data,
                status='pending'
            )
            db.session.add(booking)
            db.session.commit()

            try:
                from thabzo.services.email_service import send_booking_notification
                send_booking_notification(booking)
            except ImportError:
                logger.warning("Email service not available")

            flash('Your booking request has been submitted successfully! We will contact you shortly.', 'success')
            return redirect(url_for('main.booking'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in booking route: {str(e)}")
            flash(f'Error submitting booking: {str(e)}', 'danger')

    return render_template('main/booking.html', form=form)


@main_bp.route('/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    form = NewsletterForm()

    if form.validate_on_submit():
        try:
            existing = Subscriber.query.filter_by(email=form.email.data).first()
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.subscribed_at = datetime.utcnow()
                    db.session.commit()
                    flash('You have been re-subscribed successfully!', 'success')
                else:
                    flash('You are already subscribed to our newsletter.', 'info')
            else:
                subscriber = Subscriber(
                    email=form.email.data,
                    name=form.name.data
                )
                db.session.add(subscriber)
                db.session.commit()

                try:
                    from thabzo.services.email_service import send_newsletter_welcome
                    send_newsletter_welcome(subscriber)
                except ImportError:
                    pass

                flash('Thank you for subscribing to our newsletter!', 'success')

        except Exception as e:
            logger.error(f"Error in subscribe_newsletter: {str(e)}")
            flash(f'Error subscribing: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')

    return redirect(request.referrer or url_for('main.index'))


@main_bp.route('/newsletter/unsubscribe/<token>')
def unsubscribe_newsletter(token):
    """Unsubscribe from newsletter"""
    try:
        import base64
        email = base64.b64decode(token).decode('utf-8')

        subscriber = Subscriber.query.filter_by(email=email).first()
        if subscriber and subscriber.is_active:
            subscriber.is_active = False
            subscriber.unsubscribed_at = datetime.utcnow()
            db.session.commit()
            flash('You have been unsubscribed from our newsletter.', 'info')
        else:
            flash('You are already unsubscribed or not found.', 'info')

    except Exception as e:
        logger.error(f"Error in unsubscribe_newsletter: {str(e)}")
        flash('Invalid unsubscribe link.', 'danger')

    return redirect(url_for('main.index'))


@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate sitemap.xml dynamically"""
    from flask import Response
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom

    root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')

    static_pages = [
        ('/', 'daily', 1.0),
        ('/about', 'monthly', 0.8),
        ('/services', 'weekly', 0.9),
        ('/gallery', 'weekly', 0.9),
        ('/testimonials', 'monthly', 0.7),
        ('/contact', 'monthly', 0.8),
        ('/blog', 'weekly', 0.8),
        ('/faq', 'monthly', 0.6),
        ('/booking', 'monthly', 0.7),
        ('/privacy', 'yearly', 0.3),
        ('/terms', 'yearly', 0.3),
    ]

    base_url = current_app.config.get('BASE_URL', 'https://thabzoevents.co.za')

    for path, changefreq, priority in static_pages:
        url = SubElement(root, 'url')
        loc = SubElement(url, 'loc')
        loc.text = f"{base_url}{path}"
        lastmod = SubElement(url, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
        changefreq_elem = SubElement(url, 'changefreq')
        changefreq_elem.text = changefreq
        priority_elem = SubElement(url, 'priority')
        priority_elem.text = str(priority)

    blog_posts = BlogPost.query.filter_by(is_published=True).all()
    for post in blog_posts:
        url = SubElement(root, 'url')
        loc = SubElement(url, 'loc')
        loc.text = f"{base_url}/blog/{post.slug}"
        lastmod = SubElement(url, 'lastmod')
        lastmod.text = post.published_at.strftime('%Y-%m-%d') if post.published_at else datetime.now().strftime(
            '%Y-%m-%d')
        changefreq_elem = SubElement(url, 'changefreq')
        changefreq_elem.text = 'monthly'
        priority_elem = SubElement(url, 'priority')
        priority_elem.text = '0.6'

    albums = EventAlbum.query.filter_by(is_active=True).all()
    for album in albums:
        url = SubElement(root, 'url')
        loc = SubElement(url, 'loc')
        loc.text = f"{base_url}/gallery/{album.id}"
        lastmod = SubElement(url, 'lastmod')
        lastmod.text = album.updated_at.strftime('%Y-%m-%d')
        changefreq_elem = SubElement(url, 'changefreq')
        changefreq_elem.text = 'monthly'
        priority_elem = SubElement(url, 'priority')
        priority_elem.text = '0.7'

    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent='  ')

    return Response(xml_str, mimetype='application/xml')


@main_bp.route('/search')
def search():
    """Global search page"""
    try:
        query = request.args.get('q', '').strip()

        if not query:
            flash('Please enter a search term.', 'warning')
            return redirect(url_for('main.index'))

        # Search in services
        services = Service.query.filter(
            db.or_(
                Service.name.ilike(f'%{query}%'),
                Service.description.ilike(f'%{query}%')
            ),
            Service.is_active == True
        ).all()

        # Search in blog posts
        blog_posts = BlogPost.query.filter(
            db.or_(
                BlogPost.title.ilike(f'%{query}%'),
                BlogPost.content.ilike(f'%{query}%'),
                BlogPost.excerpt.ilike(f'%{query}%')
            ),
            BlogPost.is_published == True
        ).all()

        # Search in FAQs
        faqs = FAQ.query.filter(
            db.or_(
                FAQ.question.ilike(f'%{query}%'),
                FAQ.answer.ilike(f'%{query}%')
            ),
            FAQ.is_active == True
        ).all()

        # Search in albums
        albums = EventAlbum.query.filter(
            db.or_(
                EventAlbum.name.ilike(f'%{query}%'),
                EventAlbum.description.ilike(f'%{query}%')
            ),
            EventAlbum.is_active == True
        ).all()

        results_count = len(services) + len(blog_posts) + len(faqs) + len(albums)

        return render_template('main/search_results.html',
                               query=query,
                               services=services,
                               blog_posts=blog_posts,
                               faqs=faqs,
                               albums=albums,
                               results_count=results_count)

    except Exception as e:
        logger.error(f"Error in search route: {str(e)}")
        flash('An error occurred while searching. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@main_bp.route('/debug-routes')
def debug_routes():
    """Debug route to show all registered routes"""
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)


@main_bp.app_errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    logger.error(f"500 error: {str(e)}")
    return render_template('errors/500.html'), 500
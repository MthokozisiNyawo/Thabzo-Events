from flask import Flask, request, g, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect, generate_csrf
from config import config
import os
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    # ============================================================
    # STATIC FOLDER CONFIGURATION - INSIDE thabzo folder
    # ============================================================
    thabzo_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(thabzo_dir, 'static')
    upload_folder = os.path.join(static_folder, 'uploads')

    app = Flask(__name__,
                static_folder=static_folder,
                static_url_path='/static',
                template_folder='templates')

    app.config.from_object(config[config_name])

    # Override static and upload folders to ensure they're inside thabzo
    app.config['STATIC_FOLDER'] = static_folder
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Update UPLOAD_SUBDIRS to use the correct paths
    app.config['UPLOAD_SUBDIRS'] = {
        'team': os.path.join(upload_folder, 'team'),
        'gallery': os.path.join(upload_folder, 'gallery'),
        'albums': os.path.join(upload_folder, 'albums'),
        'blog': os.path.join(upload_folder, 'blog'),
        'videos': os.path.join(upload_folder, 'videos'),
        'video-thumbnails': os.path.join(upload_folder, 'video-thumbnails'),
        'services': os.path.join(upload_folder, 'services'),
    }

    # ============================================================
    # COMPLETELY DISABLE CSRF PROTECTION
    # ============================================================
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_METHODS'] = []

    # ============================================================
    # CREATE ALL UPLOAD DIRECTORIES INSIDE thabzo/static/uploads/
    # ============================================================
    print("=" * 60)
    print("📁 CREATING UPLOAD DIRECTORIES (INSIDE thabzo/static/uploads/)")
    print("=" * 60)

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        print(f"✅ Main upload directory: {app.config['UPLOAD_FOLDER']}")
    except Exception as e:
        print(f"⚠️ Error creating main upload directory: {e}")

    for subdir, path in app.config['UPLOAD_SUBDIRS'].items():
        try:
            os.makedirs(path, exist_ok=True)
            print(f"✅ {subdir}: {path}")
        except Exception as e:
            print(f"⚠️ Error creating {subdir} directory: {e}")

    print("=" * 60)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db, directory=app.config.get('SQLALCHEMY_MIGRATE_REPO', 'migrations'))
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Exempt all routes from CSRF protection
    @csrf.exempt
    def exempt_all():
        pass

    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.login_message = 'Please login to access this page.'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from thabzo.models import User
            return User.query.get(int(user_id))
        except (ValueError, TypeError, AttributeError):
            return None

    # Register blueprints
    try:
        from thabzo.routes.main import main_bp
        app.register_blueprint(main_bp)
        print("✅ Registered main blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register main blueprint: {e}")

    try:
        from thabzo.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("✅ Registered admin blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register admin blueprint: {e}")

    try:
        from thabzo.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Registered auth blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register auth blueprint: {e}")

    try:
        from thabzo.routes.contact import contact_bp
        app.register_blueprint(contact_bp, url_prefix='/contact')
        print("✅ Registered contact blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register contact blueprint: {e}")

    try:
        from thabzo.routes.gallery import gallery_bp
        app.register_blueprint(gallery_bp, url_prefix='/gallery')
        print("✅ Registered gallery blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register gallery blueprint: {e}")

    try:
        from thabzo.routes.client import client_bp
        app.register_blueprint(client_bp, url_prefix='/client')
        print("✅ Registered client blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register client blueprint: {e}")

    try:
        from thabzo.routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        print("✅ Registered api blueprint")
    except ImportError as e:
        print(f"⚠️ Could not register api blueprint: {e}")

    # ============ SERVE UPLOADED FILES FROM INSIDE thabzo/static/uploads/ ============
    @app.route('/static/uploads/<path:filename>')
    def serve_upload(filename):
        """Serve uploaded files from thabzo/static/uploads/"""
        # Security: Prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return '', 404

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

        # Return default image if file doesn't exist
        default_image = os.path.join(static_folder, 'images', 'default-image.png')
        if os.path.exists(default_image):
            return send_from_directory(os.path.join(static_folder, 'images'), 'default-image.png')

        return '', 404

    # ============ SECURITY HEADERS MIDDLEWARE ============
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        headers = app.config.get('SECURITY_HEADERS', {})
        for key, value in headers.items():
            response.headers[key] = value
        return response

    # ============ COOKIE CONSENT MIDDLEWARE ============
    @app.before_request
    def check_cookie_consent():
        """Check if user has accepted cookies"""
        if request.path.startswith('/static') or request.path.startswith('/admin'):
            return

        consent_given = request.cookies.get('cookie_consent')
        if not consent_given and request.method == 'GET':
            request.environ['show_cookie_banner'] = True

    # ============ CONTEXT PROCESSORS ============
    @app.context_processor
    def inject_business_info():
        """Inject business info into all templates"""
        from thabzo.models import SiteSetting, User, Service, Testimonial, Inquiry, Booking, Subscriber, AdminNotification

        settings = {}
        try:
            site_settings = SiteSetting.query.all()
            settings = {s.key: s.value for s in site_settings}
        except:
            pass

        try:
            services = Service.query.filter_by(is_active=True).all()
            testimonials = Testimonial.query.filter_by(is_approved=True).all()
        except:
            services = []
            testimonials = []

        # ============================================================
        # SIDEBAR COUNTS - For admin sidebar
        # ============================================================
        sidebar_counts = {
            'total_users': 0,
            'new_inquiries': 0,
            'pending_bookings': 0,
            'pending_testimonials': 0,
            'active_subscribers': 0,
            'unread_notifications': 0
        }

        # Only query for counts if user is authenticated and accessing admin
        try:
            if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                # Check if user is admin
                if current_user.role == 'admin':
                    sidebar_counts['total_users'] = User.query.count()
                    sidebar_counts['new_inquiries'] = Inquiry.query.filter_by(status='new').count()
                    sidebar_counts['pending_bookings'] = Booking.query.filter_by(status='pending').count()
                    sidebar_counts['pending_testimonials'] = Testimonial.query.filter_by(is_approved=False).count()
                    sidebar_counts['active_subscribers'] = Subscriber.query.filter_by(is_active=True).count()
                    sidebar_counts['unread_notifications'] = AdminNotification.query.filter_by(
                        is_read=False,
                        user_id=current_user.id
                    ).count()
        except Exception as e:
            # Tables might not exist yet or other DB errors
            pass

        return {
            'business_name': settings.get('business_name', app.config.get('BUSINESS_NAME')),
            'business_phone': settings.get('business_phone', app.config.get('BUSINESS_PHONE')),
            'business_phone_alt': settings.get('business_phone_alt', app.config.get('BUSINESS_PHONE_ALT')),
            'business_location': settings.get('business_location', app.config.get('BUSINESS_LOCATION')),
            'business_tagline': settings.get('business_tagline', app.config.get('BUSINESS_TAGLINE')),
            'business_motto': settings.get('business_motto', app.config.get('BUSINESS_MOTTO')),
            'whatsapp_number': settings.get('whatsapp_number', app.config.get('WHATSAPP_NUMBER')),
            'footer_text': settings.get('footer_text', ''),
            'hero_title': settings.get('hero_title', 'Making Memories Beautiful'),
            'hero_subtitle': settings.get('hero_subtitle', 'We Do Decorations For All Events'),
            'admin_email': app.config.get('ADMIN_EMAIL', 'info@thabzoevents.co.za'),
            'User': User,
            'Service': Service,
            'Testimonial': Testimonial,
            'services': services,
            'testimonials': testimonials,
            'now': datetime.utcnow(),
            'show_cookie_banner': request.environ.get('show_cookie_banner', False),
            # Sidebar counts
            'total_users': sidebar_counts['total_users'],
            'new_inquiries': sidebar_counts['new_inquiries'],
            'pending_bookings': sidebar_counts['pending_bookings'],
            'pending_testimonials': sidebar_counts['pending_testimonials'],
            'active_subscribers': sidebar_counts['active_subscribers'],
            'unread_notifications': sidebar_counts['unread_notifications']
        }

    # ============ ERROR HANDLERS ============
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
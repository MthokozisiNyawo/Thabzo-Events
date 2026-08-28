"""
THABZO EVENTS - Application Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Base directory (project root - where thabzo folder is)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # STATIC FOLDER INSIDE THABZO FOLDER
    THABZO_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_FOLDER = os.path.join(THABZO_DIR, 'static')
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'uploads')

    # Create upload directories INSIDE thabzo/static/uploads/
    UPLOAD_SUBDIRS = {
        'team': os.path.join(UPLOAD_FOLDER, 'team'),
        'gallery': os.path.join(UPLOAD_FOLDER, 'gallery'),
        'albums': os.path.join(UPLOAD_FOLDER, 'albums'),
        'blog': os.path.join(UPLOAD_FOLDER, 'blog'),
        'videos': os.path.join(UPLOAD_FOLDER, 'videos'),
        'video-thumbnails': os.path.join(UPLOAD_FOLDER, 'video-thumbnails'),
        'services': os.path.join(UPLOAD_FOLDER, 'services'),
    }

    # Database - Handle PostgreSQL URL properly
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        # Render.com uses postgres://, but SQLAlchemy needs postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///thabzo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database pool settings for PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20,
    } if database_url else {}

    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size

    # Allowed extensions
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
        'video': {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'm4v', '3gp'},
        'document': {'pdf', 'doc', 'docx', 'txt'}
    }
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv', 'm4v', '3gp'}

    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Email settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@thabzo.co.za')
    BUSINESS_EMAIL = os.environ.get('BUSINESS_EMAIL', 'info@thabzo.co.za')
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'

    # Business Information
    BUSINESS_NAME = os.environ.get('BUSINESS_NAME', 'THABZO EVENTS')
    BUSINESS_PHONE = os.environ.get('BUSINESS_PHONE', '0765841224')
    BUSINESS_PHONE_ALT = os.environ.get('BUSINESS_PHONE_ALT', '')
    BUSINESS_LOCATION = os.environ.get('BUSINESS_LOCATION', 'Jozini, KwaZulu-Natal')
    BUSINESS_TAGLINE = os.environ.get('BUSINESS_TAGLINE', 'Creating Unforgettable Events')
    BUSINESS_MOTTO = os.environ.get('BUSINESS_MOTTO', 'Your Event, Our Passion')

    # Social Media
    FACEBOOK_URL = os.environ.get('FACEBOOK_URL', 'https://facebook.com/thabzoevents')
    INSTAGRAM_URL = os.environ.get('INSTAGRAM_URL', 'https://instagram.com/thabzoevents')
    TWITTER_URL = os.environ.get('TWITTER_URL', 'https://twitter.com/thabzoevents')
    YOUTUBE_URL = os.environ.get('YOUTUBE_URL', '')
    LINKEDIN_URL = os.environ.get('LINKEDIN_URL', '')
    TIKTOK_URL = os.environ.get('TIKTOK_URL', '')

    # WhatsApp
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '2765841224')
    WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"

    # Base URL
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # Security
    REMEMBER_COOKIE_DURATION = 30 * 24 * 60 * 60
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Session
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', SECRET_KEY)
    WTF_CSRF_TIME_LIMIT = 3600

    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # Authentication
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'False').lower() == 'true'
    VERIFICATION_TOKEN_EXPIRY_DAYS = 7
    RESET_TOKEN_EXPIRY_HOURS = 24

    # Pagination
    ITEMS_PER_PAGE = 12
    ADMIN_ITEMS_PER_PAGE = 25

    # Cache
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(THABZO_DIR, 'logs', 'app.log')

    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create upload directories INSIDE thabzo/static/uploads/
        for folder in app.config['UPLOAD_SUBDIRS'].values():
            try:
                os.makedirs(folder, exist_ok=True)
                print(f"✅ Created/verified: {folder}")
            except Exception as e:
                print(f"⚠️ Error creating folder {folder}: {e}")

        # Create logs directory
        try:
            os.makedirs(os.path.dirname(app.config['LOG_FILE']), exist_ok=True)
        except:
            pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL', 'sqlite:///thabzo_dev.db')
    LOG_LEVEL = 'DEBUG'
    MAIL_SUPPRESS_SEND = os.environ.get('DEV_MAIL_SUPPRESS_SEND', 'True').lower() == 'true'
    ASSETS_DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    WTF_CSRF_ENABLED = os.environ.get('DEV_CSRF_ENABLED', 'True').lower() == 'true'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    BCRYPT_ROUNDS = 4
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Handle PostgreSQL URL properly
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = database_url
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL must be set in production")

    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'False').lower() == 'true'
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = True
    LOG_LEVEL = 'WARNING'
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')

    # PostgreSQL specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'max_overflow': 20,
    }


class RenderConfig(ProductionConfig):
    """Render-specific configuration"""

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url

    PORT = int(os.environ.get('PORT', 10000))
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'render': RenderConfig,
    'default': DevelopmentConfig
}
"""
THABZO EVENTS - Database Models
"""
from thabzo import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """Unified User model for both admins and clients"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='client')  # admin, client
    is_active = db.Column(db.Boolean, default=True)

    # Email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    verification_token_expiry = db.Column(db.DateTime, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Password reset fields
    reset_password_token = db.Column(db.String(100), nullable=True)
    reset_password_expiry = db.Column(db.DateTime, nullable=True)

    # Security fields
    last_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    login_count = db.Column(db.Integer, default=0)
    deactivated_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    inquiries = db.relationship('Inquiry', backref='user', lazy=True)
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    notifications = db.relationship('AdminNotification', backref='user', lazy=True)

    def set_password(self, password):
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            return False

    def is_admin(self):
        return self.role == 'admin'

    def is_client(self):
        return self.role == 'client'

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Category(db.Model):
    """Unified category model for services, gallery, etc."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(50), default='service')
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - REMOVED gallery_videos
    services = db.relationship('Service', backref='category', lazy=True)
    gallery_images = db.relationship('GalleryImage', backref='category', lazy=True)

    TYPES = [
        ('service', 'Service'),
        ('gallery', 'Gallery'),
        ('event', 'Event'),
        ('blog', 'Blog')
    ]

    def __repr__(self):
        return f'<Category {self.name}>'


class EventAlbum(db.Model):
    """Event Album model for organizing gallery images by event"""
    __tablename__ = 'event_albums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    cover_image_id = db.Column(db.Integer, db.ForeignKey('gallery_images.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - REMOVED videos
    cover_image = db.relationship('GalleryImage', foreign_keys=[cover_image_id], lazy=True)
    images = db.relationship('GalleryImage', foreign_keys='GalleryImage.album_id',
                             backref='album', lazy=True,
                             order_by='GalleryImage.display_order')

    CATEGORIES = {
        'wedding': 'Wedding',
        'birthday': 'Birthday Party',
        'corporate': 'Corporate Event',
        'baby-shower': 'Baby Shower',
        'engagement': 'Engagement Party',
        'anniversary': 'Anniversary',
        'other': 'Other'
    }

    def get_category_display(self):
        return self.CATEGORIES.get(self.event_type, self.event_type or 'General')

    def get_cover_url(self):
        if self.cover_image and self.cover_image.filepath:
            return self.cover_image.filepath
        if self.images and len(self.images) > 0:
            return self.images[0].filepath
        return None

    def __repr__(self):
        return f'<EventAlbum {self.name}>'


class GalleryImage(db.Model):
    """Gallery image model with album support"""
    __tablename__ = 'gallery_images'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(200), nullable=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    album_id = db.Column(db.Integer, db.ForeignKey('event_albums.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_category_display(self):
        """Get the category display name"""
        if self.category:
            return self.category.name
        return 'Uncategorized'

    def __repr__(self):
        return f'<GalleryImage {self.title or self.filename}>'


class Service(db.Model):
    """Service offering model"""
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=True)
    starting_price = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    levels = db.relationship('ServiceLevel', backref='service', lazy=True, order_by='ServiceLevel.display_order')
    bookings = db.relationship('Booking', backref='service', lazy=True)

    def __repr__(self):
        return f'<Service {self.name}>'


class ServiceLevel(db.Model):
    """Service level/package model"""
    __tablename__ = 'service_levels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount_percentage = db.Column(db.Float, default=0)
    features = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(20), default='#6c5ce7')
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ServiceLevel {self.name}>'


class TeamMember(db.Model):
    """Team Member model for displaying team on website"""
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    photo_filename = db.Column(db.String(200), nullable=True)
    photo_filepath = db.Column(db.String(300), nullable=True)
    facebook = db.Column(db.String(200), nullable=True)
    twitter = db.Column(db.String(200), nullable=True)
    instagram = db.Column(db.String(200), nullable=True)
    linkedin = db.Column(db.String(200), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TeamMember {self.name}>'


class Inquiry(db.Model):
    """Event inquiry/quote request model"""
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.Date, nullable=True)
    budget_range = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='new')
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    EVENT_TYPES = {
        'wedding': 'Wedding',
        'birthday': 'Birthday Party',
        'corporate': 'Corporate Event',
        'baby-shower': 'Baby Shower',
        'engagement': 'Engagement Party',
        'anniversary': 'Anniversary',
        'other': 'Other'
    }

    STATUS_OPTIONS = {
        'new': 'New',
        'contacted': 'Contacted',
        'booked': 'Booked',
        'archived': 'Archived'
    }

    def get_event_type_display(self):
        return self.EVENT_TYPES.get(self.event_type, self.event_type)

    def get_status_display(self):
        return self.STATUS_OPTIONS.get(self.status, self.status)

    def __repr__(self):
        return f'<Inquiry {self.name} - {self.event_type}>'


class Booking(db.Model):
    """Online booking model"""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(10), nullable=True)
    number_of_guests = db.Column(db.Integer, nullable=True)
    event_location = db.Column(db.String(200), nullable=True)
    budget_range = db.Column(db.String(50), nullable=True)
    special_requests = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    STATUSES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ]

    def __repr__(self):
        return f'<Booking {self.client_name} - {self.event_type}>'


class Testimonial(db.Model):
    """Client testimonial model"""
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.String(50), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Testimonial {self.client_name}>'


class BlogPost(db.Model):
    """Blog/News post model"""
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    author = db.Column(db.String(100), default='THABZO EVENTS')
    views = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = db.relationship('BlogComment', backref='post', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BlogPost {self.title}>'

    def get_excerpt(self, length=150):
        if self.excerpt:
            return self.excerpt
        if self.content:
            return self.content[:length] + '...'
        return ''


class BlogComment(db.Model):
    """Blog comments model"""
    __tablename__ = 'blog_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    author_website = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BlogComment {self.author_name} - {self.post.title if self.post else "Unknown"}>'


class FAQ(db.Model):
    """Frequently Asked Questions model"""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FAQ {self.question[:30]}>'


class Subscriber(db.Model):
    """Newsletter subscriber model"""
    __tablename__ = 'subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Subscriber {self.email}>'


class AdminNotification(db.Model):
    """Admin notifications model"""
    __tablename__ = 'admin_notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AdminNotification {self.title}>'


class ActivityLog(db.Model):
    """User activity log model"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ActivityLog {self.action} - {self.entity_type}>'


class SiteSetting(db.Model):
    """Site settings/configuration model"""
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(200), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SiteSetting {self.key}>'


# Add this to your models.py file

class BudgetRange(db.Model):
    """Budget range options for inquiry forms"""
    __tablename__ = 'budget_ranges'

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)  # Display label like "R5,000 - R10,000"
    min_amount = db.Column(db.Numeric(10, 2), nullable=True)  # Optional min for filtering
    max_amount = db.Column(db.Numeric(10, 2), nullable=True)  # Optional max for filtering
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BudgetRange {self.label}>'

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

class ClientSetting(db.Model):
    """Client-specific settings and preferences"""
    __tablename__ = 'client_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    whatsapp_notifications = db.Column(db.Boolean, default=True)
    marketing_updates = db.Column(db.Boolean, default=False)

    # Preferences
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='SAST')
    default_event_type = db.Column(db.String(50), nullable=True)

    # Security
    two_factor_auth = db.Column(db.Boolean, default=False)
    login_alerts = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('client_settings', uselist=False))

    def __repr__(self):
        return f'<ClientSetting for User {self.user_id}>'

    def to_dict(self):
        return {
            'email_notifications': self.email_notifications,
            'sms_notifications': self.sms_notifications,
            'whatsapp_notifications': self.whatsapp_notifications,
            'marketing_updates': self.marketing_updates,
            'language': self.language,
            'timezone': self.timezone,
            'default_event_type': self.default_event_type,
            'two_factor_auth': self.two_factor_auth,
            'login_alerts': self.login_alerts
        }
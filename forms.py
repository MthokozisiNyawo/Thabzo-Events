from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, TextAreaField, SelectField, DateField,
    EmailField, TelField, FloatField, IntegerField,
    PasswordField, BooleanField, HiddenField, DecimalField, URLField,
    DateTimeField, TimeField, SubmitField
)
from thabzo.models import BudgetRange
from wtforms.validators import (
    DataRequired, Email, Length, Optional, NumberRange,
    EqualTo, ValidationError, Regexp, URL
)
from datetime import datetime


class NewsletterForm(FlaskForm):
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.')
    ])
    name = StringField('Name', validators=[
        Optional(),
        Length(max=100)
    ])
    submit = SubmitField('Subscribe')


class BlogCommentForm(FlaskForm):
    author_name = StringField('Name', validators=[
        DataRequired(message='Please enter your name.'),
        Length(max=100)
    ])
    author_email = EmailField('Email', validators=[
        DataRequired(message='Please enter your email.'),
        Email(message='Please enter a valid email.')
    ])
    author_website = URLField('Website', validators=[
        Optional(),
        URL(message='Please enter a valid URL.')
    ])
    content = TextAreaField('Comment', validators=[
        DataRequired(message='Please enter your comment.'),
        Length(max=1000, message='Comment cannot exceed 1000 characters.')
    ])
    submit = SubmitField('Post Comment')


class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Please enter your username.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UserRegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Please enter your full name.'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
    ])
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.')
    ])
    phone = TelField('Phone Number', validators=[
        Optional(),
        Length(max=20, message='Phone number cannot exceed 20 characters.')
    ])
    username = StringField('Username', validators=[
        Optional(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters.'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter a password.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    terms = BooleanField('I agree to the Terms of Service and Privacy Policy', validators=[
        DataRequired(message='You must agree to the terms to register.')
    ])
    submit = SubmitField('Create Account')


class UserLoginForm(FlaskForm):
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please enter your email.'),
        Email(message='Please enter a valid email.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.')
    ])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message='Please enter a new password.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')


class ServiceLevelForm(FlaskForm):
    """Service level/package form"""
    name = StringField('Level Name', validators=[
        DataRequired(message='Level name is required.'),
        Length(max=50)
    ])
    slug = StringField('Slug (URL)', validators=[
        DataRequired(message='Slug is required.'),
        Length(max=50),
        Regexp(r'^[a-z0-9-]+$', message='Slug can only contain lowercase letters, numbers, and hyphens.')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ])
    price = DecimalField('Price (R)', validators=[
        Optional(),
        NumberRange(min=0, message='Price cannot be negative.')
    ])
    discount_percentage = DecimalField('Discount Percentage', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Discount must be between 0 and 100.')
    ])
    features = TextAreaField('Features (comma separated)', validators=[
        Optional(),
        Length(max=500)
    ])
    icon = StringField('Icon Class', validators=[
        Optional(),
        Length(max=50)
    ])
    color = StringField('Color', validators=[
        Optional(),
        Length(max=20)
    ])
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater.')
    ], default=0)
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    service_id = SelectField('Service', choices=[], coerce=int, validators=[DataRequired(message='Please select a service.')])
    submit = SubmitField('Save Service Level')

    def __init__(self, *args, **kwargs):
        super(ServiceLevelForm, self).__init__(*args, **kwargs)
        from thabzo.models import Service
        self.service_id.choices = [(0, '-- Select Service --')] + [(s.id, s.name) for s in Service.query.filter_by(is_active=True).order_by(Service.display_order).all()]


class CategoryForm(FlaskForm):
    """Unified category form"""
    name = StringField('Category Name', validators=[
        DataRequired(message='Category name is required.'),
        Length(max=50)
    ])
    slug = StringField('Slug (URL)', validators=[
        Optional(),
        Length(max=50),
        Regexp(r'^[a-z0-9-]+$', message='Slug can only contain lowercase letters, numbers, and hyphens.')
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500)
    ])
    icon = StringField('Icon Class', validators=[
        Optional(),
        Length(max=50)
    ])
    type = SelectField('Category Type', choices=[
        ('general', 'General'),
        ('service', 'Service'),
        ('gallery', 'Gallery Image'),
        ('video', 'Gallery Video'),
        ('album', 'Event Album')
    ], validators=[DataRequired(message='Please select a category type.')])
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater.')
    ], default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')


class EventAlbumForm(FlaskForm):
    """Event album form"""
    name = StringField('Event Name', validators=[
        DataRequired(message='Event name is required.'),
        Length(max=200, message='Event name cannot exceed 200 characters.')
    ])
    slug = StringField('Slug (URL)', validators=[
        Optional(),
        Length(max=200),
        Regexp(r'^[a-z0-9-]+$', message='Slug can only contain lowercase letters, numbers, and hyphens.')
    ])
    description = TextAreaField('Event Description', validators=[
        Optional(),
        Length(max=500)
    ])
    category_id = SelectField('Category', choices=[], coerce=int, validators=[Optional()])
    event_type = StringField('Event Type', validators=[
        Optional(),
        Length(max=100, message='Event type cannot exceed 100 characters.')
    ])
    event_date = DateField('Event Date', validators=[Optional()], format='%Y-%m-%d')
    cover_image = FileField('Cover Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed!')
    ])
    is_featured = BooleanField('Featured Album', default=False)
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater.')
    ], default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Album')

    def __init__(self, *args, **kwargs):
        super(EventAlbumForm, self).__init__(*args, **kwargs)
        from thabzo.models import Category
        categories = Category.query.filter_by(is_active=True, type='album').order_by(Category.display_order).all()
        self.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]


class InquiryForm(FlaskForm):
    """Contact/inquiry form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    event_type = SelectField('Event Type',
                             choices=[
                                 ('wedding', 'Wedding'),
                                 ('birthday', 'Birthday Party'),
                                 ('corporate', 'Corporate Event'),
                                 ('baby-shower', 'Baby Shower'),
                                 ('engagement', 'Engagement Party'),
                                 ('anniversary', 'Anniversary'),
                                 ('graduation', 'Graduation'),
                                 ('other', 'Other')
                             ],
                             validators=[DataRequired()]
                             )
    event_date = DateField('Event Date', format='%Y-%m-%d', validators=[Optional()])
    budget_range = SelectField('Budget Range', choices=[], validators=[Optional()])  # Dynamic choices
    message = TextAreaField('Your Vision / Message', validators=[Optional(), Length(max=1000)])

    def __init__(self, *args, **kwargs):
        super(InquiryForm, self).__init__(*args, **kwargs)
        # Dynamically populate budget range choices from database
        self.budget_range.choices = self.get_budget_choices()

    @staticmethod
    def get_budget_choices():
        """Get budget range choices from database"""
        try:
            ranges = BudgetRange.query.filter_by(is_active=True).order_by(BudgetRange.display_order).all()
            if ranges:
                return [('', 'Select Budget Range')] + [(str(r.id), r.label) for r in ranges]
        except:
            pass
        # Fallback choices if database table doesn't exist or no data
        return [
            ('', 'Select Budget Range'),
            ('R0 - R5,000', 'R0 - R5,000'),
            ('R5,000 - R10,000', 'R5,000 - R10,000'),
            ('R10,000 - R20,000', 'R10,000 - R20,000'),
            ('R20,000 - R50,000', 'R20,000 - R50,000'),
            ('R50,000+', 'R50,000+')]

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(message='Please enter your name.'),
        Length(max=100)
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Please enter your email.'),
        Email(message='Please enter a valid email.')
    ])
    phone = TelField('Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    subject = StringField('Subject', validators=[
        Optional(),
        Length(max=100)
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(message='Please enter your message.'),
        Length(max=1000, message='Message cannot exceed 1000 characters.')
    ])
    submit = SubmitField('Send Message')

class BookingForm(FlaskForm):
    client_name = StringField('Full Name', validators=[
        DataRequired(message='Please enter your name.'),
        Length(min=2, max=100)
    ])
    client_email = EmailField('Email Address', validators=[
        DataRequired(message='Please enter your email.'),
        Email(message='Please enter a valid email.')
    ])
    client_phone = TelField('Phone Number', validators=[
        DataRequired(message='Please enter your phone number.'),
        Length(min=10, max=20)
    ])
    event_type = SelectField('Event Type', choices=[
        ('', 'Select Event Type'),
        ('wedding', 'Wedding'),
        ('birthday', 'Birthday Party'),
        ('corporate', 'Corporate Event'),
        ('baby-shower', 'Baby Shower'),
        ('engagement', 'Engagement Party'),
        ('anniversary', 'Anniversary'),
        ('other', 'Other')
    ], validators=[DataRequired(message='Please select an event type.')])
    event_date = DateField('Event Date', validators=[
        DataRequired(message='Please select an event date.')
    ], format='%Y-%m-%d')
    event_time = TimeField('Preferred Time', validators=[Optional()], format='%H:%M')
    guest_count = IntegerField('Estimated Guest Count', validators=[
        Optional(),
        NumberRange(min=1, message='Please enter a valid number.')
    ])
    venue = StringField('Event Venue', validators=[
        Optional(),
        Length(max=200)
    ])
    message = TextAreaField('Additional Details', validators=[
        Optional(),
        Length(max=1000)
    ])
    submit = SubmitField('Submit Booking')

class AdminProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        Optional(),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters.')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email.')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(max=100)
    ])
    phone = TelField('Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='Password must be at least 6 characters.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Profile')


class TeamMemberForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(max=100)
    ])
    position = StringField('Position', validators=[
        DataRequired(message='Position is required.'),
        Length(max=100)
    ])
    bio = TextAreaField('Biography', validators=[
        Optional(),
        Length(max=500)
    ])
    email = EmailField('Email', validators=[
        Optional(),
        Email(message='Please enter a valid email.')
    ])
    phone = TelField('Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed!')
    ])
    facebook = StringField('Facebook URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL.')
    ])
    twitter = StringField('Twitter/X URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL.')
    ])
    instagram = StringField('Instagram URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL.')
    ])
    linkedin = StringField('LinkedIn URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL.')
    ])
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater.')
    ], default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Team Member')


class BlogPostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(message='Title is required.'),
        Length(max=200)
    ])
    slug = StringField('Slug (URL)', validators=[
        Optional(),
        Length(max=200),
        Regexp(r'^[a-z0-9-]+$', message='Slug can only contain lowercase letters, numbers, and hyphens.')
    ])
    excerpt = TextAreaField('Excerpt', validators=[
        Optional(),
        Length(max=500)
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(message='Content is required.')
    ])
    category = StringField('Category', validators=[
        Optional(),
        Length(max=50)
    ])
    tags = StringField('Tags (comma separated)', validators=[
        Optional(),
        Length(max=200)
    ])
    author = StringField('Author', validators=[
        Optional(),
        Length(max=100)
    ])
    featured_image = FileField('Featured Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed!')
    ])
    is_published = BooleanField('Published', default=False)
    is_featured = BooleanField('Featured Post', default=False)
    published_at = DateTimeField('Publish Date', validators=[Optional()], format='%Y-%m-%d %H:%M')
    submit = SubmitField('Save Blog Post')


class FAQForm(FlaskForm):
    question = StringField('Question', validators=[
        DataRequired(message='Question is required.'),
        Length(max=200)
    ])
    answer = TextAreaField('Answer', validators=[
        DataRequired(message='Answer is required.')
    ])
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('services', 'Services'),
        ('pricing', 'Pricing'),
        ('bookings', 'Bookings'),
        ('other', 'Other')
    ], validators=[Optional()])
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0)
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save FAQ')


class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[
        DataRequired(message='Service name is required.'),
        Length(max=50)
    ])
    slug = StringField('Slug (URL)', validators=[
        Optional(),
        Length(max=50),
        Regexp(r'^[a-z0-9-]+$', message='Slug can only contain lowercase letters, numbers, and hyphens.')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required.')
    ])
    icon = StringField('FontAwesome Icon Class', validators=[
        Optional(),
        Length(max=50)
    ])
    starting_price = DecimalField('Starting Price (R)', validators=[
        Optional(),
        NumberRange(min=0, message='Price cannot be negative.')
    ])
    is_active = BooleanField('Active', default=True)
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater.')
    ], default=0)
    category_id = SelectField('Category', choices=[], coerce=int, validators=[Optional()])
    submit = SubmitField('Save Service')

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        from thabzo.models import Category
        categories = Category.query.filter_by(is_active=True, type='service').order_by(Category.display_order).all()
        self.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]


class GalleryImageForm(FlaskForm):
    title = StringField('Title', validators=[
        Optional(),
        Length(max=100)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=200)
    ])
    category_id = SelectField('Category', choices=[], coerce=int, validators=[DataRequired(message='Please select a category.')])
    image = FileField('Image', validators=[
        DataRequired(message='Please select an image.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed!')
    ])
    is_featured = BooleanField('Featured Image', default=False)
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0)
    album_id = SelectField('Event Album', choices=[], coerce=int, validators=[Optional()])
    submit = SubmitField('Upload Image')

    def __init__(self, *args, **kwargs):
        super(GalleryImageForm, self).__init__(*args, **kwargs)
        from thabzo.models import Category, EventAlbum
        categories = Category.query.filter_by(is_active=True, type='gallery').order_by(Category.display_order).all()
        self.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]
        albums = EventAlbum.query.filter_by(is_active=True).order_by(EventAlbum.display_order).all()
        self.album_id.choices = [(0, 'No Album')] + [(a.id, a.name) for a in albums]


class MultipleGalleryImageForm(FlaskForm):
    title = StringField('Title (Optional)', validators=[
        Optional(),
        Length(max=100)
    ])
    description = TextAreaField('Description (Optional)', validators=[
        Optional(),
        Length(max=200)
    ])
    category_id = SelectField('Category', choices=[], coerce=int, validators=[DataRequired(message='Please select a category.')])
    images = MultipleFileField('Select Images', validators=[
        DataRequired(message='Please select at least one image.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only images are allowed!')
    ])
    is_featured = BooleanField('Featured Images', default=False)
    display_order = IntegerField('Display Order', validators=[
        Optional(),
        NumberRange(min=0)
    ], default=0)
    album_id = SelectField('Event Album', choices=[], coerce=int, validators=[Optional()])
    create_new_album = BooleanField('Create New Album', default=False)
    album_name = StringField('New Album Name', validators=[
        Optional(),
        Length(max=100)
    ])
    submit = SubmitField('Upload Images')

    def __init__(self, *args, **kwargs):
        super(MultipleGalleryImageForm, self).__init__(*args, **kwargs)
        from thabzo.models import Category, EventAlbum
        categories = Category.query.filter_by(is_active=True, type='gallery').order_by(Category.display_order).all()
        self.category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]
        albums = EventAlbum.query.filter_by(is_active=True).order_by(EventAlbum.display_order).all()
        self.album_id.choices = [(0, 'No Album')] + [(a.id, a.name) for a in albums]

class TestimonialForm(FlaskForm):
    client_name = StringField('Client Name', validators=[
        DataRequired(message='Client name is required.'),
        Length(max=100)
    ])
    event_type = StringField('Event Type', validators=[
        Optional(),
        Length(max=50)
    ])
    content = TextAreaField('Testimonial', validators=[
        DataRequired(message='Testimonial content is required.')
    ])
    rating = IntegerField('Rating (1-5)', validators=[
        Optional(),
        NumberRange(min=1, max=5, message='Rating must be between 1 and 5.')
    ], default=5)
    is_approved = BooleanField('Approved', default=False)
    submit = SubmitField('Save Testimonial')


class InquiryStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('booked', 'Booked'),
        ('archived', 'Archived')
    ], validators=[DataRequired(message='Please select a status.')])
    notes = TextAreaField('Admin Notes', validators=[Optional()])
    submit = SubmitField('Update Status')


class SiteSettingForm(FlaskForm):
    business_name = StringField('Business Name', validators=[Optional(), Length(max=100)])
    business_phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    business_phone_alt = StringField('Alternative Phone', validators=[Optional(), Length(max=20)])
    business_location = StringField('Location', validators=[Optional(), Length(max=100)])
    whatsapp_number = StringField('WhatsApp Number', validators=[Optional(), Length(max=20)])
    business_tagline = StringField('Tagline', validators=[Optional(), Length(max=100)])
    business_motto = StringField('Motto', validators=[Optional(), Length(max=200)])
    about_content = TextAreaField('About Us Content', validators=[Optional()])
    hero_title = StringField('Hero Title', validators=[Optional(), Length(max=100)])
    hero_subtitle = StringField('Hero Subtitle', validators=[Optional(), Length(max=200)])
    footer_text = StringField('Footer Text', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Settings')


# Add this to your forms.py

class BudgetRangeForm(FlaskForm):
    """Form for managing budget ranges"""
    label = StringField('Budget Range Label', validators=[
        DataRequired(message='Budget range label is required'),
        Length(max=100, message='Label must be less than 100 characters')
    ])
    min_amount = DecimalField('Minimum Amount (R)', validators=[
        Optional(),
        NumberRange(min=0, message='Minimum amount must be 0 or greater')
    ])
    max_amount = DecimalField('Maximum Amount (R)', validators=[
        Optional(),
        NumberRange(min=0, message='Maximum amount must be 0 or greater')
    ])
    display_order = IntegerField('Display Order', default=0, validators=[
        Optional(),
        NumberRange(min=0, message='Display order must be 0 or greater')
    ])
    is_active = BooleanField('Active', default=True)


# Add this to your forms.py

class ClientSettingsForm(FlaskForm):
    """Client settings form"""
    # Notification preferences
    email_notifications = BooleanField('Email Notifications', default=True)
    sms_notifications = BooleanField('SMS Notifications', default=False)
    whatsapp_notifications = BooleanField('WhatsApp Notifications', default=True)
    marketing_updates = BooleanField('Marketing Updates', default=False)

    # Preferences
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('zu', 'isiZulu'),
        ('af', 'Afrikaans')
    ], default='en')

    timezone = SelectField('Time Zone', choices=[
        ('SAST', 'South Africa (SAST)'),
        ('UTC', 'UTC'),
        ('CAT', 'Central Africa Time'),
        ('EAT', 'East Africa Time')
    ], default='SAST')

    default_event_type = SelectField('Default Event Type', choices=[
        ('', 'Select event type'),
        ('wedding', 'Wedding'),
        ('birthday', 'Birthday Party'),
        ('corporate', 'Corporate Event'),
        ('baby-shower', 'Baby Shower'),
        ('engagement', 'Engagement Party'),
        ('anniversary', 'Anniversary'),
        ('graduation', 'Graduation'),
        ('other', 'Other')
    ], default='')

    # Security
    two_factor_auth = BooleanField('Two-Factor Authentication', default=False)
    login_alerts = BooleanField('Login Alerts', default=True)
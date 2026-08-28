"""
THABZO EVENTS - Custom Validators
"""
import re
from wtforms.validators import ValidationError


def validate_phone(form, field):
    """Validate South African phone number"""
    if not field.data:
        return

    # Remove spaces, dashes, etc.
    phone = re.sub(r'[\s\-\(\)]', '', field.data)

    # Check if it's a valid SA number
    # 0765841224, +27765841224, 076-584-1224, etc.
    patterns = [
        r'^0[6-8][0-9]{8}$',  # 0x xxxxxxx
        r'^\+27[6-8][0-9]{8}$',  # +27x xxxxxxx
        r'^27[6-8][0-9]{8}$',  # 27x xxxxxxx
    ]

    valid = any(re.match(pattern, phone) for pattern in patterns)
    if not valid:
        raise ValidationError('Please enter a valid South African phone number.')


def validate_future_date(form, field):
    """Validate that date is in the future"""
    from datetime import datetime
    if field.data and field.data < datetime.now().date():
        raise ValidationError('Date cannot be in the past.')


def validate_service_slug(form, field):
    """Validate service slug is unique"""
    from thabzo.models import Service
    if field.data:
        # Check if slug exists
        existing = Service.query.filter_by(slug=field.data).first()
        if existing and (not hasattr(form, '_obj') or existing.id != form._obj.id):
            raise ValidationError('Slug already exists. Please use a different slug.')


def validate_username(form, field):
    """Validate username is unique"""
    from thabzo.models import Admin
    if field.data:
        existing = Admin.query.filter_by(username=field.data).first()
        if existing and (not hasattr(form, '_obj') or existing.id != form._obj.id):
            raise ValidationError('Username already exists.')


def validate_email_unique(form, field):
    """Validate email is unique"""
    from thabzo.models import Admin
    if field.data:
        existing = Admin.query.filter_by(email=field.data).first()
        if existing and (not hasattr(form, '_obj') or existing.id != form._obj.id):
            raise ValidationError('Email already registered.')


def validate_budget_range(form, field):
    """Validate budget range format"""
    if field.data:
        valid_ranges = ['under-5000', '5000-10000', '10000-20000', '20000-50000', 'above-50000']
        if field.data not in valid_ranges:
            raise ValidationError('Invalid budget range selected.')
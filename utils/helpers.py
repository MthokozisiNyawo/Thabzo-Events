"""
THABZO EVENTS - Helper Functions
"""
import re
import string
import random
from datetime import datetime, timedelta
from flask import current_app


def generate_slug(text):
    """Generate a URL-friendly slug from text"""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    # Remove special characters
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Remove multiple hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def generate_random_string(length=8):
    """Generate a random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def format_currency(amount):
    """Format amount as South African Rand"""
    if amount is None:
        return 'R0.00'
    return f'R{amount:,.2f}'.replace('.00', '')


def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length"""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix


def days_until(date):
    """Calculate days until a date"""
    if not date:
        return None
    delta = date - datetime.now().date()
    return delta.days


def date_display(date, format='%d %B %Y'):
    """Format date for display"""
    if not date:
        return 'Not specified'
    return date.strftime(format)


def datetime_display(dt, format='%d %B %Y at %H:%M'):
    """Format datetime for display"""
    if not dt:
        return 'Not specified'
    return dt.strftime(format)


def time_ago(dt):
    """Return human-readable time since"""
    if not dt:
        return ''

    now = datetime.utcnow()
    diff = now - dt

    if diff.days == 0:
        if diff.seconds < 60:
            return 'Just now'
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        else:
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif diff.days < 7:
        return f'{diff.days} day{"s" if diff.days > 1 else ""} ago'
    elif diff.days < 30:
        weeks = diff.days // 7
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'
    else:
        return dt.strftime('%d %b %Y')


def get_status_color(status):
    """Return Bootstrap color class for status"""
    colors = {
        'new': 'warning',
        'contacted': 'info',
        'booked': 'success',
        'archived': 'secondary'
    }
    return colors.get(status, 'secondary')


def get_rating_stars(rating):
    """Return HTML for rating stars"""
    if not rating:
        return ''
    full_stars = int(rating)
    empty_stars = 5 - full_stars
    return '★' * full_stars + '☆' * empty_stars


def get_rating_width(rating):
    """Return percentage width for star ratings"""
    if not rating:
        return 0
    return (rating / 5) * 100


def safe_boolean(value):
    """Convert various inputs to boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    return False
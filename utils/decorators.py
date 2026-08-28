"""
THABZO EVENTS - Custom Decorators
"""
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.logout'))
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('client.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """Decorator to require super admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('client.dashboard'))
        # Super admin is admin with role 'admin' (you can add additional checks)
        return f(*args, **kwargs)
    return decorated_function


def client_required(f):
    """Decorator to require client role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.logout'))
        if current_user.is_admin():
            return f(*args, **kwargs)
        if not current_user.is_client():
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def login_required_with_redirect(f):
    """Custom login required with redirect"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
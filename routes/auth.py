"""
THABZO EVENTS - Authentication Routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, make_response, \
    jsonify
from flask_login import login_user, logout_user, login_required, current_user
from thabzo.models import User, db
from thabzo.forms import UserRegisterForm, UserLoginForm
from datetime import datetime, timedelta
import logging
import secrets
import string
from urllib.parse import urlparse, urljoin

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


def is_safe_url(target):
    """Check if URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def generate_verification_token():
    """Generate a secure verification token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def generate_reset_token():
    """Generate a password reset token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('main.index'))

    form = UserLoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)

            session.clear()
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()

            flash(f'Welcome back, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)

            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('client.dashboard'))

        else:
            flash('Invalid email or password.', 'danger')
            logger.warning(f'Failed login attempt for email: {form.email.data} from {request.remote_addr}')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Client registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = UserRegisterForm()

    if form.validate_on_submit():
        try:
            email = form.email.data.lower().strip()
            username = form.username.data or email.split('@')[0]

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('This email is already registered. Please login or use a different email.', 'danger')
                return render_template('auth/register.html', form=form)

            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                username = f"{username}{secrets.randbelow(1000)}"

            user = User(
                username=username,
                email=email,
                full_name=form.full_name.data.strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
                role='client',
                is_active=True,
                email_verified=True,  # Auto-verify for simplicity
                email_verification_token=generate_verification_token(),
                verification_token_expiry=datetime.utcnow() + timedelta(days=7)
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            # Try to send welcome email (don't fail if it doesn't work)
            try:
                from thabzo.services.email_service import send_welcome_email, send_verification_email
                send_welcome_email(user)
                # send_verification_email(user)  # Optional: uncomment if you want verification
            except Exception as e:
                logger.error(f'Welcome email failed: {e}')

            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Registration error: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """Verify user's email address"""
    try:
        user = User.query.filter_by(email_verification_token=token).first()

        if not user:
            flash('Invalid or expired verification link.', 'danger')
            return redirect(url_for('auth.login'))

        if user.verification_token_expiry and user.verification_token_expiry < datetime.utcnow():
            flash('Verification link has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.resend_verification'))

        user.email_verified = True
        user.email_verification_token = None
        user.verification_token_expiry = None
        user.verified_at = datetime.utcnow()
        db.session.commit()

        flash('Your email has been verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        logger.error(f'Email verification error: {str(e)}')
        flash('An error occurred during verification. Please try again.', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend verification email"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/resend_verification.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/resend_verification.html')

        if user.email_verified:
            flash('Your email is already verified. Please login.', 'success')
            return redirect(url_for('auth.login'))

        user.email_verification_token = generate_verification_token()
        user.verification_token_expiry = datetime.utcnow() + timedelta(days=7)
        db.session.commit()

        try:
            from thabzo.services.email_service import send_verification_email
            send_verification_email(user)
            flash('Verification email has been resent. Please check your inbox.', 'success')
        except Exception as e:
            logger.error(f'Failed to resend verification email: {str(e)}')
            flash('Failed to send verification email. Please try again later.', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('auth/resend_verification.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()

        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if user:
            user.reset_password_token = generate_reset_token()
            user.reset_password_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()

            try:
                from thabzo.services.email_service import send_password_reset_email
                send_password_reset_email(user)
                flash('Password reset instructions have been sent to your email.', 'success')
            except Exception as e:
                logger.error(f'Failed to send reset email: {str(e)}')
                flash('Failed to send reset email. Please try again later.', 'danger')
        else:
            flash('If an account exists with that email, password reset instructions have been sent.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user = User.query.filter_by(reset_password_token=token).first()

    if not user:
        flash('Invalid or expired reset link. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if user.reset_password_expiry and user.reset_password_expiry < datetime.utcnow():
        flash('Reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not password or len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.reset_password_token = None
        user.reset_password_expiry = None
        user.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Your password has been reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in user"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('auth.change_password'))

        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('client.profile'))

    return render_template('auth/change_password.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    try:
        response = make_response(redirect(url_for('main.index')))
        session.clear()

        for key in request.cookies:
            response.delete_cookie(key)

        logout_user()
        session.modified = True

        flash('You have been logged out successfully.', 'info')
        return response

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash('An error occurred during logout.', 'danger')
        return redirect(url_for('main.index'))


@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """Check if email is available (AJAX)"""
    email = request.json.get('email', '').lower().strip()
    user = User.query.filter_by(email=email).first()
    return jsonify({'available': user is None})


@auth_bp.route('/check-username', methods=['POST'])
def check_username():
    """Check if username is available (AJAX)"""
    username = request.json.get('username', '').strip()
    user = User.query.filter_by(username=username).first()
    return jsonify({'available': user is None})


@auth_bp.context_processor
def inject_user_data():
    """Inject user data into all templates"""
    if current_user.is_authenticated:
        return {
            'current_user': current_user,
            'user_full_name': current_user.full_name,
            'user_email': current_user.email,
            'user_role': current_user.role,
            'is_admin': current_user.is_admin(),
            'is_client': not current_user.is_admin()
        }
    return {
        'current_user': None,
        'user_full_name': None,
        'user_email': None,
        'user_role': None,
        'is_admin': False,
        'is_client': False
    }
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from thabzo.models import (
    User, Booking, Inquiry, Testimonial, Service,
    EventAlbum, BlogPost, ActivityLog, db, SiteSetting, ClientSetting
)
from thabzo.forms import (
    AdminProfileForm, BookingForm, InquiryForm,
    TestimonialForm, UserRegisterForm, ContactForm, ClientSettingsForm
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from sqlalchemy import and_, or_
import logging
import re
import json

client_bp = Blueprint('client', __name__)
logger = logging.getLogger(__name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def log_activity(user_id, action, entity_type, entity_id=None, details=None):
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")
        db.session.rollback()


def get_client_stats(user_id):
    """Get client statistics"""
    try:
        total_bookings = Booking.query.filter_by(user_id=user_id).count()
        pending_bookings = Booking.query.filter_by(user_id=user_id, status='pending').count()
        confirmed_bookings = Booking.query.filter_by(user_id=user_id, status='confirmed').count()
        completed_bookings = Booking.query.filter_by(user_id=user_id, status='completed').count()
        cancelled_bookings = Booking.query.filter_by(user_id=user_id, status='cancelled').count()

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_activity = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.created_at >= thirty_days_ago
        ).count()

        total_inquiries = Inquiry.query.filter_by(user_id=user_id).count()
        total_spent = 0

        return {
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'confirmed_bookings': confirmed_bookings,
            'completed_bookings': completed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'recent_activity': recent_activity,
            'total_inquiries': total_inquiries,
            'total_spent': total_spent
        }
    except Exception as e:
        logger.error(f"Error getting client stats: {str(e)}")
        return {}


def get_notification_count(user_id):
    """Get unread notification count"""
    try:
        pending = Booking.query.filter_by(user_id=user_id, status='pending').count()
        return pending
    except:
        return 0


# ============================================================
# DASHBOARD
# ============================================================

@client_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced client dashboard"""
    try:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))

        stats = get_client_stats(current_user.id)

        recent_bookings = Booking.query.filter_by(
            user_id=current_user.id
        ).order_by(Booking.created_at.desc()).limit(10).all()

        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        upcoming_events = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.event_date >= today,
            Booking.event_date <= thirty_days_later,
            Booking.status.in_(['pending', 'confirmed'])
        ).order_by(Booking.event_date.asc()).all()

        recent_inquiries = Inquiry.query.filter_by(
            user_id=current_user.id
        ).order_by(Inquiry.created_at.desc()).limit(5).all()

        services = Service.query.filter_by(is_active=True).order_by(Service.display_order).limit(6).all()
        notification_count = get_notification_count(current_user.id)

        return render_template('client/dashboard.html',
                               stats=stats,
                               recent_bookings=recent_bookings,
                               upcoming_events=upcoming_events,
                               recent_inquiries=recent_inquiries,
                               services=services,
                               notification_count=notification_count,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client dashboard: {str(e)}")
        flash('An error occurred loading your dashboard.', 'danger')
        return redirect(url_for('main.index'))


# ============================================================
# PROFILE
# ============================================================

@client_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Enhanced client profile page"""
    try:
        if current_user.is_admin():
            return redirect(url_for('admin.profile'))

        form = AdminProfileForm(obj=current_user)

        if form.validate_on_submit():
            existing_email = User.query.filter(
                User.email == form.email.data,
                User.id != current_user.id
            ).first()
            if existing_email:
                flash('Email already registered by another user.', 'danger')
                return render_template('client/profile.html', form=form)

            if form.username.data:
                existing_username = User.query.filter(
                    User.username == form.username.data,
                    User.id != current_user.id
                ).first()
                if existing_username:
                    flash('Username already taken.', 'danger')
                    return render_template('client/profile.html', form=form)

            current_user.email = form.email.data
            current_user.full_name = form.full_name.data
            current_user.phone = form.phone.data

            if form.username.data:
                current_user.username = form.username.data

            if form.new_password.data:
                if not form.current_password.data:
                    flash('Current password is required to change password.', 'danger')
                    return render_template('client/profile.html', form=form)

                if not current_user.check_password(form.current_password.data):
                    flash('Current password is incorrect.', 'danger')
                    return render_template('client/profile.html', form=form)

                current_user.set_password(form.new_password.data)
                log_activity(current_user.id, 'password_change', 'user', current_user.id, 'Password changed')

            current_user.updated_at = datetime.utcnow()
            db.session.commit()

            log_activity(current_user.id, 'profile_update', 'user', current_user.id, 'Profile updated')
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('client.profile'))

        return render_template('client/profile.html', form=form, client=current_user)
    except Exception as e:
        logger.error(f"Error in client profile: {str(e)}")
        flash('An error occurred loading your profile.', 'danger')
        return redirect(url_for('client.dashboard'))


# ============================================================
# BOOKINGS
# ============================================================

@client_bp.route('/bookings')
@login_required
def bookings():
    """View all client bookings with filtering"""
    try:
        if current_user.is_admin():
            return redirect(url_for('admin.bookings'))

        status_filter = request.args.get('status', '')
        event_type_filter = request.args.get('event_type', '')
        search_query = request.args.get('search', '')

        query = Booking.query.filter_by(user_id=current_user.id)

        if status_filter:
            query = query.filter_by(status=status_filter)

        if event_type_filter:
            query = query.filter_by(event_type=event_type_filter)

        if search_query:
            query = query.filter(
                or_(
                    Booking.client_name.ilike(f'%{search_query}%'),
                    Booking.event_type.ilike(f'%{search_query}%'),
                    Booking.event_location.ilike(f'%{search_query}%')
                )
            )

        bookings = query.order_by(Booking.created_at.desc()).all()

        event_types = db.session.query(Booking.event_type).filter_by(
            user_id=current_user.id
        ).distinct().all()
        event_types = [et[0] for et in event_types if et[0]]

        # FIXED: Properly calculate status counts
        status_counts = {}
        for status, _ in Booking.STATUSES:
            count = Booking.query.filter_by(
                user_id=current_user.id,
                status=status
            ).count()
            status_counts[status] = count

        return render_template('client/bookings.html',
                               bookings=bookings,
                               status_filter=status_filter,
                               event_type_filter=event_type_filter,
                               search_query=search_query,
                               event_types=event_types,
                               status_counts=status_counts,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client bookings: {str(e)}")
        flash('An error occurred loading your bookings.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.route('/booking/<int:id>')
@login_required
def booking_detail(id):
    """View booking details"""
    try:
        booking = Booking.query.get_or_404(id)

        if booking.user_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to view this booking.', 'danger')
            return redirect(url_for('client.bookings'))

        services = Service.query.filter_by(is_active=True).all() if current_user.is_admin() else None

        return render_template('client/booking_detail.html',
                               booking=booking,
                               services=services,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in booking_detail for id {id}: {str(e)}")
        flash('Booking not found.', 'danger')
        return redirect(url_for('client.bookings'))


@client_bp.route('/booking/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_booking(id):
    """Cancel a booking with reason"""
    try:
        booking = Booking.query.get_or_404(id)

        if booking.user_id != current_user.id:
            flash('You do not have permission to cancel this booking.', 'danger')
            return redirect(url_for('client.bookings'))

        if booking.status not in ['pending', 'confirmed']:
            flash('This booking cannot be cancelled. Only pending or confirmed bookings can be cancelled.', 'danger')
            return redirect(url_for('client.booking_detail', id=id))

        cancel_reason = request.form.get('cancel_reason', 'No reason provided')

        booking.status = 'cancelled'
        booking.updated_at = datetime.utcnow()
        booking.notes = f"Cancelled: {cancel_reason}\n\nPrevious notes: {booking.notes or ''}"
        db.session.commit()

        log_activity(
            current_user.id,
            'booking_cancel',
            'booking',
            booking.id,
            f'Booking cancelled: {cancel_reason}'
        )

        # Send cancellation notification
        try:
            from thabzo.services.email_service import send_booking_cancellation_email
            send_booking_cancellation_email(booking, cancel_reason)
        except Exception as e:
            logger.error(f'Failed to send cancellation email: {e}')
            flash('Booking cancelled but email notification failed.', 'warning')

        flash('Booking cancelled successfully.', 'success')
        return redirect(url_for('client.bookings'))
    except Exception as e:
        logger.error(f"Error in cancel_booking for id {id}: {str(e)}")
        db.session.rollback()
        flash('An error occurred cancelling the booking.', 'danger')
        return redirect(url_for('client.booking_detail', id=id))


@client_bp.route('/booking/<int:id>/reschedule', methods=['GET', 'POST'])
@login_required
def reschedule_booking(id):
    """Reschedule a booking"""
    try:
        booking = Booking.query.get_or_404(id)

        if booking.user_id != current_user.id:
            flash('You do not have permission to modify this booking.', 'danger')
            return redirect(url_for('client.bookings'))

        if booking.status not in ['pending', 'confirmed']:
            flash('This booking cannot be rescheduled.', 'danger')
            return redirect(url_for('client.booking_detail', id=id))

        if request.method == 'POST':
            new_date = request.form.get('event_date')
            new_time = request.form.get('event_time')
            new_venue = request.form.get('event_location')

            if not new_date:
                flash('Please select a new date.', 'danger')
                return render_template('client/reschedule_booking.html', booking=booking)

            try:
                booking.event_date = datetime.strptime(new_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'danger')
                return render_template('client/reschedule_booking.html', booking=booking)

            if new_time:
                booking.event_time = new_time

            if new_venue:
                booking.event_location = new_venue

            booking.updated_at = datetime.utcnow()

            reschedule_note = f"Rescheduled from previous date/time. New date: {booking.event_date}"
            if booking.notes:
                booking.notes = f"{booking.notes}\n\n{reschedule_note}"
            else:
                booking.notes = reschedule_note

            db.session.commit()

            log_activity(
                current_user.id,
                'booking_reschedule',
                'booking',
                booking.id,
                f'Booking rescheduled to {booking.event_date}'
            )

            # Send reschedule notification
            try:
                from thabzo.services.email_service import send_booking_reschedule_email
                send_booking_reschedule_email(booking)
            except Exception as e:
                logger.error(f'Failed to send reschedule email: {e}')
                flash('Booking rescheduled but email notification failed.', 'warning')

            flash('Booking rescheduled successfully. Our team will confirm the new date.', 'success')
            return redirect(url_for('client.booking_detail', id=booking.id))

        return render_template('client/reschedule_booking.html', booking=booking)
    except Exception as e:
        logger.error(f"Error in reschedule_booking for id {id}: {str(e)}")
        db.session.rollback()
        flash('An error occurred rescheduling the booking.', 'danger')
        return redirect(url_for('client.booking_detail', id=id))


@client_bp.route('/booking/new', methods=['GET', 'POST'])
@login_required
def new_booking():
    """Create a new booking"""
    try:
        form = BookingForm()

        if form.validate_on_submit():
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
                status='pending',
                user_id=current_user.id
            )

            db.session.add(booking)
            db.session.commit()

            log_activity(
                current_user.id,
                'booking_create',
                'booking',
                booking.id,
                f'New booking created for {booking.event_type} on {booking.event_date}'
            )

            # Send booking confirmation emails
            try:
                from thabzo.services.email_service import send_booking_notification, send_booking_confirmation
                send_booking_notification(booking)
                send_booking_confirmation(booking)
            except Exception as e:
                logger.error(f'Failed to send booking emails: {e}')

            flash('Booking created successfully! We will confirm your booking shortly.', 'success')
            return redirect(url_for('client.booking_detail', id=booking.id))

        # Pre-fill form with user data
        form.client_name.data = current_user.full_name
        form.client_email.data = current_user.email
        form.client_phone.data = current_user.phone

        return render_template('client/new_booking.html', form=form, client=current_user)
    except Exception as e:
        logger.error(f"Error in new_booking: {str(e)}")
        flash('An error occurred creating your booking.', 'danger')
        return redirect(url_for('client.dashboard'))


# ============================================================
# INQUIRIES
# ============================================================

@client_bp.route('/inquiries')
@login_required
def inquiries():
    """View all client inquiries with filtering"""
    try:
        if current_user.is_admin():
            return redirect(url_for('admin.inquiries'))

        status_filter = request.args.get('status', '')
        event_type_filter = request.args.get('event_type', '')
        search_query = request.args.get('search', '')

        query = Inquiry.query.filter_by(user_id=current_user.id)

        if status_filter:
            query = query.filter_by(status=status_filter)

        if event_type_filter:
            query = query.filter_by(event_type=event_type_filter)

        if search_query:
            query = query.filter(
                or_(
                    Inquiry.name.ilike(f'%{search_query}%'),
                    Inquiry.message.ilike(f'%{search_query}%'),
                    Inquiry.event_type.ilike(f'%{search_query}%')
                )
            )

        inquiries = query.order_by(Inquiry.created_at.desc()).all()

        event_types = db.session.query(Inquiry.event_type).filter_by(
            user_id=current_user.id
        ).distinct().all()
        event_types = [et[0] for et in event_types if et[0]]

        # FIXED: Properly calculate status counts
        status_counts = {}
        for status in ['new', 'contacted', 'booked', 'archived']:
            count = Inquiry.query.filter_by(
                user_id=current_user.id,
                status=status
            ).count()
            status_counts[status] = count

        return render_template('client/inquiries.html',
                               inquiries=inquiries,
                               status_filter=status_filter,
                               event_type_filter=event_type_filter,
                               search_query=search_query,
                               event_types=event_types,
                               status_counts=status_counts,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client inquiries: {str(e)}")
        flash('An error occurred loading your inquiries.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.route('/inquiry/<int:id>')
@login_required
def inquiry_detail(id):
    """View inquiry details"""
    try:
        inquiry = Inquiry.query.get_or_404(id)

        if inquiry.user_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to view this inquiry.', 'danger')
            return redirect(url_for('client.inquiries'))

        return render_template('client/inquiry_detail.html',
                               inquiry=inquiry,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in inquiry_detail for id {id}: {str(e)}")
        flash('Inquiry not found.', 'danger')
        return redirect(url_for('client.inquiries'))


@client_bp.route('/inquiry/new', methods=['GET', 'POST'])
@login_required
def new_inquiry():
    """Create a new inquiry"""
    try:
        form = InquiryForm()

        if form.validate_on_submit():
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                event_type=form.event_type.data,
                event_date=form.event_date.data,
                budget_range=form.budget_range.data,
                message=form.message.data,
                status='new',
                user_id=current_user.id
            )

            db.session.add(inquiry)
            db.session.commit()

            log_activity(
                current_user.id,
                'inquiry_create',
                'inquiry',
                inquiry.id,
                f'New inquiry created for {inquiry.event_type}'
            )

            # Send inquiry notification
            try:
                from thabzo.services.email_service import send_inquiry_email, send_inquiry_confirmation
                send_inquiry_email(inquiry)
                send_inquiry_confirmation(inquiry)
            except Exception as e:
                logger.error(f'Failed to send inquiry emails: {e}')
                flash('Inquiry submitted but email notification failed.', 'warning')

            flash('Your inquiry has been submitted! We will get back to you soon.', 'success')
            return redirect(url_for('client.inquiry_detail', id=inquiry.id))

        form.name.data = current_user.full_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone

        return render_template('client/new_inquiry.html', form=form, client=current_user)
    except Exception as e:
        logger.error(f"Error in new_inquiry: {str(e)}")
        flash('An error occurred submitting your inquiry.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.route('/inquiry/<int:id>/delete', methods=['POST'])
@login_required
def delete_inquiry(id):
    """Delete an inquiry"""
    try:
        inquiry = Inquiry.query.get_or_404(id)

        if inquiry.user_id != current_user.id:
            flash('You do not have permission to delete this inquiry.', 'danger')
            return redirect(url_for('client.inquiries'))

        if inquiry.status != 'new':
            flash('Only new inquiries can be deleted.', 'danger')
            return redirect(url_for('client.inquiry_detail', id=id))

        db.session.delete(inquiry)
        db.session.commit()

        log_activity(
            current_user.id,
            'inquiry_delete',
            'inquiry',
            id,
            'Inquiry deleted'
        )

        flash('Inquiry deleted successfully.', 'success')
        return redirect(url_for('client.inquiries'))
    except Exception as e:
        logger.error(f"Error in delete_inquiry for id {id}: {str(e)}")
        db.session.rollback()
        flash('An error occurred deleting the inquiry.', 'danger')
        return redirect(url_for('client.inquiries'))


# ============================================================
# TESTIMONIALS
# ============================================================

@client_bp.route('/testimonials')
@login_required
def testimonials():
    """View client testimonials"""
    try:
        user_testimonials = Testimonial.query.filter_by(
            client_name=current_user.full_name
        ).order_by(Testimonial.created_at.desc()).all()

        approved_testimonials = Testimonial.query.filter_by(
            is_approved=True
        ).order_by(Testimonial.created_at.desc()).limit(10).all()

        return render_template('client/testimonials.html',
                               user_testimonials=user_testimonials,
                               approved_testimonials=approved_testimonials,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client testimonials: {str(e)}")
        flash('An error occurred loading testimonials.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.route('/testimonial/new', methods=['GET', 'POST'])
@login_required
def new_testimonial():
    """Submit a new testimonial"""
    try:
        form = TestimonialForm()

        has_completed_booking = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status == 'completed'
        ).first() is not None

        if not has_completed_booking:
            flash('You need to have a completed booking before you can submit a testimonial.', 'warning')
            return redirect(url_for('client.testimonials'))

        existing = Testimonial.query.filter_by(
            client_name=current_user.full_name,
            is_approved=False
        ).first()

        if existing:
            flash('You have already submitted a testimonial. It is pending approval.', 'info')
            return redirect(url_for('client.testimonials'))

        if form.validate_on_submit():
            testimonial = Testimonial(
                client_name=form.client_name.data or current_user.full_name,
                event_type=form.event_type.data,
                content=form.content.data,
                rating=form.rating.data or 5,
                is_approved=False
            )

            db.session.add(testimonial)
            db.session.commit()

            log_activity(
                current_user.id,
                'testimonial_create',
                'testimonial',
                testimonial.id,
                'Testimonial submitted for approval'
            )

            flash('Thank you for your testimonial! It will be reviewed and published soon.', 'success')
            return redirect(url_for('client.testimonials'))

        form.client_name.data = current_user.full_name

        return render_template('client/new_testimonial.html',
                               form=form,
                               client=current_user,
                               has_completed_booking=has_completed_booking)
    except Exception as e:
        logger.error(f"Error in new_testimonial: {str(e)}")
        flash('An error occurred submitting your testimonial.', 'danger')
        return redirect(url_for('client.dashboard'))

# ============================================================
# NOTIFICATIONS
# ============================================================

@client_bp.route('/notifications')
@login_required
def notifications():
    """View client notifications"""
    try:
        pending_bookings = Booking.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).all()

        confirmed_bookings = Booking.query.filter_by(
            user_id=current_user.id,
            status='confirmed'
        ).all()

        new_inquiries = Inquiry.query.filter_by(
            user_id=current_user.id,
            status='new'
        ).all()

        return render_template('client/notifications.html',
                               pending_bookings=pending_bookings,
                               confirmed_bookings=confirmed_bookings,
                               new_inquiries=new_inquiries,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client notifications: {str(e)}")
        flash('An error occurred loading notifications.', 'danger')
        return redirect(url_for('client.dashboard'))


# ============================================================
# AJAX / API ENDPOINTS
# ============================================================

@client_bp.route('/api/booking/status/<int:id>', methods=['GET'])
@login_required
def api_booking_status(id):
    """Get booking status as JSON"""
    try:
        booking = Booking.query.get_or_404(id)

        if booking.user_id != current_user.id:
            return jsonify({'error': 'Permission denied'}), 403

        return jsonify({
            'id': booking.id,
            'status': booking.status,
            'event_type': booking.event_type,
            'event_date': booking.event_date.strftime('%Y-%m-%d') if booking.event_date else None,
            'updated_at': booking.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@client_bp.route('/api/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """Get dashboard statistics as JSON"""
    try:
        stats = get_client_stats(current_user.id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

@client_bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """Request account deletion"""
    try:
        active_bookings = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status.in_(['pending', 'confirmed'])
        ).first()

        if active_bookings:
            flash('You cannot delete your account while you have active bookings. Please cancel all bookings first.',
                  'danger')
            return redirect(url_for('client.settings'))

        current_user.is_active = False
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        log_activity(current_user.id, 'account_deactivate', 'user', current_user.id, 'Account deactivated')

        from flask_login import logout_user
        logout_user()

        flash('Your account has been deactivated. You can reactivate it by contacting us.', 'info')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error in delete_account: {str(e)}")
        db.session.rollback()
        flash('An error occurred deactivating your account.', 'danger')
        return redirect(url_for('client.settings'))


@client_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Client settings and preferences"""
    try:
        from thabzo.forms import ClientSettingsForm
        from thabzo.models import ClientSetting

        # Get or create client settings
        settings = ClientSetting.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = ClientSetting(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()

        form = ClientSettingsForm(obj=settings)

        # Handle POST requests
        if request.method == 'POST':
            # Check if it's an AJAX request
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

            if is_ajax:
                # Handle individual setting update via AJAX
                data = request.get_json()
                if data:
                    setting_key = data.get('key')
                    setting_value = data.get('value')

                    # Map frontend keys to model fields
                    field_map = {
                        'email_notifications': 'email_notifications',
                        'sms_notifications': 'sms_notifications',
                        'whatsapp_notifications': 'whatsapp_notifications',
                        'marketing_updates': 'marketing_updates',
                        'language': 'language',
                        'timezone': 'timezone',
                        'default_event_type': 'default_event_type',
                        'two_factor_auth': 'two_factor_auth',
                        'login_alerts': 'login_alerts'
                    }

                    if setting_key in field_map:
                        field_name = field_map[setting_key]
                        # Convert string 'true'/'false' to boolean for checkbox fields
                        if field_name in ['email_notifications', 'sms_notifications', 'whatsapp_notifications',
                                          'marketing_updates', 'two_factor_auth', 'login_alerts']:
                            setattr(settings, field_name, setting_value in ['true', True, 'on', 1])
                        else:
                            setattr(settings, field_name, setting_value)

                        settings.updated_at = datetime.utcnow()
                        db.session.commit()

                        log_activity(
                            current_user.id,
                            'settings_update',
                            'user',
                            current_user.id,
                            f'Setting {setting_key} updated to {setting_value}'
                        )

                        return jsonify({'success': True, 'message': 'Setting updated successfully'})

                    return jsonify({'success': False, 'error': 'Invalid setting key'}), 400

                return jsonify({'success': False, 'error': 'Invalid data'}), 400

            # Regular form submission - handle all settings at once
            print("=" * 60)
            print("📝 SAVING ALL SETTINGS")
            print("=" * 60)
            print(f"Form data: {dict(request.form)}")

            try:
                # Update all settings from form data
                settings.email_notifications = request.form.get('email_notifications') == 'on'
                settings.sms_notifications = request.form.get('sms_notifications') == 'on'
                settings.whatsapp_notifications = request.form.get('whatsapp_notifications') == 'on'
                settings.marketing_updates = request.form.get('marketing_updates') == 'on'
                settings.language = request.form.get('language', 'en')
                settings.timezone = request.form.get('timezone', 'SAST')
                settings.default_event_type = request.form.get('default_event_type')
                settings.two_factor_auth = request.form.get('two_factor_auth') == 'on'
                settings.login_alerts = request.form.get('login_alerts') == 'on'
                settings.updated_at = datetime.utcnow()

                db.session.commit()

                log_activity(
                    current_user.id,
                    'settings_update',
                    'user',
                    current_user.id,
                    'All settings updated'
                )

                print(f"✅ Settings saved successfully")
                print(f"   Email: {settings.email_notifications}")
                print(f"   SMS: {settings.sms_notifications}")
                print(f"   WhatsApp: {settings.whatsapp_notifications}")
                print(f"   Marketing: {settings.marketing_updates}")
                print(f"   Language: {settings.language}")
                print(f"   Timezone: {settings.timezone}")
                print(f"   Default Event: {settings.default_event_type}")
                print(f"   2FA: {settings.two_factor_auth}")
                print(f"   Login Alerts: {settings.login_alerts}")
                print("=" * 60)

                flash('Settings saved successfully!', 'success')
                return redirect(url_for('client.settings'))

            except Exception as e:
                db.session.rollback()
                print(f"❌ Error saving settings: {str(e)}")
                flash(f'Error saving settings: {str(e)}', 'danger')
                return redirect(url_for('client.settings'))

        # GET request - display settings
        # Get user's completed bookings for testimonial eligibility
        has_completed_booking = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status == 'completed'
        ).first() is not None

        return render_template('client/settings.html',
                               form=form,
                               settings=settings,
                               has_completed_booking=has_completed_booking,
                               client=current_user)

    except Exception as e:
        logger.error(f"Error in client settings: {str(e)}")
        db.session.rollback()
        flash('An error occurred loading settings.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.route('/settings/update', methods=['POST'])
@login_required
def update_setting_ajax():
    """Update a single setting via AJAX"""
    try:
        from thabzo.models import ClientSetting

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        setting_key = data.get('key')
        setting_value = data.get('value')

        if not setting_key:
            return jsonify({'success': False, 'error': 'No setting key provided'}), 400

        # Get or create settings
        settings = ClientSetting.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = ClientSetting(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()

        # Map frontend keys to model fields
        field_map = {
            'email_notifications': 'email_notifications',
            'sms_notifications': 'sms_notifications',
            'whatsapp_notifications': 'whatsapp_notifications',
            'marketing_updates': 'marketing_updates',
            'language': 'language',
            'timezone': 'timezone',
            'default_event_type': 'default_event_type',
            'two_factor_auth': 'two_factor_auth',
            'login_alerts': 'login_alerts'
        }

        if setting_key not in field_map:
            return jsonify({'success': False, 'error': 'Invalid setting key'}), 400

        field_name = field_map[setting_key]

        # Convert value based on field type
        if field_name in ['email_notifications', 'sms_notifications', 'whatsapp_notifications',
                          'marketing_updates', 'two_factor_auth', 'login_alerts']:
            # Boolean fields
            setattr(settings, field_name, setting_value in ['true', True, 'on', 1, 'True'])
        else:
            # String fields
            setattr(settings, field_name, setting_value)

        settings.updated_at = datetime.utcnow()
        db.session.commit()

        print(f"✅ Setting updated: {setting_key} = {setting_value}")

        return jsonify({
            'success': True,
            'message': 'Setting updated successfully',
            'key': setting_key,
            'value': setting_value
        })

    except Exception as e:
        logger.error(f"Error updating setting: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# CONTACT & SUPPORT
# ============================================================

@client_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    """Client support page"""
    try:
        form = ContactForm()

        if form.validate_on_submit():
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data or current_user.phone,
                event_type='other',
                message=f"Support Request: {form.subject.data}\n\n{form.message.data}",
                status='new',
                user_id=current_user.id
            )

            db.session.add(inquiry)
            db.session.commit()

            log_activity(
                current_user.id,
                'support_request',
                'inquiry',
                inquiry.id,
                'Support request submitted'
            )

            # Send support email notification
            try:
                from thabzo.services.email_service import send_inquiry_email
                send_inquiry_email(inquiry)
            except Exception as e:
                logger.error(f'Failed to send support email: {e}')

            flash('Your support request has been submitted. We will get back to you within 24 hours.', 'success')
            return redirect(url_for('client.dashboard'))

        form.name.data = current_user.full_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone

        settings = SiteSetting.query.all()
        settings_dict = {s.key: s.value for s in settings}

        return render_template('client/support.html',
                               form=form,
                               settings=settings_dict,
                               client=current_user)
    except Exception as e:
        logger.error(f"Error in client support: {str(e)}")
        flash('An error occurred submitting your support request.', 'danger')
        return redirect(url_for('client.dashboard'))


@client_bp.context_processor
def inject_client_data():
    """Inject client data into all templates"""
    try:
        if current_user.is_authenticated and not current_user.is_admin():
            pending_count = Booking.query.filter_by(
                user_id=current_user.id,
                status='pending'
            ).count()
            return {
                'pending_bookings_count': pending_count,
                'notification_count': pending_count
            }
    except:
        pass
    return {
        'pending_bookings_count': 0,
        'notification_count': 0
    }
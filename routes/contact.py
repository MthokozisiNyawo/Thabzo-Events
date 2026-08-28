"""
THABZO EVENTS - Contact Routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from thabzo.forms import InquiryForm, ContactForm
from thabzo.models import Inquiry, db
from thabzo.services.email_service import send_inquiry_email, send_contact_email, send_inquiry_confirmation
from datetime import datetime
import logging

contact_bp = Blueprint('contact', __name__)
logger = logging.getLogger(__name__)


@contact_bp.route('/', methods=['GET', 'POST'])
def contact():
    """Contact page with inquiry form"""
    form = InquiryForm()

    if form.validate_on_submit():
        try:
            inquiry = Inquiry(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                event_type=form.event_type.data,
                event_date=form.event_date.data,
                budget_range=form.budget_range.data,
                message=form.message.data,
                status='new'
            )
            db.session.add(inquiry)
            db.session.commit()

            # Send emails (try but don't fail if email doesn't work)
            try:
                send_inquiry_email(inquiry)
                send_inquiry_confirmation(inquiry)
            except Exception as e:
                logger.error(f'Email send failed: {e}')
                # Don't show error to user, just log it

            flash('Thank you! Your inquiry has been received. We will contact you shortly.', 'success')
            return redirect(url_for('contact.contact'))

        except Exception as e:
            logger.error(f'Inquiry submission failed: {e}')
            db.session.rollback()
            flash('An error occurred. Please try again or contact us directly.', 'danger')

    return render_template('contact.html', form=form)


@contact_bp.route('/quick-contact', methods=['POST'])
def quick_contact():
    """AJAX endpoint for quick contact form"""
    try:
        data = request.get_json()

        required = ['name', 'email', 'phone', 'event_type']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400

        inquiry = Inquiry(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            event_type=data.get('event_type'),
            event_date=datetime.strptime(data.get('event_date'), '%Y-%m-%d').date() if data.get('event_date') else None,
            budget_range=data.get('budget_range'),
            message=data.get('message'),
            status='new'
        )
        db.session.add(inquiry)
        db.session.commit()

        try:
            send_inquiry_email(inquiry)
        except:
            pass

        return jsonify({'success': True, 'message': 'Inquiry submitted successfully'}), 201

    except Exception as e:
        logger.error(f'AJAX inquiry failed: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@contact_bp.route('/contact-form', methods=['POST'])
def contact_form():
    """Simple contact form submission"""
    form = ContactForm()
    if form.validate_on_submit():
        contact_data = {
            'name': form.name.data,
            'email': form.email.data,
            'phone': form.phone.data,
            'subject': form.subject.data,
            'message': form.message.data
        }

        try:
            send_contact_email(contact_data)
        except:
            pass

        flash('Thank you for your message. We will get back to you soon.', 'success')
        return redirect(url_for('contact.contact'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'danger')

    return redirect(url_for('contact.contact'))
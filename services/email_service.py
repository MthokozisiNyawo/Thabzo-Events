"""
THABZO EVENTS - Basic Email Service
Simple working email integration
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def send_email(to_email, subject, body, html_body=None):
    """
    Send email - basic working implementation
    """
    try:
        config = current_app.config

        # Get email config
        smtp_server = config.get('MAIL_SERVER', 'smtp.gmail.com')
        smtp_port = config.get('MAIL_PORT', 587)
        username = config.get('MAIL_USERNAME')
        password = config.get('MAIL_PASSWORD')
        sender = config.get('MAIL_DEFAULT_SENDER', username)

        # Check if email is configured
        if not username or not password:
            logger.warning('Email not configured - skipping send')
            return True

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = subject

        # Attach plain text
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Attach HTML if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Connect and send
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)
        server.send_message(msg)
        server.quit()

        logger.info(f'Email sent to {to_email}')
        return True

    except Exception as e:
        logger.error(f'Email send failed: {str(e)}')
        return False


def send_verification_email(user):
    """Send email verification link"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    verification_url = f"{base_url}/auth/verify-email/{user.email_verification_token}"

    subject = "Verify Your Email - THABZO EVENTS"
    body = f"""
Hello {user.full_name},

Welcome to THABZO EVENTS!

Please click the link below to verify your email address:
{verification_url}

This link expires in 7 days.

If you didn't create this account, please ignore this email.

Regards,
THABZO EVENTS Team
"""

    return send_email(user.email, subject, body)


def send_password_reset_email(user):
    """Send password reset link"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    reset_url = f"{base_url}/auth/reset-password/{user.reset_password_token}"

    subject = "Password Reset - THABZO EVENTS"
    body = f"""
Hello {user.full_name},

We received a request to reset your password.

Click the link below to reset your password:
{reset_url}

This link expires in 24 hours.

If you didn't request this, please ignore this email.

Regards,
THABZO EVENTS Team
"""

    return send_email(user.email, subject, body)


def send_welcome_email(user):
    """Send welcome email after registration"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

    subject = "Welcome to THABZO EVENTS!"
    body = f"""
Hello {user.full_name},

Welcome to THABZO EVENTS!

You can now:
- Book events online
- Manage your bookings
- Submit inquiries
- View our gallery

Login here: {base_url}/auth/login

Regards,
THABZO EVENTS Team
"""

    return send_email(user.email, subject, body)


def send_inquiry_email(inquiry):
    """Send inquiry notification to admin"""
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')

    subject = f"New Inquiry: {inquiry.name}"
    body = f"""
New inquiry received:

Name: {inquiry.name}
Email: {inquiry.email}
Phone: {inquiry.phone}
Event Type: {inquiry.event_type or 'Not specified'}
Event Date: {inquiry.event_date.strftime('%d %B %Y') if inquiry.event_date else 'Not specified'}
Budget: {inquiry.budget_range or 'Not specified'}

Message:
{inquiry.message or 'No message provided'}
"""

    return send_email(admin_email, subject, body)


def send_inquiry_confirmation(inquiry):
    """Send confirmation to inquiry submitter"""
    subject = "Thank You for Your Inquiry - THABZO EVENTS"
    body = f"""
Hello {inquiry.name},

Thank you for your inquiry!

We received your inquiry and will get back to you within 24-48 hours.

Summary:
Event Type: {inquiry.event_type or 'Not specified'}
Event Date: {inquiry.event_date.strftime('%d %B %Y') if inquiry.event_date else 'Not specified'}

Your Message:
{inquiry.message or 'No message'}

Regards,
THABZO EVENTS Team
"""

    return send_email(inquiry.email, subject, body)


def send_reply_email(inquiry, reply_message):
    """Send reply to inquiry"""
    subject = f"Response to Your Inquiry - THABZO EVENTS"
    body = f"""
Hello {inquiry.name},

Thank you for your inquiry.

{reply_message}

Regards,
THABZO EVENTS Team
"""

    return send_email(inquiry.email, subject, body)


def send_booking_notification(booking):
    """Send booking notification to admin"""
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')

    subject = f"New Booking: {booking.client_name}"
    body = f"""
New booking received:

Client: {booking.client_name}
Email: {booking.client_email}
Phone: {booking.client_phone}
Event Type: {booking.event_type}
Event Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
Time: {booking.event_time or 'TBD'}
Guests: {booking.number_of_guests or 'Not specified'}
Venue: {booking.event_location or 'Not specified'}

Special Requests:
{booking.special_requests or 'None'}
"""

    return send_email(admin_email, subject, body)


def send_booking_confirmation(booking):
    """Send booking confirmation to client"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

    subject = f"Booking Confirmation - THABZO EVENTS"
    body = f"""
Hello {booking.client_name},

Thank you for booking with THABZO EVENTS!

Booking Details:
- Booking ID: #{booking.id}
- Event Type: {booking.event_type}
- Event Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
- Time: {booking.event_time or 'TBD'}
- Guests: {booking.number_of_guests or 'Not specified'}

We will confirm your booking within 24-48 hours.

View your booking: {base_url}/client/booking/{booking.id}

Regards,
THABZO EVENTS Team
"""

    return send_email(booking.client_email, subject, body)


def send_booking_status_update(booking):
    """Send booking status update to client"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

    subject = f"Booking #{booking.id} Status Update - THABZO EVENTS"
    body = f"""
Hello {booking.client_name},

Your booking status has been updated.

Booking Details:
- Booking ID: #{booking.id}
- Event Type: {booking.event_type}
- Event Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
- New Status: {booking.status.upper()}

View your booking: {base_url}/client/booking/{booking.id}

If you have any questions, please contact us.

Regards,
THABZO EVENTS Team
"""

    return send_email(booking.client_email, subject, body)


def send_booking_reschedule_email(booking):
    """Send booking reschedule notification to admin"""
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

    subject = f"Booking #{booking.id} Reschedule Request"
    body = f"""
Booking reschedule request:

Client: {booking.client_name}
Email: {booking.client_email}
Phone: {booking.client_phone}
Event Type: {booking.event_type}
New Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
New Time: {booking.event_time or 'TBD'}
New Venue: {booking.event_location or 'TBD'}

Please review and confirm availability.

View booking: {base_url}/admin/booking/{booking.id}
"""

    return send_email(admin_email, subject, body)


def send_booking_cancellation_email(booking, reason):
    """Send booking cancellation notification to admin and client"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')

    # Send to admin
    admin_subject = f"Booking #{booking.id} Cancelled by Client"
    admin_body = f"""
Booking cancelled by client:

Client: {booking.client_name}
Email: {booking.client_email}
Phone: {booking.client_phone}
Event Type: {booking.event_type}
Event Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
Reason: {reason}

View: {base_url}/admin/booking/{booking.id}
"""
    send_email(admin_email, admin_subject, admin_body)

    # Send to client
    client_subject = f"Booking #{booking.id} Cancelled - THABZO EVENTS"
    client_body = f"""
Hello {booking.client_name},

Your booking has been cancelled.

Booking Details:
- Booking ID: #{booking.id}
- Event Type: {booking.event_type}
- Event Date: {booking.event_date.strftime('%d %B %Y') if booking.event_date else 'TBD'}
- Cancellation Reason: {reason}

If you believe this was a mistake or need to reschedule, please contact us immediately.

Regards,
THABZO EVENTS Team
"""

    return send_email(booking.client_email, client_subject, client_body)


def send_contact_email(contact_data):
    """Send contact form email to admin"""
    admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')

    subject = f"Contact Form: {contact_data.get('subject', 'No Subject')}"
    body = f"""
New contact form submission:

Name: {contact_data.get('name', 'Not provided')}
Email: {contact_data.get('email', 'Not provided')}
Phone: {contact_data.get('phone', 'Not provided')}
Subject: {contact_data.get('subject', 'Not provided')}

Message:
{contact_data.get('message', 'No message')}
"""

    return send_email(admin_email, subject, body)


def send_contact_confirmation(contact_data):
    """Send confirmation to contact form submitter"""
    subject = "Thank You for Contacting THABZO EVENTS"
    body = f"""
Hello {contact_data.get('name', 'Customer')},

Thank you for contacting THABZO EVENTS!

We received your message and will respond within 24-48 hours.

Summary:
Subject: {contact_data.get('subject', 'N/A')}
Message: {contact_data.get('message', 'No message')}

If you need immediate assistance, please call us.

Regards,
THABZO EVENTS Team
"""

    return send_email(contact_data.get('email'), subject, body)


def send_newsletter_welcome(subscriber):
    """Send welcome email to new subscriber"""
    base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

    subject = "Welcome to THABZO EVENTS Newsletter!"
    body = f"""
Hello {subscriber.name or 'Subscriber'},

Welcome to the THABZO EVENTS newsletter!

You'll now receive updates about:
- Upcoming events and special offers
- New services and packages
- Event inspiration and tips
- Exclusive discounts and promotions

Regards,
THABZO EVENTS Team
"""

    return send_email(subscriber.email, subject, body)


def test_email():
    """Test email configuration"""
    try:
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@thabzo.co.za')

        result = send_email(
            admin_email,
            "THABZO EVENTS - Email Test",
            f"This is a test email from THABZO EVENTS.\n\nSent at: {datetime.now()}\n\nIf you received this, email is working!"
        )

        if result:
            return True, "Test email sent successfully"
        else:
            return False, "Failed to send test email"

    except Exception as e:
        return False, f"Error: {str(e)}"
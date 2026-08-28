from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, session, jsonify
from flask_login import login_required, current_user
from thabzo.models import (
    User, TeamMember, Inquiry, Testimonial, GalleryImage,
    Service, ServiceLevel, Category, SiteSetting, EventAlbum, BlogPost, FAQ,
    Booking, AdminNotification, ActivityLog, Subscriber, BudgetRange,
    db
)
from thabzo.forms import (
    AdminProfileForm, TeamMemberForm, ServiceForm, ServiceLevelForm, CategoryForm,
    GalleryImageForm, MultipleGalleryImageForm, TestimonialForm,
    InquiryStatusForm, SiteSettingForm, EventAlbumForm,
    BlogPostForm, FAQForm, BudgetRangeForm,
    AdminLoginForm
)
from thabzo.utils.decorators import admin_required, super_admin_required
from thabzo.services.image_service import save_image, delete_image, get_image_url
from datetime import datetime, timedelta
import csv
import os
from io import StringIO
from flask import Response

admin_bp = Blueprint('admin', __name__)


# ==================== AUTHENTICATION ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login - redirects to unified login"""
    return redirect(url_for('auth.login'))


# ==================== DASHBOARD ====================

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    total_inquiries = Inquiry.query.count()
    new_inquiries = Inquiry.query.filter_by(status='new').count()
    contacted_inquiries = Inquiry.query.filter_by(status='contacted').count()
    booked_inquiries = Inquiry.query.filter_by(status='booked').count()

    total_users = User.query.count()
    total_team_members = TeamMember.query.count()
    active_team_members = TeamMember.query.filter_by(is_active=True).count()

    total_testimonials = Testimonial.query.count()
    pending_testimonials = Testimonial.query.filter_by(is_approved=False).count()

    total_gallery = GalleryImage.query.count()
    total_albums = EventAlbum.query.count()
    total_services = Service.query.filter_by(is_active=True).count()
    total_service_levels = ServiceLevel.query.filter_by(is_active=True).count()
    total_categories = Category.query.filter_by(is_active=True).count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status='pending').count()
    total_blog_posts = BlogPost.query.count()
    total_subscribers = Subscriber.query.count() if Subscriber else 0

    recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(10).all()

    # Chart data
    chart_labels = []
    chart_data = []
    today = datetime.utcnow().date()
    for i in range(13, -1, -1):
        date = today - timedelta(days=i)
        count = Inquiry.query.filter(
            db.func.date(Inquiry.created_at) == date.isoformat()
        ).count()
        chart_labels.append(date.strftime('%d %b'))
        chart_data.append(count)

    # Recent activity
    recent_activity = []

    for inquiry in recent_inquiries:
        recent_activity.append({
            'type': 'inquiry',
            'title': f'New inquiry from {inquiry.name}',
            'subtitle': getattr(inquiry, 'event_type', 'Inquiry'),
            'timestamp': inquiry.created_at,
            'url': url_for('admin.inquiry_detail', id=inquiry.id)
        })

    recent_testimonials = Testimonial.query.order_by(
        Testimonial.created_at.desc()
    ).limit(5).all()
    for testimonial in recent_testimonials:
        recent_activity.append({
            'type': 'testimonial',
            'title': f'Testimonial from {testimonial.client_name}',
            'subtitle': 'Pending approval' if not testimonial.is_approved else 'Approved',
            'timestamp': testimonial.created_at,
            'url': url_for('admin.testimonials')
        })

    recent_bookings = Booking.query.order_by(
        Booking.created_at.desc()
    ).limit(5).all()
    for booking in recent_bookings:
        recent_activity.append({
            'type': 'booking',
            'title': f'New booking from {booking.client_name}',
            'subtitle': f'Status: {booking.status}',
            'timestamp': booking.created_at,
            'url': url_for('admin.booking_detail', id=booking.id)
        })

    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]

    unread_notifications = AdminNotification.query.filter_by(is_read=False).count()

    return render_template('admin/dashboard.html',
                           total_inquiries=total_inquiries,
                           new_inquiries=new_inquiries,
                           contacted_inquiries=contacted_inquiries,
                           booked_inquiries=booked_inquiries,
                           total_users=total_users,
                           total_team_members=total_team_members,
                           active_team_members=active_team_members,
                           total_testimonials=total_testimonials,
                           pending_testimonials=pending_testimonials,
                           total_gallery=total_gallery,
                           total_albums=total_albums,
                           total_services=total_services,
                           total_service_levels=total_service_levels,
                           total_categories=total_categories,
                           total_bookings=total_bookings,
                           pending_bookings=pending_bookings,
                           total_blog_posts=total_blog_posts,
                           total_subscribers=total_subscribers,
                           recent_inquiries=recent_inquiries,
                           recent_activity=recent_activity,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           unread_notifications=unread_notifications)


# ==================== USER MANAGEMENT ====================

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/user/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:id>/role', methods=['POST'])
@login_required
@admin_required
def change_user_role(id):
    user = User.query.get_or_404(id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'client']:
        user.role = new_role
        db.session.commit()
        flash(f'User role changed to {new_role}.', 'success')
    else:
        flash('Invalid role.', 'danger')
    return redirect(url_for('admin.users'))


# ==================== TEAM MANAGEMENT ====================

@admin_bp.route('/team')
@login_required
@admin_required
def team():
    team_members = TeamMember.query.order_by(TeamMember.display_order).all()
    return render_template('admin/team.html', team_members=team_members)


@admin_bp.route('/team/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_team_member():
    form = TeamMemberForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            print("=" * 60)
            print("📝 ADDING TEAM MEMBER")
            print("=" * 60)

            member = TeamMember(
                name=form.name.data,
                position=form.position.data,
                bio=form.bio.data,
                email=form.email.data,
                phone=form.phone.data,
                facebook=form.facebook.data,
                twitter=form.twitter.data,
                instagram=form.instagram.data,
                linkedin=form.linkedin.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data
            )

            if form.photo.data and form.photo.data.filename:
                print(f"📸 Photo file: {form.photo.data.filename}")
                filename = save_image(form.photo.data, 'team', resize=(400, 400))
                if filename:
                    member.photo_filename = filename
                    member.photo_filepath = f'uploads/team/{filename}'
                    print(f"✅ Photo saved: {member.photo_filepath}")
                else:
                    print(f"❌ Failed to save photo")
                    flash('Failed to upload image. Please check file format and size.', 'warning')

            db.session.add(member)
            db.session.commit()
            print(f"✅ Team member added: {member.name}")
            print("=" * 60)
            flash('Team member added successfully!', 'success')
            return redirect(url_for('admin.team'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            flash(f'Error adding team member: {str(e)}', 'danger')

    return render_template('admin/team_form.html', form=form, title='Add Team Member')


@admin_bp.route('/team/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_team_member(id):
    member = TeamMember.query.get_or_404(id)
    form = TeamMemberForm(obj=member)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            print("=" * 60)
            print(f"📝 EDITING TEAM MEMBER: {member.name}")
            print("=" * 60)

            member.name = form.name.data
            member.position = form.position.data
            member.bio = form.bio.data
            member.email = form.email.data
            member.phone = form.phone.data
            member.facebook = form.facebook.data
            member.twitter = form.twitter.data
            member.instagram = form.instagram.data
            member.linkedin = form.linkedin.data
            member.display_order = form.display_order.data
            member.is_active = form.is_active.data
            member.updated_at = datetime.utcnow()

            if form.photo.data and form.photo.data.filename:
                print(f"📸 Updating photo: {form.photo.data.filename}")
                if member.photo_filename:
                    delete_image(member.photo_filename, 'team')
                    print(f"🗑️ Deleted old photo: {member.photo_filename}")

                filename = save_image(form.photo.data, 'team', resize=(400, 400))
                if filename:
                    member.photo_filename = filename
                    member.photo_filepath = f'uploads/team/{filename}'
                    print(f"✅ Photo updated: {member.photo_filepath}")
                else:
                    print(f"❌ Failed to update photo")
                    flash('Failed to upload image. Please check file format and size.', 'warning')

            db.session.commit()
            print(f"✅ Team member updated: {member.name}")
            print("=" * 60)
            flash('Team member updated successfully!', 'success')
            return redirect(url_for('admin.team'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            flash(f'Error updating team member: {str(e)}', 'danger')

    return render_template('admin/team_form.html', form=form, title='Edit Team Member', member=member)


@admin_bp.route('/team/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    try:
        if member.photo_filename:
            delete_image(member.photo_filename, 'team')
        db.session.delete(member)
        db.session.commit()
        flash('Team member deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting team member: {str(e)}', 'danger')
    return redirect(url_for('admin.team'))


@admin_bp.route('/team/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_team_member(id):
    member = TeamMember.query.get_or_404(id)
    member.is_active = not member.is_active
    db.session.commit()
    status = 'activated' if member.is_active else 'deactivated'
    flash(f'Team member {status} successfully.', 'success')
    return redirect(url_for('admin.team'))


# ==================== CATEGORIES ====================

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.type, Category.display_order).all()
    types = Category.TYPES
    return render_template('admin/categories.html', categories=categories, types=types)


@admin_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    form = CategoryForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            category = Category(
                name=form.name.data,
                slug=form.slug.data.lower().replace(' ', '-'),
                description=form.description.data,
                icon=form.icon.data,
                type=form.type.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data
            )
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'danger')

    return render_template('admin/category_form.html', form=form, title='Add Category')


@admin_bp.route('/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            category.name = form.name.data
            category.slug = form.slug.data.lower().replace(' ', '-')
            category.description = form.description.data
            category.icon = form.icon.data
            category.type = form.type.data
            category.display_order = form.display_order.data
            category.is_active = form.is_active.data
            category.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'danger')

    return render_template('admin/category_form.html', form=form, title='Edit Category', category=category)


@admin_bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/category/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_category(id):
    category = Category.query.get_or_404(id)
    category.is_active = not category.is_active
    db.session.commit()
    status = 'activated' if category.is_active else 'deactivated'
    flash(f'Category {status} successfully.', 'success')
    return redirect(url_for('admin.categories'))


# ==================== SERVICE LEVELS ====================

@admin_bp.route('/service-levels')
@login_required
@admin_required
def service_levels():
    levels = ServiceLevel.query.order_by(ServiceLevel.display_order).all()
    return render_template('admin/service_levels.html', levels=levels)


@admin_bp.route('/service-level/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service_level():
    form = ServiceLevelForm()

    service_id = request.args.get('service_id', type=int)
    if service_id and request.method == 'GET':
        form.service_id.data = service_id

    if request.method == 'POST' and form.validate_on_submit():
        try:
            level = ServiceLevel(
                name=form.name.data,
                slug=form.slug.data.lower().replace(' ', '-'),
                description=form.description.data,
                price=form.price.data,
                discount_percentage=form.discount_percentage.data,
                features=form.features.data,
                icon=form.icon.data,
                color=form.color.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                service_id=form.service_id.data if form.service_id.data != 0 else None
            )
            db.session.add(level)
            db.session.commit()
            flash('Service level added successfully!', 'success')
            return redirect(url_for('admin.service_levels'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding service level: {str(e)}', 'danger')

    return render_template('admin/service_level_form.html', form=form, title='Add Service Level')


@admin_bp.route('/service-level/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service_level(id):
    level = ServiceLevel.query.get_or_404(id)
    form = ServiceLevelForm(obj=level)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            level.name = form.name.data
            level.slug = form.slug.data.lower().replace(' ', '-')
            level.description = form.description.data
            level.price = form.price.data
            level.discount_percentage = form.discount_percentage.data
            level.features = form.features.data
            level.icon = form.icon.data
            level.color = form.color.data
            level.display_order = form.display_order.data
            level.is_active = form.is_active.data
            level.is_featured = form.is_featured.data
            level.service_id = form.service_id.data if form.service_id.data != 0 else None
            level.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Service level updated successfully!', 'success')
            return redirect(url_for('admin.service_levels'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating service level: {str(e)}', 'danger')

    return render_template('admin/service_level_form.html', form=form, title='Edit Service Level', level=level)


@admin_bp.route('/service-level/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service_level(id):
    level = ServiceLevel.query.get_or_404(id)
    try:
        db.session.delete(level)
        db.session.commit()
        flash('Service level deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting service level: {str(e)}', 'danger')
    return redirect(url_for('admin.service_levels'))


@admin_bp.route('/service-level/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_service_level(id):
    level = ServiceLevel.query.get_or_404(id)
    level.is_active = not level.is_active
    db.session.commit()
    status = 'activated' if level.is_active else 'deactivated'
    flash(f'Service level {status} successfully.', 'success')
    return redirect(url_for('admin.service_levels'))


# ==================== SERVICES ====================

@admin_bp.route('/services')
@login_required
@admin_required
def services():
    all_services = Service.query.order_by(Service.display_order).all()
    categories = Category.query.filter_by(is_active=True, type='service').order_by(Category.display_order).all()
    return render_template('admin/services.html', services=all_services, categories=categories)


@admin_bp.route('/service/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    form = ServiceForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            category_id = form.category_id.data
            if category_id == 0:
                category_id = None

            service = Service(
                name=form.name.data,
                slug=form.slug.data.lower().replace(' ', '-'),
                description=form.description.data,
                icon=form.icon.data,
                starting_price=form.starting_price.data,
                is_active=form.is_active.data,
                display_order=form.display_order.data,
                category_id=category_id
            )
            db.session.add(service)
            db.session.commit()
            flash('Service added successfully.', 'success')
            return redirect(url_for('admin.services'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding service: {str(e)}', 'danger')

    return render_template('admin/service_form.html', form=form, title='Add Service')


@admin_bp.route('/service/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            category_id = form.category_id.data
            if category_id == 0:
                category_id = None

            service.name = form.name.data
            service.slug = form.slug.data.lower().replace(' ', '-')
            service.description = form.description.data
            service.icon = form.icon.data
            service.starting_price = form.starting_price.data
            service.is_active = form.is_active.data
            service.display_order = form.display_order.data
            service.category_id = category_id
            service.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Service updated successfully.', 'success')
            return redirect(url_for('admin.services'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating service: {str(e)}', 'danger')

    return render_template('admin/service_form.html', form=form, title='Edit Service', service=service)


@admin_bp.route('/service/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_service(id):
    service = Service.query.get_or_404(id)
    service.is_active = not service.is_active
    db.session.commit()
    status = 'activated' if service.is_active else 'deactivated'
    flash(f'Service {status} successfully.', 'success')
    return redirect(url_for('admin.services'))


@admin_bp.route('/service/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting service: {str(e)}', 'danger')
    return redirect(url_for('admin.services'))


# ==================== EVENT ALBUMS ====================

@admin_bp.route('/albums')
@login_required
@admin_required
def albums():
    albums = EventAlbum.query.order_by(EventAlbum.display_order).all()
    return render_template('admin/albums.html', albums=albums)


@admin_bp.route('/album/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_album():
    form = EventAlbumForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            print("=" * 60)
            print("📸 ADDING ALBUM")
            print("=" * 60)

            slug = form.slug.data or form.name.data.lower().replace(' ', '-')

            album = EventAlbum(
                name=form.name.data,
                slug=slug,
                description=form.description.data,
                event_type=form.event_type.data if form.event_type.data else None,
                event_date=form.event_date.data,
                is_featured=form.is_featured.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data
            )

            if form.cover_image.data and form.cover_image.data.filename:
                print(f"📸 Saving cover image: {form.cover_image.data.filename}")
                filename = save_image(form.cover_image.data, 'albums', resize=(1200, 800))
                if filename:
                    cover_image = GalleryImage(
                        title=f'Cover - {form.name.data}',
                        description=f'Cover image for {form.name.data}',
                        filename=filename,
                        filepath=get_image_url(filename, 'albums'),
                        is_featured=True,
                        display_order=0
                    )
                    db.session.add(cover_image)
                    db.session.flush()
                    album.cover_image_id = cover_image.id
                    print(f"✅ Cover image saved: {cover_image.filepath}")
                else:
                    print(f"❌ Failed to save cover image")

            db.session.add(album)
            db.session.commit()
            print(f"✅ Album added: {album.name}")
            print("=" * 60)
            flash('Event album created successfully!', 'success')
            return redirect(url_for('admin.albums'))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding album: {str(e)}")
            flash(f'Error creating album: {str(e)}', 'danger')

    return render_template('admin/album_form.html', form=form, title='Add Event Album')


@admin_bp.route('/album/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_album(id):
    album = EventAlbum.query.get_or_404(id)
    form = EventAlbumForm(obj=album)

    if request.method == 'POST':
        print(f"🔍 POST received for album {id}")
        print(f"🔍 Form data: {dict(request.form)}")

        if form.validate_on_submit():
            try:
                print("=" * 60)
                print(f"📸 EDITING ALBUM: {album.name}")
                print("=" * 60)

                album.name = form.name.data
                album.slug = form.slug.data or form.name.data.lower().replace(' ', '-')
                album.description = form.description.data
                album.event_type = form.event_type.data if form.event_type.data else None
                album.event_date = form.event_date.data
                album.is_featured = form.is_featured.data
                album.display_order = form.display_order.data
                album.is_active = form.is_active.data
                album.updated_at = datetime.utcnow()

                if form.cover_image.data and form.cover_image.data.filename:
                    print(f"📸 Updating cover image: {form.cover_image.data.filename}")
                    if album.cover_image_id:
                        old_cover = GalleryImage.query.get(album.cover_image_id)
                        if old_cover:
                            delete_image(old_cover.filename, 'albums')
                            db.session.delete(old_cover)
                            print(f"🗑️ Deleted old cover: {old_cover.filename}")

                    filename = save_image(form.cover_image.data, 'albums', resize=(1200, 800))
                    if filename:
                        cover_image = GalleryImage(
                            title=f'Cover - {form.name.data}',
                            description=f'Cover image for {form.name.data}',
                            filename=filename,
                            filepath=get_image_url(filename, 'albums'),
                            is_featured=True,
                            display_order=0,
                            album_id=album.id
                        )
                        db.session.add(cover_image)
                        db.session.flush()
                        album.cover_image_id = cover_image.id
                        print(f"✅ New cover saved: {cover_image.filepath}")
                    else:
                        print(f"❌ Failed to save cover image")
                        flash('Failed to upload cover image. Please check file format and size.', 'warning')

                db.session.commit()
                print(f"✅ Album updated: {album.name}")
                print("=" * 60)
                flash('Event album updated successfully!', 'success')
                return redirect(url_for('admin.albums'))

            except Exception as e:
                db.session.rollback()
                print(f"❌ Error updating album: {str(e)}")
                flash(f'Error updating album: {str(e)}', 'danger')
        else:
            print(f"❌ Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')

    return render_template('admin/album_form.html', form=form, title='Edit Event Album', album=album)


@admin_bp.route('/album/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_album(id):
    album = EventAlbum.query.get_or_404(id)
    try:
        for image in album.images:
            delete_image(image.filename, 'gallery')
            db.session.delete(image)

        if album.cover_image_id:
            cover = GalleryImage.query.get(album.cover_image_id)
            if cover:
                delete_image(cover.filename, 'albums')
                db.session.delete(cover)

        db.session.delete(album)
        db.session.commit()
        flash('Event album deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting album: {str(e)}', 'danger')
    return redirect(url_for('admin.albums'))


@admin_bp.route('/album/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_album(id):
    album = EventAlbum.query.get_or_404(id)
    album.is_active = not album.is_active
    db.session.commit()
    status = 'activated' if album.is_active else 'deactivated'
    flash(f'Album {status} successfully.', 'success')
    return redirect(url_for('admin.albums'))


@admin_bp.route('/album/<int:id>/view')
@login_required
@admin_required
def view_album(id):
    album = EventAlbum.query.get_or_404(id)
    images = GalleryImage.query.filter_by(album_id=id).order_by(GalleryImage.display_order).all()
    return render_template('admin/album_view.html', album=album, images=images)


# ==================== GALLERY IMAGES ====================

@admin_bp.route('/gallery')
@login_required
@admin_required
def gallery():
    images = GalleryImage.query.order_by(GalleryImage.display_order).all()
    categories = Category.query.filter_by(is_active=True, type='gallery').order_by(Category.display_order).all()
    albums = EventAlbum.query.filter_by(is_active=True).order_by(EventAlbum.display_order).all()
    return render_template('admin/gallery.html', images=images, categories=categories, albums=albums)


@admin_bp.route('/gallery/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_gallery_image():
    form = GalleryImageForm()

    if request.method == 'POST' and form.validate_on_submit():
        if form.image.data and form.image.data.filename:
            filename = save_image(form.image.data, 'gallery', resize=(1200, 800))
            if filename:
                image = GalleryImage(
                    title=form.title.data,
                    description=form.description.data,
                    filename=filename,
                    filepath=get_image_url(filename, 'gallery'),
                    category_id=form.category_id.data if form.category_id.data != 0 else None,
                    is_featured=form.is_featured.data,
                    display_order=form.display_order.data,
                    album_id=form.album_id.data if form.album_id.data != 0 else None
                )
                db.session.add(image)
                db.session.commit()
                flash('Image added to gallery successfully.', 'success')
                return redirect(url_for('admin.gallery'))
            else:
                flash('Failed to upload image. Please check file format.', 'danger')
        else:
            flash('Please select an image to upload.', 'danger')

    return render_template('admin/gallery_form.html', form=form, title='Add Image')


@admin_bp.route('/gallery/add-multiple', methods=['GET', 'POST'])
@login_required
@admin_required
def add_multiple_gallery_images():
    form = MultipleGalleryImageForm()

    if request.method == 'POST' and form.validate_on_submit():
        if form.images.data:
            uploaded_count = 0
            failed_count = 0

            album_id = form.album_id.data if form.album_id.data != 0 else None
            category_id = form.category_id.data if form.category_id.data != 0 else None

            if form.create_new_album.data and form.album_name.data:
                album = EventAlbum(
                    name=form.album_name.data,
                    slug=form.album_name.data.lower().replace(' ', '-'),
                    is_active=True
                )
                db.session.add(album)
                db.session.flush()
                album_id = album.id
                flash(f'New album "{album.name}" created!', 'success')

            for image_file in form.images.data:
                if image_file and image_file.filename:
                    filename = save_image(image_file, 'gallery', resize=(1200, 800))
                    if filename:
                        image = GalleryImage(
                            title=form.title.data or f'Image {uploaded_count + 1}',
                            description=form.description.data,
                            filename=filename,
                            filepath=get_image_url(filename, 'gallery'),
                            category_id=category_id,
                            is_featured=form.is_featured.data,
                            display_order=form.display_order.data + uploaded_count,
                            album_id=album_id
                        )
                        db.session.add(image)
                        uploaded_count += 1
                    else:
                        failed_count += 1

            if uploaded_count > 0:
                db.session.commit()
                flash(f'{uploaded_count} image(s) added to gallery successfully!', 'success')
                if failed_count > 0:
                    flash(f'{failed_count} image(s) failed to upload.', 'warning')
                return redirect(url_for('admin.gallery'))
            else:
                flash('Failed to upload images. Please check file formats.', 'danger')
        else:
            flash('Please select at least one image to upload.', 'danger')

    return render_template('admin/gallery_multiple_form.html', form=form, title='Upload Multiple Images')


@admin_bp.route('/gallery/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_gallery_image(id):
    image = GalleryImage.query.get_or_404(id)
    form = GalleryImageForm(obj=image)

    if request.method == 'POST' and form.validate_on_submit():
        image.title = form.title.data
        image.description = form.description.data
        image.category_id = form.category_id.data if form.category_id.data != 0 else None
        image.is_featured = form.is_featured.data
        image.display_order = form.display_order.data
        image.album_id = form.album_id.data if form.album_id.data != 0 else None

        if form.image.data and form.image.data.filename:
            delete_image(image.filename, 'gallery')
            filename = save_image(form.image.data, 'gallery', resize=(1200, 800))
            if filename:
                image.filename = filename
                image.filepath = get_image_url(filename, 'gallery')
            else:
                flash('Failed to upload new image. Keeping existing image.', 'warning')

        db.session.commit()
        flash('Image updated successfully.', 'success')
        return redirect(url_for('admin.gallery'))

    return render_template('admin/gallery_form.html', form=form, title='Edit Image', image=image)


@admin_bp.route('/gallery/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_gallery_image(id):
    image = GalleryImage.query.get_or_404(id)
    delete_image(image.filename, 'gallery')
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully.', 'success')
    return redirect(url_for('admin.gallery'))


@admin_bp.route('/gallery/<int:id>/feature', methods=['POST'])
@login_required
@admin_required
def feature_gallery_image(id):
    image = GalleryImage.query.get_or_404(id)
    image.is_featured = not image.is_featured
    db.session.commit()
    status = 'Featured' if image.is_featured else 'Unfeatured'
    flash(f'Image {status} successfully.', 'success')
    return redirect(url_for('admin.gallery'))


@admin_bp.route('/gallery/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_gallery_images():
    """Bulk delete gallery images"""
    image_ids = request.form.getlist('image_ids')

    if not image_ids:
        flash('No images selected for deletion.', 'warning')
        return redirect(url_for('admin.gallery'))

    deleted_count = 0
    failed_count = 0

    for image_id in image_ids:
        try:
            image = GalleryImage.query.get(int(image_id))
            if image:
                # Delete the physical file
                delete_image(image.filename, 'gallery')
                # Delete from database
                db.session.delete(image)
                deleted_count += 1
            else:
                failed_count += 1
        except Exception as e:
            current_app.logger.error(f'Error deleting image {image_id}: {e}')
            failed_count += 1

    try:
        db.session.commit()
        if deleted_count > 0:
            flash(f'{deleted_count} image(s) deleted successfully.', 'success')
        if failed_count > 0:
            flash(f'{failed_count} image(s) could not be deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Bulk delete error: {e}')
        flash('An error occurred while deleting images.', 'danger')

    return redirect(url_for('admin.gallery'))

# ==================== INQUIRIES ====================

@admin_bp.route('/inquiries')
@login_required
@admin_required
def inquiries():
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '')

    query = Inquiry.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(
            db.or_(
                Inquiry.name.ilike(f'%{search_query}%'),
                Inquiry.email.ilike(f'%{search_query}%'),
                Inquiry.phone.ilike(f'%{search_query}%'),
                Inquiry.message.ilike(f'%{search_query}%')
            )
        )

    inquiries = query.order_by(Inquiry.created_at.desc()).all()

    counts = {
        'all': Inquiry.query.count(),
        'new': Inquiry.query.filter_by(status='new').count(),
        'contacted': Inquiry.query.filter_by(status='contacted').count(),
        'booked': Inquiry.query.filter_by(status='booked').count(),
        'archived': Inquiry.query.filter_by(status='archived').count()
    }

    return render_template('admin/inquiries.html',
                           inquiries=inquiries,
                           current_status=status_filter,
                           counts=counts,
                           search_query=search_query)


@admin_bp.route('/inquiry/<int:id>')
@login_required
@admin_required
def inquiry_detail(id):
    inquiry = Inquiry.query.get_or_404(id)
    form = InquiryStatusForm(obj=inquiry)
    return render_template('admin/inquiry_detail.html', inquiry=inquiry, form=form)


@admin_bp.route('/inquiry/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_inquiry(id):
    inquiry = Inquiry.query.get_or_404(id)
    form = InquiryStatusForm()

    if request.method == 'POST' and form.validate_on_submit():
        inquiry.status = form.status.data
        inquiry.notes = form.notes.data
        inquiry.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Inquiry updated successfully.', 'success')
    else:
        flash('Error updating inquiry.', 'danger')

    return redirect(url_for('admin.inquiry_detail', id=id))


@admin_bp.route('/inquiry/<int:id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_inquiry(id):
    inquiry = Inquiry.query.get_or_404(id)
    reply_message = request.form.get('reply_message', '').strip()

    if not reply_message:
        flash('Reply message cannot be empty.', 'danger')
        return redirect(url_for('admin.inquiry_detail', id=id))

    try:
        from thabzo.services.email_service import send_reply_email
        if send_reply_email(inquiry, reply_message):
            if inquiry.status == 'new':
                inquiry.status = 'contacted'
                db.session.commit()
            flash('Reply sent successfully!', 'success')
        else:
            flash('Failed to send reply. Please check email configuration.', 'danger')
    except Exception as e:
        current_app.logger.error(f'Reply email error: {str(e)}')
        flash('Error sending reply. Please try again.', 'danger')

    return redirect(url_for('admin.inquiry_detail', id=id))


@admin_bp.route('/inquiry/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_inquiry(id):
    inquiry = Inquiry.query.get_or_404(id)
    db.session.delete(inquiry)
    db.session.commit()
    flash('Inquiry deleted successfully.', 'success')
    return redirect(url_for('admin.inquiries'))


@admin_bp.route('/inquiries/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_inquiry_action():
    inquiry_ids = request.form.getlist('inquiry_ids')
    action = request.form.get('action')

    if not inquiry_ids:
        flash('No inquiries selected.', 'warning')
        return redirect(url_for('admin.inquiries'))

    if action == 'delete':
        Inquiry.query.filter(Inquiry.id.in_(inquiry_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'{len(inquiry_ids)} inquiries deleted successfully.', 'success')
    elif action in ['new', 'contacted', 'booked', 'archived']:
        Inquiry.query.filter(Inquiry.id.in_(inquiry_ids)).update(
            {'status': action, 'updated_at': datetime.utcnow()},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'{len(inquiry_ids)} inquiries updated to "{action}".', 'success')
    else:
        flash('Invalid action.', 'danger')

    return redirect(url_for('admin.inquiries'))


# ==================== BOOKINGS ====================

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    status_filter = request.args.get('status', 'all')
    query = Booking.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    bookings = query.order_by(Booking.created_at.desc()).all()

    counts = {
        'all': Booking.query.count(),
        'pending': Booking.query.filter_by(status='pending').count(),
        'confirmed': Booking.query.filter_by(status='confirmed').count(),
        'cancelled': Booking.query.filter_by(status='cancelled').count(),
        'completed': Booking.query.filter_by(status='completed').count()
    }

    return render_template('admin/bookings.html', bookings=bookings, current_status=status_filter, counts=counts)


@admin_bp.route('/booking/<int:id>')
@login_required
@admin_required
def booking_detail(id):
    booking = Booking.query.get_or_404(id)
    return render_template('admin/booking_detail.html', booking=booking)


@admin_bp.route('/booking/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_booking(id):
    """Update booking status and send email notification"""
    booking = Booking.query.get_or_404(id)
    status = request.form.get('status')
    notes = request.form.get('notes')

    if status:
        booking.status = status
        booking.updated_at = datetime.utcnow()
        booking.notes = notes or booking.notes

        try:
            from thabzo.services.email_service import send_booking_status_update
            send_booking_status_update(booking)
            flash(f'Booking status updated to {status}. Email notification sent to client.', 'success')
        except Exception as e:
            flash(f'Booking status updated to {status} but email notification failed.', 'warning')

        db.session.commit()

    return redirect(url_for('admin.booking_detail', id=id))


@admin_bp.route('/booking/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_booking(id):
    booking = Booking.query.get_or_404(id)
    try:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting booking: {str(e)}', 'danger')
    return redirect(url_for('admin.bookings'))


@admin_bp.route('/booking-calendar')
@login_required
@admin_required
def booking_calendar():
    """Booking calendar view"""
    bookings = Booking.query.all()
    events = []

    for booking in bookings:
        # Determine color based on status
        color_map = {
            'pending': '#f39c12',
            'confirmed': '#2ecc71',
            'cancelled': '#e74c3c',
            'completed': '#3498db'
        }

        # Create event object
        event = {
            'id': booking.id,
            'title': f'{booking.client_name} - {booking.event_type}',
            'start': booking.event_date.isoformat(),
            'status': booking.status,
            'color': color_map.get(booking.status, '#6c5ce7'),
            'url': url_for('admin.booking_detail', id=booking.id),
            'extendedProps': {
                'status': booking.status,
                'client_name': booking.client_name,
                'event_type': booking.event_type,
                'phone': booking.client_phone,
                'email': booking.client_email,
                'guests': booking.number_of_guests or 'N/A',
                'location': booking.event_location or 'TBD',
                'time': booking.event_time or 'TBD'
            }
        }

        # Add end date if available (for multi-day events)
        if booking.event_date:
            # For single day events, set end to same day + 1 day for full-day display
            from datetime import timedelta
            event['end'] = (booking.event_date + timedelta(days=1)).isoformat()
            event['allDay'] = True

        events.append(event)

    return render_template('admin/booking_calendar.html', events=events)

# ==================== TESTIMONIALS ====================

@admin_bp.route('/testimonials')
@login_required
@admin_required
def testimonials():
    filter_type = request.args.get('filter', 'all')
    query = Testimonial.query

    if filter_type == 'approved':
        query = query.filter_by(is_approved=True)
    elif filter_type == 'pending':
        query = query.filter_by(is_approved=False)

    all_testimonials = query.order_by(Testimonial.created_at.desc()).all()

    counts = {
        'all': Testimonial.query.count(),
        'approved': Testimonial.query.filter_by(is_approved=True).count(),
        'pending': Testimonial.query.filter_by(is_approved=False).count()
    }

    return render_template('admin/testimonials.html',
                           testimonials=all_testimonials,
                           current_filter=filter_type,
                           counts=counts)


@admin_bp.route('/testimonial/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_testimonial():
    form = TestimonialForm()

    if request.method == 'POST' and form.validate_on_submit():
        testimonial = Testimonial(
            client_name=form.client_name.data,
            event_type=form.event_type.data,
            content=form.content.data,
            rating=form.rating.data,
            is_approved=form.is_approved.data
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Testimonial added successfully.', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonial_form.html', form=form, title='Add Testimonial')


@admin_bp.route('/testimonial/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    form = TestimonialForm(obj=testimonial)

    if request.method == 'POST' and form.validate_on_submit():
        testimonial.client_name = form.client_name.data
        testimonial.event_type = form.event_type.data
        testimonial.content = form.content.data
        testimonial.rating = form.rating.data
        testimonial.is_approved = form.is_approved.data
        db.session.commit()
        flash('Testimonial updated successfully.', 'success')
        return redirect(url_for('admin.testimonials'))

    return render_template('admin/testimonial_form.html', form=form, title='Edit Testimonial', testimonial=testimonial)


@admin_bp.route('/testimonial/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    db.session.delete(testimonial)
    db.session.commit()
    flash('Testimonial deleted successfully.', 'success')
    return redirect(url_for('admin.testimonials'))


@admin_bp.route('/testimonial/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    testimonial.is_approved = not testimonial.is_approved
    db.session.commit()
    status = 'approved' if testimonial.is_approved else 'hidden'
    flash(f'Testimonial {status} successfully.', 'success')
    return redirect(url_for('admin.testimonials'))


# ==================== BLOG ====================

@admin_bp.route('/blog')
@login_required
@admin_required
def blog_posts():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@admin_bp.route('/blog/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_blog_post():
    form = BlogPostForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            slug = form.slug.data or form.title.data.lower().replace(' ', '-')
            existing = BlogPost.query.filter_by(slug=slug).first()
            if existing:
                slug = f"{slug}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            post = BlogPost(
                title=form.title.data,
                slug=slug,
                excerpt=form.excerpt.data,
                content=form.content.data,
                category=form.category.data,
                tags=form.tags.data,
                author=form.author.data or 'THABZO EVENTS',
                is_published=form.is_published.data,
                is_featured=form.is_featured.data,
                published_at=form.published_at.data if form.is_published.data else (
                    datetime.utcnow() if form.is_published.data else None)
            )

            if form.featured_image.data and form.featured_image.data.filename:
                filename = save_image(form.featured_image.data, 'blog', resize=(1200, 630))
                if filename:
                    post.featured_image = get_image_url(filename, 'blog')

            db.session.add(post)
            db.session.commit()
            flash('Blog post created successfully!', 'success')
            return redirect(url_for('admin.blog_posts'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating blog post: {str(e)}', 'danger')

    return render_template('admin/blog_form.html', form=form, title='Add Blog Post')


@admin_bp.route('/blog/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    form = BlogPostForm(obj=post)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            post.title = form.title.data
            post.slug = form.slug.data or form.title.data.lower().replace(' ', '-')
            post.excerpt = form.excerpt.data
            post.content = form.content.data
            post.category = form.category.data
            post.tags = form.tags.data
            post.author = form.author.data
            post.is_published = form.is_published.data
            post.is_featured = form.is_featured.data
            post.published_at = form.published_at.data if form.is_published.data else (
                datetime.utcnow() if form.is_published.data else None)
            post.updated_at = datetime.utcnow()

            if form.featured_image.data and form.featured_image.data.filename:
                if post.featured_image:
                    filename = post.featured_image.split('/')[-1]
                    delete_image(filename, 'blog')
                filename = save_image(form.featured_image.data, 'blog', resize=(1200, 630))
                if filename:
                    post.featured_image = get_image_url(filename, 'blog')

            db.session.commit()
            flash('Blog post updated successfully!', 'success')
            return redirect(url_for('admin.blog_posts'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating blog post: {str(e)}', 'danger')

    return render_template('admin/blog_form.html', form=form, title='Edit Blog Post', post=post)


@admin_bp.route('/blog/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    try:
        if post.featured_image:
            filename = post.featured_image.split('/')[-1]
            delete_image(filename, 'blog')
        db.session.delete(post)
        db.session.commit()
        flash('Blog post deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting blog post: {str(e)}', 'danger')
    return redirect(url_for('admin.blog_posts'))


@admin_bp.route('/blog/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    post.is_published = not post.is_published
    if post.is_published and not post.published_at:
        post.published_at = datetime.utcnow()
    db.session.commit()
    status = 'published' if post.is_published else 'unpublished'
    flash(f'Blog post {status} successfully.', 'success')
    return redirect(url_for('admin.blog_posts'))


# ==================== FAQS ====================

@admin_bp.route('/faqs')
@login_required
@admin_required
def faqs():
    faqs = FAQ.query.order_by(FAQ.category, FAQ.display_order).all()
    return render_template('admin/faqs.html', faqs=faqs)


@admin_bp.route('/faq/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_faq():
    form = FAQForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            faq = FAQ(
                question=form.question.data,
                answer=form.answer.data,
                category=form.category.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data
            )
            db.session.add(faq)
            db.session.commit()
            flash('FAQ added successfully!', 'success')
            return redirect(url_for('admin.faqs'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding FAQ: {str(e)}', 'danger')

    return render_template('admin/faq_form.html', form=form, title='Add FAQ')


@admin_bp.route('/faq/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_faq(id):
    faq = FAQ.query.get_or_404(id)
    form = FAQForm(obj=faq)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            faq.question = form.question.data
            faq.answer = form.answer.data
            faq.category = form.category.data
            faq.display_order = form.display_order.data
            faq.is_active = form.is_active.data
            faq.updated_at = datetime.utcnow()
            db.session.commit()
            flash('FAQ updated successfully!', 'success')
            return redirect(url_for('admin.faqs'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating FAQ: {str(e)}', 'danger')

    return render_template('admin/faq_form.html', form=form, title='Edit FAQ', faq=faq)


@admin_bp.route('/faq/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_faq(id):
    faq = FAQ.query.get_or_404(id)
    try:
        db.session.delete(faq)
        db.session.commit()
        flash('FAQ deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting FAQ: {str(e)}', 'danger')
    return redirect(url_for('admin.faqs'))


@admin_bp.route('/faq/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_faq(id):
    faq = FAQ.query.get_or_404(id)
    faq.is_active = not faq.is_active
    db.session.commit()
    status = 'activated' if faq.is_active else 'deactivated'
    flash(f'FAQ {status} successfully.', 'success')
    return redirect(url_for('admin.faqs'))


# ==================== SUBSCRIBERS ====================

@admin_bp.route('/subscribers')
@login_required
@admin_required
def subscribers():
    subscribers = Subscriber.query.order_by(Subscriber.subscribed_at.desc()).all()
    active_count = Subscriber.query.filter_by(is_active=True).count()
    total_count = Subscriber.query.count()
    return render_template('admin/subscribers.html',
                           subscribers=subscribers,
                           active_count=active_count,
                           total_count=total_count)


@admin_bp.route('/subscriber/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    subscriber.is_active = not subscriber.is_active
    if subscriber.is_active:
        subscriber.unsubscribed_at = None
    else:
        subscriber.unsubscribed_at = datetime.utcnow()
    db.session.commit()
    status = 'activated' if subscriber.is_active else 'deactivated'
    flash(f'Subscriber {status} successfully.', 'success')
    return redirect(url_for('admin.subscribers'))


@admin_bp.route('/subscriber/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    try:
        db.session.delete(subscriber)
        db.session.commit()
        flash('Subscriber deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting subscriber: {str(e)}', 'danger')
    return redirect(url_for('admin.subscribers'))


# ==================== PROFILE ====================

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    form = AdminProfileForm(obj=current_user)

    if request.method == 'POST' and form.validate_on_submit():
        existing_email = User.query.filter(
            User.email == form.email.data,
            User.id != current_user.id
        ).first()
        if existing_email:
            flash('Email already registered.', 'danger')
            return render_template('admin/profile.html', form=form)

        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.username = form.username.data or current_user.username

        if form.new_password.data:
            if not form.current_password.data or not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('admin/profile.html', form=form)
            current_user.set_password(form.new_password.data)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html', form=form)


# ==================== NOTIFICATIONS ====================

@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    notifications = AdminNotification.query.filter_by(user_id=current_user.id).order_by(
        AdminNotification.created_at.desc()).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return render_template('admin/notifications.html', notifications=notifications)


@admin_bp.route('/notification/<int:id>/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_notification_read(id):
    notification = AdminNotification.query.get_or_404(id)
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@admin_required
def mark_all_notifications_read():
    AdminNotification.query.filter_by(user_id=current_user.id).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('admin.notifications'))


# ==================== ACTIVITY LOGS ====================

@admin_bp.route('/activity-logs')
@login_required
@admin_required
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return render_template('admin/activity_logs.html', logs=logs)


# ==================== EXPORT DATA ====================

@admin_bp.route('/export/<string:entity>')
@login_required
@admin_required
def export_data(entity):
    import csv
    from io import StringIO
    from flask import Response

    data = []
    filename = f'{entity}_export_{datetime.now().strftime("%Y%m%d")}.csv'

    if entity == 'inquiries':
        data = Inquiry.query.all()
        headers = ['ID', 'Name', 'Email', 'Phone', 'Event Type', 'Event Date', 'Status', 'Created At']
        rows = [[d.id, d.name, d.email, d.phone, d.get_event_type_display(),
                 d.event_date.strftime('%Y-%m-%d') if d.event_date else '',
                 d.get_status_display(), d.created_at.strftime('%Y-%m-%d %H:%M')] for d in data]
    elif entity == 'bookings':
        data = Booking.query.all()
        headers = ['ID', 'Client Name', 'Email', 'Phone', 'Event Type', 'Event Date', 'Status', 'Created At']
        rows = [[d.id, d.client_name, d.client_email, d.client_phone, d.event_type,
                 d.event_date.strftime('%Y-%m-%d'), d.status, d.created_at.strftime('%Y-%m-%d %H:%M')] for d in data]
    elif entity == 'users':
        data = User.query.all()
        headers = ['ID', 'Name', 'Email', 'Phone', 'Role', 'Status', 'Created At']
        rows = [[d.id, d.full_name, d.email, d.phone or '', d.role,
                 'Active' if d.is_active else 'Inactive', d.created_at.strftime('%Y-%m-%d %H:%M')] for d in data]
    elif entity == 'services':
        data = Service.query.all()
        headers = ['ID', 'Name', 'Slug', 'Category', 'Price', 'Active', 'Created At']
        rows = [[d.id, d.name, d.slug, d.category.name if d.category else '',
                 d.starting_price or '', 'Yes' if d.is_active else 'No',
                 d.created_at.strftime('%Y-%m-%d %H:%M')] for d in data]
    elif entity == 'testimonials':
        data = Testimonial.query.all()
        headers = ['ID', 'Client Name', 'Event Type', 'Rating', 'Approved', 'Created At']
        rows = [[d.id, d.client_name, d.event_type or '', d.rating,
                 'Yes' if d.is_approved else 'No', d.created_at.strftime('%Y-%m-%d %H:%M')] for d in data]
    else:
        flash('Invalid export type.', 'danger')
        return redirect(url_for('admin.dashboard'))

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    writer.writerows(rows)

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={filename}'})


@admin_bp.route('/budget-ranges')
@login_required
@admin_required
def budget_ranges():
    """Manage budget ranges"""
    budget_ranges = BudgetRange.query.order_by(BudgetRange.display_order).all()
    return render_template('admin/budget_ranges.html', budget_ranges=budget_ranges)


@admin_bp.route('/budget-range/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_budget_range():
    """Add a new budget range"""
    form = BudgetRangeForm()

    if request.method == 'POST' and form.validate_on_submit():
        try:
            budget_range = BudgetRange(
                label=form.label.data,
                min_amount=form.min_amount.data,
                max_amount=form.max_amount.data,
                display_order=form.display_order.data,
                is_active=form.is_active.data
            )
            db.session.add(budget_range)
            db.session.commit()
            flash('Budget range added successfully!', 'success')
            return redirect(url_for('admin.budget_ranges'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding budget range: {str(e)}', 'danger')

    return render_template('admin/budget_range_form.html', form=form, title='Add Budget Range')


@admin_bp.route('/budget-range/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_budget_range(id):
    """Edit a budget range"""
    budget_range = BudgetRange.query.get_or_404(id)
    form = BudgetRangeForm(obj=budget_range)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            budget_range.label = form.label.data
            budget_range.min_amount = form.min_amount.data
            budget_range.max_amount = form.max_amount.data
            budget_range.display_order = form.display_order.data
            budget_range.is_active = form.is_active.data
            budget_range.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Budget range updated successfully!', 'success')
            return redirect(url_for('admin.budget_ranges'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating budget range: {str(e)}', 'danger')

    return render_template('admin/budget_range_form.html', form=form, title='Edit Budget Range',
                           budget_range=budget_range)


@admin_bp.route('/budget-range/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_budget_range(id):
    """Delete a budget range"""
    budget_range = BudgetRange.query.get_or_404(id)
    try:
        db.session.delete(budget_range)
        db.session.commit()
        flash('Budget range deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting budget range: {str(e)}', 'danger')
    return redirect(url_for('admin.budget_ranges'))


@admin_bp.route('/budget-range/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_budget_range(id):
    """Toggle budget range active status"""
    budget_range = BudgetRange.query.get_or_404(id)
    budget_range.is_active = not budget_range.is_active
    db.session.commit()
    status = 'activated' if budget_range.is_active else 'deactivated'
    flash(f'Budget range {status} successfully.', 'success')
    return redirect(url_for('admin.budget_ranges'))

# ==================== SETTINGS ====================

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@super_admin_required
def settings():
    form = SiteSettingForm()

    if request.method == 'GET':
        settings = SiteSetting.query.all()
        setting_dict = {s.key: s.value for s in settings}

        form.business_name.data = setting_dict.get('business_name', current_app.config.get('BUSINESS_NAME'))
        form.business_phone.data = setting_dict.get('business_phone', current_app.config.get('BUSINESS_PHONE'))
        form.business_phone_alt.data = setting_dict.get('business_phone_alt',
                                                        current_app.config.get('BUSINESS_PHONE_ALT'))
        form.business_location.data = setting_dict.get('business_location', current_app.config.get('BUSINESS_LOCATION'))
        form.whatsapp_number.data = setting_dict.get('whatsapp_number', current_app.config.get('WHATSAPP_NUMBER'))
        form.business_tagline.data = setting_dict.get('business_tagline', current_app.config.get('BUSINESS_TAGLINE'))
        form.business_motto.data = setting_dict.get('business_motto', current_app.config.get('BUSINESS_MOTTO'))
        form.about_content.data = setting_dict.get('about_content', '')
        form.hero_title.data = setting_dict.get('hero_title', '')
        form.hero_subtitle.data = setting_dict.get('hero_subtitle', '')
        form.footer_text.data = setting_dict.get('footer_text', '')

    if request.method == 'POST' and form.validate_on_submit():
        settings_data = {
            'business_name': form.business_name.data,
            'business_phone': form.business_phone.data,
            'business_phone_alt': form.business_phone_alt.data,
            'business_location': form.business_location.data,
            'whatsapp_number': form.whatsapp_number.data,
            'business_tagline': form.business_tagline.data,
            'business_motto': form.business_motto.data,
            'about_content': form.about_content.data,
            'hero_title': form.hero_title.data,
            'hero_subtitle': form.hero_subtitle.data,
            'footer_text': form.footer_text.data
        }

        for key, value in settings_data.items():
            setting = SiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = SiteSetting(key=key, value=value)
                db.session.add(setting)

        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html', form=form)


# ==================== DEBUG ROUTES ====================

@admin_bp.route('/debug-uploads')
@login_required
@admin_required
def debug_uploads():
    """Debug route to check upload directories"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    result = {
        'upload_folder': upload_folder,
        'exists': os.path.exists(upload_folder),
        'subdirs': {}
    }

    for subdir, path in current_app.config['UPLOAD_SUBDIRS'].items():
        result['subdirs'][subdir] = {
            'path': path,
            'exists': os.path.exists(path),
            'files': os.listdir(path) if os.path.exists(path) else []
        }

    return jsonify(result)


@admin_bp.route('/debug-team-images')
@login_required
@admin_required
def debug_team_images():
    """Debug route to check team member images"""
    members = TeamMember.query.all()
    result = []

    for m in members:
        file_exists = False
        full_path = None

        if m.photo_filepath:
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], m.photo_filepath)
            file_exists = os.path.exists(full_path)

        result.append({
            'id': m.id,
            'name': m.name,
            'photo_filename': m.photo_filename,
            'photo_filepath': m.photo_filepath,
            'full_path': full_path,
            'file_exists': file_exists,
            'upload_folder': current_app.config['UPLOAD_FOLDER']
        })

    return jsonify(result)


@admin_bp.route('/debug-file-locations')
@login_required
@admin_required
def debug_file_locations():
    """Debug file locations"""
    import os
    from flask import jsonify

    result = {
        'app_root_path': current_app.root_path,
        'static_folder': current_app.static_folder,
        'upload_folder': current_app.config.get('UPLOAD_FOLDER'),
        'upload_subdirs': current_app.config.get('UPLOAD_SUBDIRS', {}),
        'files': {}
    }

    for key, path in result['upload_subdirs'].items():
        result['files'][key] = {
            'path': path,
            'exists': os.path.exists(path),
            'files': os.listdir(path) if os.path.exists(path) else []
        }

    return jsonify(result)


@admin_bp.context_processor
def inject_sidebar_counts():
    """Inject sidebar count variables into all admin templates"""
    from thabzo.models import User, Inquiry, Booking, Testimonial, Subscriber, AdminNotification

    try:
        return {
            'total_users': User.query.count(),
            'new_inquiries': Inquiry.query.filter_by(status='new').count(),
            'pending_bookings': Booking.query.filter_by(status='pending').count(),
            'pending_testimonials': Testimonial.query.filter_by(is_approved=False).count(),
            'active_subscribers': Subscriber.query.filter_by(is_active=True).count(),
            'unread_notifications': AdminNotification.query.filter_by(
                is_read=False,
                user_id=current_user.id if current_user.is_authenticated else None
            ).count() if current_user.is_authenticated else 0
        }
    except Exception as e:
        # Handle case where tables might not exist yet
        return {
            'total_users': 0,
            'new_inquiries': 0,
            'pending_bookings': 0,
            'pending_testimonials': 0,
            'active_subscribers': 0,
            'unread_notifications': 0
        }
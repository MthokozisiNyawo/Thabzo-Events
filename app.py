from thabzo import create_app, db
from thabzo.models import User
from datetime import datetime, timezone
import os

# Get environment - default to production for deployment
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)


def create_admin_user():
    """Create admin user if it doesn't exist"""
    with app.app_context():
        try:
            admin_email = os.environ.get('ADMIN_EMAIL', 'thabzoevents@gmail.com')
            admin = User.query.filter_by(email=admin_email).first()

            if not admin:
                admin = User(
                    username='admin',
                    email=admin_email,
                    full_name='Administrator',
                    phone=os.environ.get('ADMIN_PHONE', '0765841224'),
                    role='admin',
                    is_active=True,
                    email_verified=True,
                    verified_at=datetime.now(timezone.UTC),
                    created_at=datetime.now(timezone.UTC),
                    updated_at=datetime.now(timezone.UTC)
                )
                admin_password = os.environ.get('ADMIN_PASSWORD', 'admin@123')
                admin.set_password(admin_password)

                db.session.add(admin)
                db.session.commit()
                print(f"✅ Admin user created successfully!")
                print(f"   Email: {admin_email}")
            else:
                print(f"✅ Admin user already exists: {admin_email}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")


def create_client_user():
    """Create a demo client user if it doesn't exist"""
    with app.app_context():
        try:
            client_email = os.environ.get('DEMO_CLIENT_EMAIL', 'client@example.com')
            client = User.query.filter_by(email=client_email).first()

            if not client:
                client = User(
                    username='client',
                    email=client_email,
                    full_name='Demo Client',
                    phone='0765841225',
                    role='client',
                    is_active=True,
                    email_verified=True,
                    verified_at=datetime.now(timezone.UTC),
                    created_at=datetime.now(timezone.UTC),
                    updated_at=datetime.now(timezone.UTC)
                )
                client_password = os.environ.get('DEMO_CLIENT_PASSWORD', 'client@123')
                client.set_password(client_password)

                db.session.add(client)
                db.session.commit()
                print(f"✅ Demo client user created successfully!")
                print(f"   Email: {client_email}")
            else:
                print(f"✅ Demo client user already exists: {client_email}")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating client user: {str(e)}")


# Create tables and admin user
with app.app_context():
    db.create_all()
    create_admin_user()
    create_client_user()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    print("\n" + "=" * 60)
    print("🚀 THABZO EVENTS Application Started")
    print("=" * 60)
    print(f"📍 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"🔗 URL: http://0.0.0.0:{port}")
    print(f"🗄️  Database: PostgreSQL" if 'postgresql' in str(
        app.config.get('SQLALCHEMY_DATABASE_URI', '')) else f"🗄️  Database: SQLite")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
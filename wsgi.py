
from app import app as application

# For Gunicorn
app = application

if __name__ == "__main__":
    app.run()
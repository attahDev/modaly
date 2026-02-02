import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'modaly-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'modaly.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Admin Credentials
    ADMIN_EMAIL = 'admin010@gmail.com'
    ADMIN_PASSWORD = 'admin1100'
    
    # Blog Settings
    POSTS_PER_PAGE = 6
    CATEGORIES = ['General', 'Education', 'Healthcare', 'Community', 'Events', 'News']

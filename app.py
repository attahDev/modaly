from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os
from flask_bootstrap import Bootstrap
from app_config import Config
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)
Bootstrap(app)

db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    category = db.Column(db.String(50), default='General')
    image_url = db.Column(db.String(500))
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def handle_image_upload(files, existing_url=None):
    if 'image_file' in files:
        file = files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return f"/static/uploads/{filename}"
    return existing_url


@app.context_processor
def inject_globals():
    return {'current_year': datetime.now().year}


# =============================================================================
# PUBLIC ROUTES
# =============================================================================

@app.route('/')
def index():
    recent_posts = BlogPost.query.filter_by(published=True)\
        .order_by(BlogPost.created_at.desc()).limit(3).all()
    return render_template('index.html', recent_posts=recent_posts)


@app.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    
    query = BlogPost.query.filter_by(published=True)
    if category:
        query = query.filter_by(category=category)
    
    posts = query.order_by(BlogPost.created_at.desc())\
        .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    categories = db.session.query(BlogPost.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return render_template('blog.html', posts=posts, categories=categories, current_category=category)


@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    
    if not post.published and 'user_id' not in session:
        return redirect(url_for('blog'))
    
    recent_posts = BlogPost.query.filter(
        BlogPost.id != post_id, BlogPost.published == True
    ).order_by(BlogPost.created_at.desc()).limit(3).all()
    
    return render_template('blog_post.html', post=post, recent_posts=recent_posts)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if name and email and message:
            msg = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Please fill in all required fields.', 'danger')

    return render_template('contact.html')


@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        amount = request.form.get('amount', '').strip()
        custom_amount = request.form.get('custom_amount', '').strip()
        message = request.form.get('message', '').strip()

        
        final_amount = 0
        try:
            if custom_amount:
                final_amount = float(custom_amount)
            elif amount:
                final_amount = float(amount)
        except (ValueError, TypeError):
            flash('Please enter a valid donation amount.', 'danger')
            return render_template('donate.html')

       
        if not name:
            flash('Please enter your name.', 'danger')
            return render_template('donate.html')
        elif not email:
            flash('Please enter your email address.', 'danger')
            return render_template('donate.html')
        elif final_amount <= 0:
            flash('Please select or enter a donation amount.', 'danger')
            return render_template('donate.html')

        
        donation = Donation(name=name, email=email, amount=final_amount, message=message)
        db.session.add(donation)
        db.session.commit()
        
        
        return render_template('donate_success.html', 
                             amount=f'{final_amount:.2f}',
                             email=email,
                             name=name)

    return render_template('donate.html')


@app.route('/media')
def media():
    return render_template('media.html')



# =============================================================================
# AUTH ROUTES
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# =============================================================================
# ADMIN ROUTES
# =============================================================================

@app.route('/admin')
@login_required
def admin_dashboard():
    recent_posts = BlogPost.query.order_by(BlogPost.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    recent_donations = Donation.query.order_by(Donation.created_at.desc()).limit(5).all()
    
    stats = {
        'total_posts': BlogPost.query.count(),
        'published_posts': BlogPost.query.filter_by(published=True).count(),
        'total_messages': ContactMessage.query.count(),
        'unread_messages': ContactMessage.query.filter_by(read=False).count(),
        'total_donations': Donation.query.count(),
        'donation_sum': db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    }
    
    return render_template('admin/dashboard.html', 
                          recent_posts=recent_posts, 
                          recent_messages=recent_messages,
                          recent_donations=recent_donations, 
                          stats=stats)


@app.route('/admin/posts')
@login_required
def admin_posts():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts)


@app.route('/admin/post/new', methods=['GET', 'POST'])
@login_required
def admin_new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category = request.form.get('category', 'General')
        image_url = request.form.get('image_url', '').strip()
        published = request.form.get('published') == 'on'

        uploaded_url = handle_image_upload(request.files)
        if uploaded_url:
            image_url = uploaded_url

        if title and content:
            post = BlogPost(
                title=title,
                content=content,
                excerpt=excerpt or content[:150] + '...',
                category=category,
                image_url=image_url,
                published=published
            )
            db.session.add(post)
            db.session.commit()
            flash('Blog post created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Title and content are required.', 'danger')

    return render_template('admin/post_form.html', post=None, categories=app.config['CATEGORIES'])


@app.route('/admin/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.excerpt = request.form.get('excerpt', '').strip() or post.content[:150] + '...'
        post.category = request.form.get('category', 'General')
        post.published = request.form.get('published') == 'on'
        
        uploaded_url = handle_image_upload(request.files)
        if uploaded_url:
            post.image_url = uploaded_url
        elif request.form.get('image_url', '').strip():
            post.image_url = request.form.get('image_url', '').strip()

        db.session.commit()
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/post_form.html', post=post, categories=app.config['CATEGORIES'])


@app.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/messages')
@login_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@app.route('/admin/message/<int:message_id>/read', methods=['POST'])
@login_required
def admin_mark_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))


@app.route('/admin/message/<int:message_id>/delete', methods=['POST'])
@login_required
def admin_delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('admin_messages'))


@app.route('/admin/donations')
@login_required
def admin_donations():
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    total = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    return render_template('admin/donations.html', donations=donations, total=total)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# =============================================================================
# INIT DATABASE
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).first():
            admin = User(email=app.config['ADMIN_EMAIL'])
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {app.config['ADMIN_EMAIL']}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
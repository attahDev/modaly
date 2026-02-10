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


class MediaCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  
    completion_date = db.Column(db.String(50)) 

    metric1_value = db.Column(db.String(50))  
    metric1_label = db.Column(db.String(100))  
    metric2_value = db.Column(db.String(50))
    metric2_label = db.Column(db.String(100))
    metric3_value = db.Column(db.String(50))
    metric3_label = db.Column(db.String(100))
    
    overview = db.Column(db.Text)
    services_provided = db.Column(db.Text)  
    
    published = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    images = db.relationship('MediaImage', backref='campaign', lazy=True, cascade='all, delete-orphan')
    
    def get_services_list(self):
        if self.services_provided:
            return [s.strip() for s in self.services_provided.split('\n') if s.strip()]
        return []
    
    def get_primary_image(self):
        if self.images:
            primary = next((img for img in self.images if img.is_primary), None)
            return primary or self.images[0]
        return None


class MediaImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('media_campaign.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)  # Primary image shown on card
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def handle_multiple_image_uploads(files_list):
    uploaded_urls = []
    
    for file in files_list:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_urls.append(f"/static/uploads/{filename}")
    
    return uploaded_urls



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


@app.route('/media')
def media():
    # Get all published campaigns, ordered by display order then date
    campaigns = MediaCampaign.query.filter_by(published=True)\
        .order_by(MediaCampaign.display_order.desc(), 
                 MediaCampaign.created_at.desc()).all()
    
    return render_template('media.html', campaigns=campaigns)


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


@app.route('/admin/media')
@login_required
def admin_media():
    campaigns = MediaCampaign.query.order_by(MediaCampaign.display_order.desc(), 
                                             MediaCampaign.created_at.desc()).all()
    return render_template('admin/media.html', campaigns=campaigns)


@app.route('/admin/media/new', methods=['GET', 'POST'])
@login_required
def admin_new_campaign():
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General')
        completion_date = request.form.get('completion_date', '').strip()
        
        # Metrics
        metric1_value = request.form.get('metric1_value', '').strip()
        metric1_label = request.form.get('metric1_label', '').strip()
        metric2_value = request.form.get('metric2_value', '').strip()
        metric2_label = request.form.get('metric2_label', '').strip()
        metric3_value = request.form.get('metric3_value', '').strip()
        metric3_label = request.form.get('metric3_label', '').strip()
        
        # Details
        overview = request.form.get('overview', '').strip()
        services_provided = request.form.get('services_provided', '').strip()
        
        # Status
        published = request.form.get('published') == 'on'
        featured = request.form.get('featured') == 'on'
        display_order = int(request.form.get('display_order', 0))
        
        if title and description:
            # Create campaign
            campaign = MediaCampaign(
                title=title,
                description=description,
                category=category,
                completion_date=completion_date,
                metric1_value=metric1_value,
                metric1_label=metric1_label,
                metric2_value=metric2_value,
                metric2_label=metric2_label,
                metric3_value=metric3_value,
                metric3_label=metric3_label,
                overview=overview,
                services_provided=services_provided,
                published=published,
                featured=featured,
                display_order=display_order
            )
            db.session.add(campaign)
            db.session.flush()  # Get campaign.id
            
            # Handle image uploads
            images = request.files.getlist('images')
            if images:
                for idx, file in enumerate(images):
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        # Create MediaImage
                        media_image = MediaImage(
                            campaign_id=campaign.id,
                            image_url=f"/static/uploads/{filename}",
                            display_order=idx,
                            is_primary=(idx == 0)  # First image is primary
                        )
                        db.session.add(media_image)
            
            db.session.commit()
            flash('Media campaign created successfully!', 'success')
            return redirect(url_for('admin_media'))
        else:
            flash('Title and description are required.', 'danger')
    
    categories = ['Education', 'Healthcare', 'Community', 'Environment']
    return render_template('admin/campaign_form.html', campaign=None, categories=categories)


@app.route('/admin/media/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_campaign(campaign_id):
    
    campaign = MediaCampaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        # Update basic info
        campaign.title = request.form.get('title', '').strip()
        campaign.description = request.form.get('description', '').strip()
        campaign.category = request.form.get('category', 'General')
        campaign.completion_date = request.form.get('completion_date', '').strip()
        
        # Update metrics
        campaign.metric1_value = request.form.get('metric1_value', '').strip()
        campaign.metric1_label = request.form.get('metric1_label', '').strip()
        campaign.metric2_value = request.form.get('metric2_value', '').strip()
        campaign.metric2_label = request.form.get('metric2_label', '').strip()
        campaign.metric3_value = request.form.get('metric3_value', '').strip()
        campaign.metric3_label = request.form.get('metric3_label', '').strip()
        
        # Update details
        campaign.overview = request.form.get('overview', '').strip()
        campaign.services_provided = request.form.get('services_provided', '').strip()
        
        # Update status
        campaign.published = request.form.get('published') == 'on'
        campaign.featured = request.form.get('featured') == 'on'
        campaign.display_order = int(request.form.get('display_order', 0))
        
        # Handle new image uploads
        images = request.files.getlist('images')
        if images and images[0].filename:  # Check if any images were uploaded
            # Get current max display order
            max_order = db.session.query(db.func.max(MediaImage.display_order))\
                .filter_by(campaign_id=campaign.id).scalar() or -1
            
            for idx, file in enumerate(images):
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    # Create MediaImage
                    media_image = MediaImage(
                        campaign_id=campaign.id,
                        image_url=f"/static/uploads/{filename}",
                        display_order=max_order + idx + 1,
                        is_primary=False
                    )
                    db.session.add(media_image)
        
        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('admin_media'))
    
    categories = ['Education', 'Healthcare', 'Community', 'Environment']
    return render_template('admin/campaign_form.html', campaign=campaign, categories=categories)


@app.route('/admin/media/<int:campaign_id>/delete', methods=['POST'])
@login_required
def admin_delete_campaign(campaign_id):
    
    campaign = MediaCampaign.query.get_or_404(campaign_id)
    
    # Delete associated image files from disk
    for image in campaign.images:
        try:
            # Extract filename from URL
            if image.image_url.startswith('/static/uploads/'):
                filename = image.image_url.replace('/static/uploads/', '')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
        except Exception:
            pass
    
    db.session.delete(campaign)  # Cascade will delete images from DB
    db.session.commit()
    flash('Campaign deleted successfully.', 'info')
    return redirect(url_for('admin_media'))


@app.route('/admin/media/image/<int:image_id>/delete', methods=['POST'])
@login_required
def admin_delete_campaign_image(image_id):

    image = MediaImage.query.get_or_404(image_id)
    campaign_id = image.campaign_id
    
    # Delete file from disk
    try:
        if image.image_url.startswith('/static/uploads/'):
            filename = image.image_url.replace('/static/uploads/', '')
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception:
        pass
    
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully.', 'info')
    return redirect(url_for('admin_edit_campaign', campaign_id=campaign_id))


@app.route('/admin/media/image/<int:image_id>/set-primary', methods=['POST'])
@login_required
def admin_set_primary_image(image_id):
    
    image = MediaImage.query.get_or_404(image_id)
    campaign_id = image.campaign_id
    
    # Remove primary flag from all images in this campaign
    MediaImage.query.filter_by(campaign_id=campaign_id).update({'is_primary': False})
    
    # Set this image as primary
    image.is_primary = True
    db.session.commit()
    
    flash('Primary image updated.', 'success')
    return redirect(url_for('admin_edit_campaign', campaign_id=campaign_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500




def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).first():
            admin = User(email=app.config['ADMIN_EMAIL'])
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()



def init_db_on_startup():
    """Initialize database on application startup - for Render deployment"""
    with app.app_context():
        try:
            print("=" * 60)
            print("INITIALIZING DATABASE...")
            print("=" * 60)
            
            # Create all tables including MediaCampaign and MediaImage
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Print all tables for verification
            print(f"✓ Available tables: {list(db.metadata.tables.keys())}")
            
            # Create admin user if doesn't exist
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            
            if admin_email and admin_password:
                existing_admin = User.query.filter_by(email=admin_email).first()
                
                if not existing_admin:
                    admin = User(email=admin_email)
                    admin.set_password(admin_password)
                    db.session.add(admin)
                    db.session.commit()
                    print(f"✓ Admin user created: {admin_email}")
                else:
                    print(f"✓ Admin user already exists: {admin_email}")
            else:
                print("⚠ Warning: ADMIN_EMAIL or ADMIN_PASSWORD not set in environment variables")
            
            # Verify MediaCampaign table exists
            try:
                campaign_count = MediaCampaign.query.count()
                print(f"✓ MediaCampaign table verified ({campaign_count} campaigns)")
            except Exception as e:
                print(f"⚠ Warning: Could not query MediaCampaign table: {e}")
            
            print("=" * 60)
            print("DATABASE INITIALIZATION COMPLETE!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ DATABASE INITIALIZATION ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()


# CRITICAL: Initialize database on startup (for production/Render)
init_db_on_startup()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
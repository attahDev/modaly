from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timezone
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


# =============================================================================
# MODELS
# =============================================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


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
    services_provided = db.Column(db.Text)  # newline-separated

    published = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    images = db.relationship('MediaImage', backref='campaign', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='MediaImage.display_order')
    videos = db.relationship('MediaVideo', backref='campaign', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='MediaVideo.display_order')

    def get_services_list(self):
        if self.services_provided:
            return [s.strip() for s in self.services_provided.split('\n') if s.strip()]
        return []

    def get_primary_image(self):
        primary = next((img for img in self.images if img.is_primary), None)
        return primary or (self.images[0] if self.images else None)


class MediaImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('media_campaign.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class MediaVideo(db.Model):
    """Uploaded video files OR embedded YouTube/Vimeo links."""
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('media_campaign.id'), nullable=False)
    video_url = db.Column(db.String(500), nullable=False)
    video_type = db.Column(db.String(20), default='upload')  # 'upload' | 'youtube' | 'vimeo'
    title = db.Column(db.String(200))
    caption = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def get_embed_url(self):
        """Return iframe-safe embed URL for YouTube / Vimeo."""
        if self.video_type == 'youtube':
            vid = self.video_url
            for prefix in ('https://www.youtube.com/watch?v=',
                           'https://youtu.be/',
                           'https://youtube.com/watch?v='):
                if vid.startswith(prefix):
                    vid = vid.replace(prefix, '').split('&')[0]
                    break
            return f'https://www.youtube.com/embed/{vid}'
        if self.video_type == 'vimeo':
            vid = self.video_url.rstrip('/').split('/')[-1]
            return f'https://player.vimeo.com/video/{vid}'
        return None  # uploaded files play via <video> tag

    def is_upload(self):
        return self.video_type == 'upload'


# =============================================================================
# HELPERS
# =============================================================================

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXT = {'mp4', 'mov', 'avi', 'webm', 'mkv'}


def allowed_file(filename):
    """Original helper — kept for blog post image uploads."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXT


def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXT


def save_upload(file):
    """Save a file to UPLOAD_FOLDER and return its public URL."""
    filename = secure_filename(file.filename)
    filename = f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return f"/static/uploads/{filename}"


def delete_upload(url):
    """Delete a file from disk given its /static/uploads/... URL."""
    try:
        if url and url.startswith('/static/uploads/'):
            path = os.path.join(app.config['UPLOAD_FOLDER'],
                                url.replace('/static/uploads/', ''))
            if os.path.exists(path):
                os.remove(path)
    except Exception as e:
        print(f'File delete warning: {e}')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def handle_image_upload(files, existing_url=None):
    """Single-image upload used by blog posts."""
    if 'image_file' in files:
        file = files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return f"/static/uploads/{filename}"
    return existing_url


@app.context_processor
def inject_globals():
    return {'current_year': datetime.now(timezone.utc).year}


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

    return render_template('blog.html', posts=posts, categories=categories,
                           current_category=category)


@app.route('/media')
def media():
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
                               email=email, name=name)
    return render_template('donate.html')


# =============================================================================
# AUTH
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
# ADMIN — DASHBOARD / BLOG / MESSAGES / DONATIONS
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
                title=title, content=content,
                excerpt=excerpt or content[:150] + '...',
                category=category, image_url=image_url, published=published
            )
            db.session.add(post)
            db.session.commit()
            flash('Blog post created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Title and content are required.', 'danger')
    return render_template('admin/post_form.html', post=None,
                           categories=app.config['CATEGORIES'])


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
    return render_template('admin/post_form.html', post=post,
                           categories=app.config['CATEGORIES'])


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
# ADMIN — MEDIA CAMPAIGNS
# =============================================================================

@app.route('/admin/media')
@login_required
def admin_media():
    campaigns = MediaCampaign.query\
        .order_by(MediaCampaign.display_order.desc(),
                  MediaCampaign.created_at.desc()).all()
    return render_template('admin/media.html', campaigns=campaigns)


# ── CREATE ────────────────────────────────────────────────────────────────────

@app.route('/admin/media/new', methods=['GET', 'POST'])
@login_required
def admin_new_campaign():
    categories = ['Education', 'Healthcare', 'Community', 'Environment']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('admin/campaign_form.html',
                                   campaign=None, categories=categories)

        campaign = MediaCampaign(
            title=title,
            description=description,
            category=request.form.get('category', 'General'),
            completion_date=request.form.get('completion_date', '').strip(),
            metric1_value=request.form.get('metric1_value', '').strip(),
            metric1_label=request.form.get('metric1_label', '').strip(),
            metric2_value=request.form.get('metric2_value', '').strip(),
            metric2_label=request.form.get('metric2_label', '').strip(),
            metric3_value=request.form.get('metric3_value', '').strip(),
            metric3_label=request.form.get('metric3_label', '').strip(),
            overview=request.form.get('overview', '').strip(),
            services_provided=request.form.get('services_provided', '').strip(),
            published=request.form.get('published') == 'on',
            featured=request.form.get('featured') == 'on',
            display_order=int(request.form.get('display_order', 0) or 0),
        )
        db.session.add(campaign)
        db.session.flush()  # get campaign.id before committing

        # Images
        for idx, f in enumerate(request.files.getlist('images')):
            if f and f.filename and allowed_image(f.filename):
                db.session.add(MediaImage(
                    campaign_id=campaign.id,
                    image_url=save_upload(f),
                    display_order=idx,
                    is_primary=(idx == 0),
                ))

        # Uploaded video files
        video_titles = request.form.getlist('video_title')
        for idx, f in enumerate(request.files.getlist('videos')):
            if f and f.filename and allowed_video(f.filename):
                db.session.add(MediaVideo(
                    campaign_id=campaign.id,
                    video_url=save_upload(f),
                    video_type='upload',
                    title=video_titles[idx] if idx < len(video_titles) else '',
                    display_order=idx,
                ))

        # External YouTube / Vimeo links
        ext_urls   = request.form.getlist('ext_video_url')
        ext_types  = request.form.getlist('ext_video_type')
        ext_titles = request.form.getlist('ext_video_title')
        vid_offset = len(request.files.getlist('videos'))
        for idx, url in enumerate(ext_urls):
            url = url.strip()
            if url:
                db.session.add(MediaVideo(
                    campaign_id=campaign.id,
                    video_url=url,
                    video_type=ext_types[idx] if idx < len(ext_types) else 'youtube',
                    title=ext_titles[idx] if idx < len(ext_titles) else '',
                    display_order=vid_offset + idx,
                ))

        db.session.commit()
        flash('Media campaign created successfully!', 'success')
        return redirect(url_for('admin_media'))

    return render_template('admin/campaign_form.html',
                           campaign=None, categories=categories)


# ── EDIT ──────────────────────────────────────────────────────────────────────

@app.route('/admin/media/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_campaign(campaign_id):
    campaign = MediaCampaign.query.get_or_404(campaign_id)
    categories = ['Education', 'Healthcare', 'Community', 'Environment']

    if request.method == 'POST':
        # Basic fields
        campaign.title = request.form.get('title', '').strip()
        campaign.description = request.form.get('description', '').strip()
        campaign.category = request.form.get('category', 'General')
        campaign.completion_date = request.form.get('completion_date', '').strip()
        campaign.metric1_value = request.form.get('metric1_value', '').strip()
        campaign.metric1_label = request.form.get('metric1_label', '').strip()
        campaign.metric2_value = request.form.get('metric2_value', '').strip()
        campaign.metric2_label = request.form.get('metric2_label', '').strip()
        campaign.metric3_value = request.form.get('metric3_value', '').strip()
        campaign.metric3_label = request.form.get('metric3_label', '').strip()
        campaign.overview = request.form.get('overview', '').strip()
        campaign.services_provided = request.form.get('services_provided', '').strip()
        campaign.published = request.form.get('published') == 'on'
        campaign.featured = request.form.get('featured') == 'on'
        campaign.display_order = int(request.form.get('display_order', 0) or 0)

        # New images
        max_img = max((img.display_order for img in campaign.images), default=-1)
        for idx, f in enumerate(request.files.getlist('images')):
            if f and f.filename and allowed_image(f.filename):
                db.session.add(MediaImage(
                    campaign_id=campaign.id,
                    image_url=save_upload(f),
                    display_order=max_img + idx + 1,
                    is_primary=False,
                ))

        # New uploaded video files
        video_titles = request.form.getlist('video_title')
        max_vid = max((v.display_order for v in campaign.videos), default=-1)
        for idx, f in enumerate(request.files.getlist('videos')):
            if f and f.filename and allowed_video(f.filename):
                db.session.add(MediaVideo(
                    campaign_id=campaign.id,
                    video_url=save_upload(f),
                    video_type='upload',
                    title=video_titles[idx] if idx < len(video_titles) else '',
                    display_order=max_vid + idx + 1,
                ))

        # New external links
        ext_urls   = request.form.getlist('ext_video_url')
        ext_types  = request.form.getlist('ext_video_type')
        ext_titles = request.form.getlist('ext_video_title')
        max_vid2   = max((v.display_order for v in campaign.videos), default=-1)
        for idx, url in enumerate(ext_urls):
            url = url.strip()
            if url:
                db.session.add(MediaVideo(
                    campaign_id=campaign.id,
                    video_url=url,
                    video_type=ext_types[idx] if idx < len(ext_types) else 'youtube',
                    title=ext_titles[idx] if idx < len(ext_titles) else '',
                    display_order=max_vid2 + idx + 1,
                ))

        try:
            campaign.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('Campaign updated successfully!', 'success')
            return redirect(url_for('admin_media'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Update error: {e}")
            flash(f'Update failed: {str(e)}', 'danger')
            return redirect(url_for('admin_edit_campaign', campaign_id=campaign.id))

    return render_template('admin/campaign_form.html',
                           campaign=campaign, categories=categories)


# ── DELETE CAMPAIGN ───────────────────────────────────────────────────────────

@app.route('/admin/media/<int:campaign_id>/delete', methods=['POST'])
@login_required
def admin_delete_campaign(campaign_id):
    campaign = MediaCampaign.query.get_or_404(campaign_id)
    for img in campaign.images:
        delete_upload(img.image_url)
    for vid in campaign.videos:
        if vid.is_upload():
            delete_upload(vid.video_url)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully.', 'info')
    return redirect(url_for('admin_media'))


# ── IMAGE ACTIONS ─────────────────────────────────────────────────────────────

@app.route('/admin/media/image/<int:image_id>/delete', methods=['POST'])
@login_required
def admin_delete_campaign_image(image_id):
    image = MediaImage.query.get_or_404(image_id)
    campaign_id = image.campaign_id
    delete_upload(image.image_url)
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted successfully.', 'info')
    return redirect(url_for('admin_edit_campaign', campaign_id=campaign_id))


@app.route('/admin/media/image/<int:image_id>/set-primary', methods=['POST'])
@login_required
def admin_set_primary_image(image_id):
    image = MediaImage.query.get_or_404(image_id)
    campaign_id = image.campaign_id
    MediaImage.query.filter_by(campaign_id=campaign_id).update({'is_primary': False})
    image.is_primary = True
    db.session.commit()
    flash('Primary image updated.', 'success')
    return redirect(url_for('admin_edit_campaign', campaign_id=campaign_id))


# ── VIDEO ACTIONS ─────────────────────────────────────────────────────────────

@app.route('/admin/media/video/<int:video_id>/delete', methods=['POST'])
@login_required
def admin_delete_campaign_video(video_id):
    video = MediaVideo.query.get_or_404(video_id)
    campaign_id = video.campaign_id
    if video.is_upload():
        delete_upload(video.video_url)
    db.session.delete(video)
    db.session.commit()
    flash('Video deleted successfully.', 'info')
    return redirect(url_for('admin_edit_campaign', campaign_id=campaign_id))


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(413)
def request_too_large(e):
    flash('File too large. Maximum size is 100MB.', 'danger')
    return redirect(request.referrer or url_for('admin_media'))


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# =============================================================================
# DATABASE INIT
# =============================================================================

def init_db_on_startup():
    """Auto-initialize database on startup (Render free tier compatible)."""
    with app.app_context():
        try:
            print("=" * 60)
            print("INITIALIZING DATABASE...")
            print("=" * 60)

            db.create_all()
            print(f"✓ Tables: {list(db.metadata.tables.keys())}")

            admin_email    = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')

            if admin_email and admin_password:
                existing_admin = User.query.filter_by(email=admin_email).first()
                if not existing_admin:
                    admin = User(email=admin_email)
                    admin.set_password(admin_password)
                    db.session.add(admin)
                    db.session.commit()
                    print(f"✓ Admin created: {admin_email}")
                else:
                    # Always sync password with what's in the environment
                    existing_admin.set_password(admin_password)
                    db.session.commit()
                    print(f"✓ Admin password synced: {admin_email}")
            else:
                print("⚠ ADMIN_EMAIL / ADMIN_PASSWORD not set")

            print("=" * 60)
            print("DATABASE READY")
            print("=" * 60)

        except Exception as e:
            print(f"❌ DB INIT ERROR: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()


init_db_on_startup()


if __name__ == '__main__':
    app.run(debug=True)
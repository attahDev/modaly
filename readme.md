# Modaly Website

A modern, responsive Flask website with blog functionality, admin dashboard, dark mode support, and smooth animations.

---

## Features

- Responsive design with Bootstrap 5
- Dark/Light mode toggle with system preference detection
- Blog system with full CRUD operations
- Admin dashboard with statistics
- Contact form with message management
- Donation tracking system
- Image upload support
- Smooth CSS animations
- SQLite database for data persistence
- Secure authentication with password hashing

---

## Project Structure

```
modaly-website/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── modaly.db                   # SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css          # Custom styles + animations
│   ├── js/
│   │   └── main.js            # Theme toggle + interactions
│   └── uploads/               # Uploaded images (auto-created)
└── templates/
    ├── base.html              # Base template with nav/footer
    ├── index.html             # Homepage
    ├── blog.html              # Blog listing
    ├── blog_post.html         # Single blog post
    ├── contact.html           # Contact form
    ├── donate.html            # Donation page
    ├── login.html             # Admin login
    ├── admin/
    │   ├── dashboard.html     # Admin dashboard
    │   ├── post_form.html     # Create/Edit post
    │   ├── messages.html      # View messages
    │   └── donations.html     # View donations
    └── errors/
        ├── 404.html           # Not found page
        └── 500.html           # Server error page
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Create Project Directory

```bash
mkdir modaly-website
cd modaly-website
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

### Step 5: Open in Browser

- **Website:** http://localhost:5000
- **Admin Login:** http://localhost:5000/login

---

## Admin Credentials

| Field    | Value              |
|----------|--------------------|
| Email    | admin010@gmail.com |
| Password | admin1100          |

---

## Configuration

### Environment Variables (Optional)

Create a `.env` file for production:

```env
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///modaly.db
DEBUG=False
```

### Changing Admin Credentials

Edit `config.py`:

```python
ADMIN_EMAIL = 'your-email@example.com'
ADMIN_PASSWORD = 'your-secure-password'
```

Then delete `modaly.db` and restart the app to recreate with new credentials.

---

## Deployment

### Option 1: PythonAnywhere (Free)

1. Create account at pythonanywhere.com
2. Upload files via Files tab
3. Create virtual environment in Bash console
4. Configure WSGI file to point to your app
5. Reload web app

### Option 2: Heroku

1. Add `Procfile`:
   ```
   web: gunicorn app:app
   ```

2. Add gunicorn to requirements:
   ```bash
   pip install gunicorn
   pip freeze > requirements.txt
   ```

3. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: VPS (DigitalOcean, Linode, etc.)

1. Install Python and nginx
2. Clone your repository
3. Set up virtual environment
4. Configure gunicorn as service
5. Configure nginx as reverse proxy

---

## Usage Guide

### Adding a Blog Post

1. Log in at `/login`
2. Click "New Post" in dashboard
3. Fill in title, content, category
4. Upload image or paste image URL
5. Toggle "Publish" checkbox
6. Click "Create Post"

### Managing Messages

1. Go to Admin Dashboard
2. Click "View All" under Recent Messages
3. Click "View" to read full message
4. Click "Mark Read" to update status
5. Click "Reply via Email" to respond

### Dark Mode

- Click the moon/sun icon in the navigation
- Preference is saved in browser
- Automatically detects system preference on first visit

---

## Customization

### Changing Colors

Edit CSS variables in `static/css/style.css`:

```css
:root {
    --primary-color: #2563eb;
    --primary-dark: #1d4ed8;
    /* ... other variables */
}
```

### Adding Categories

Edit the categories list in `app.py`:

```python
CATEGORIES = ['General', 'Education', 'Healthcare', 'Community', 'Events', 'News', 'Your Category']
```

---

## Troubleshooting

### Database Errors

Delete `modaly.db` and restart the app:
```bash
rm modaly.db
python app.py
```

### Upload Errors

Ensure `static/uploads/` folder exists and is writable:
```bash
mkdir -p static/uploads
chmod 755 static/uploads
```

### Module Not Found

Ensure virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## License

MIT License - Feel free to use and modify for your projects.

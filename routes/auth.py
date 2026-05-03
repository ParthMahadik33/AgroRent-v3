from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from config import LANGUAGE_NAMES, SUPPORTED_LANGUAGES
from database import get_db
from utils.translations import translate_text

bp = Blueprint('auth', __name__)

@bp.route('/set_language/<lang_code>')
def set_language(lang_code):
    """Update preferred language for the active session"""
    next_url = request.referrer or url_for('index')
    if lang_code in SUPPORTED_LANGUAGES:
        session['lang'] = lang_code
        g.current_locale = lang_code
        flash(
            translate_text('alerts.language_changed', locale=lang_code, language=LANGUAGE_NAMES[lang_code]),
            'success'
        )
    else:
        flash(translate_text('alerts.language_invalid'), 'warning')
    return redirect(next_url)

@bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/market')
def market():
    """Market overview page"""
    return render_template('market.html')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not name or not email or not password:
            flash(translate_text('auth.signup.missing_fields'), 'danger')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash(translate_text('auth.signup.short_password'), 'danger')
            return render_template('signup.html')
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            flash(translate_text('auth.signup.invalid_email'), 'danger')
            return render_template('signup.html')
        
        # Check if user already exists
        conn = get_db()
        existing_user = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()
        
        if existing_user:
            conn.close()
            flash(translate_text('auth.signup.email_exists'), 'danger')
            return render_template('signup.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        try:
            conn.execute(
                'INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)',
                (name, email, phone if phone else None, hashed_password)
            )
            conn.commit()
            conn.close()
            flash(translate_text('auth.signup.success'), 'success')
            return redirect(url_for('signin'))
        except Exception as e:
            conn.close()
            flash(translate_text('alerts.generic_error'), 'danger')
            return render_template('signup.html')
    
    return render_template('signup.html')

@bp.route('/signin', methods=['GET', 'POST'])
def signin():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        # Validation
        if not email or not password:
            flash(translate_text('auth.signin.missing_fields'), 'danger')
            return render_template('signin.html')
        
        # Check user credentials
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            # Set session
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash(translate_text('auth.signin.welcome', name=user['name']), 'success')
            return redirect(url_for('index'))
        else:
            flash(translate_text('auth.signin.invalid_credentials'), 'danger')
            return render_template('signin.html')
    
    return render_template('signin.html')

@bp.route('/signout')
def signout():
    """User logout"""
    session.clear()
    flash(translate_text('auth.signout.success'), 'success')
    return redirect(url_for('index'))

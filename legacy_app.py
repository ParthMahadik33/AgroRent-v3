from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify, g, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sqlite3
import os
from functools import wraps
from datetime import datetime, timedelta
import json
import io
import re
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(app)  # Enable CORS for chatbot API

SUPPORTED_LANGUAGES = ['en', 'hi', 'mr']
LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'हिन्दी',
    'mr': 'मराठी'
}
DEFAULT_LOCALE = 'en'


def load_translations():
    """Load translation dictionaries from i18n folder"""
    translations = {}
    for lang in SUPPORTED_LANGUAGES:
        path = os.path.join('i18n', f'{lang}.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
        except FileNotFoundError:
            translations[lang] = {}
    return translations


TRANSLATIONS = load_translations()


def get_translations():
    """Get translations, reloading in debug mode for development"""
    if app.debug:
        return load_translations()
    return TRANSLATIONS


def _get_translation_value(lang, key_parts):
    """Traverse translation dict and return value for key parts"""
    translations = get_translations()
    data = translations.get(lang, {})
    for part in key_parts:
        if isinstance(data, dict):
            data = data.get(part)
        else:
            data = None
        if data is None:
            break
    if data is None and lang != DEFAULT_LOCALE:
        return _get_translation_value(DEFAULT_LOCALE, key_parts)
    return data


def translate_text(key, locale=None, default=None, **kwargs):
    """Translate the provided key for the active locale"""
    if not key:
        return ''
    lang = locale or getattr(g, 'current_locale', None) or session.get('lang') or DEFAULT_LOCALE
    parts = key.split('.')
    value = _get_translation_value(lang, parts)
    if value is None:
        value = default if default is not None else _get_translation_value(DEFAULT_LOCALE, parts)
    if value is None:
        value = default if default is not None else key
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass
    return value


def select_locale():
    """Determine active locale for each request"""
    lang = session.get('lang')
    if lang in SUPPORTED_LANGUAGES:
        g.current_locale = lang
        return lang
    best_match = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
    selected = best_match or DEFAULT_LOCALE
    g.current_locale = selected
    return selected


babel = Babel(app, locale_selector=select_locale)


@app.context_processor
def inject_translation_helpers():
    """Expose translation helpers to templates"""
    return {
        't': translate_text,
        'current_locale': getattr(g, 'current_locale', DEFAULT_LOCALE),
        'supported_languages': SUPPORTED_LANGUAGES,
        'language_names': LANGUAGE_NAMES
    }

MECHANIC_SPECIALIZATIONS = [
    'Tractor',
    'Harvester',
    'Pump',
    'Sprayer',
    'Tiller',
    'General Farm Machinery'
]

MECHANIC_REQUEST_STATUSES = ['Pending', 'Accepted', 'Completed']

# Serve assets folder
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

# Serve uploads folder
@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)

# Database configuration
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'agrorent.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with users and listings tables"""
    conn = get_db()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Listings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            owner_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            contact_method TEXT NOT NULL,
            category TEXT NOT NULL,
            equipment_name TEXT NOT NULL,
            brand TEXT NOT NULL,
            year INTEGER,
            condition TEXT NOT NULL,
            power_spec TEXT,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            village_city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            landmark TEXT,
            service_radius TEXT NOT NULL,
            pricing_type TEXT NOT NULL,
            price REAL NOT NULL,
            min_duration TEXT,
            available_from DATE NOT NULL,
            available_till DATE,
            transport_included TEXT NOT NULL,
            transport_charge REAL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            rules TEXT,
            main_image TEXT,
            additional_images TEXT,
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Rentals table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS rentals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            listing_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Active',
            renter_address TEXT,
            location_of_use TEXT,
            contract_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (listing_id) REFERENCES listings(id)
        )
    ''')
    
    # Add new columns to existing rentals table if they don't exist
    try:
        cursor = conn.execute("PRAGMA table_info(rentals)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'renter_address' not in columns:
            conn.execute('ALTER TABLE rentals ADD COLUMN renter_address TEXT')
        if 'location_of_use' not in columns:
            conn.execute('ALTER TABLE rentals ADD COLUMN location_of_use TEXT')
        if 'contract_path' not in columns:
            conn.execute('ALTER TABLE rentals ADD COLUMN contract_path TEXT')
    except sqlite3.OperationalError:
        pass

    # Mechanics table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mechanics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            experience_years INTEGER,
            specialization TEXT NOT NULL,
            service_locations TEXT NOT NULL,
            base_charge REAL NOT NULL,
            description TEXT,
            is_available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Mechanic service requests table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mechanic_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mechanic_id INTEGER NOT NULL,
            farmer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mechanic_id) REFERENCES mechanics(id)
        )
    ''')
    
    # Notifications table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            related_id INTEGER,
            related_type TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Add phone column if it doesn't exist (for existing databases)
    try:
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'phone' not in columns:
            conn.execute('ALTER TABLE users ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Add status column to listings table if it doesn't exist (for existing databases)
    try:
        cursor = conn.execute("PRAGMA table_info(listings)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'status' not in columns:
            conn.execute('ALTER TABLE listings ADD COLUMN status TEXT DEFAULT "available"')
            # Update existing listings to have 'available' status
            conn.execute('UPDATE listings SET status = "available" WHERE status IS NULL')
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Add default listings if database is empty
def add_default_listings():
    """Add sample listings if database is empty"""
    conn = get_db()
    existing_listings = conn.execute('SELECT COUNT(*) as count FROM listings').fetchone()
    existing_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
    
    # Only add default listings if listings table is empty and at least one user exists
    if existing_listings['count'] == 0 and existing_users['count'] > 0:
        # Get first user ID
        first_user = conn.execute('SELECT id FROM users LIMIT 1').fetchone()
        user_id = first_user['id'] if first_user else 1
        # Sample listings data
        sample_listings = [
            {
                'user_id': user_id,
                'owner_name': 'Rajesh Kumar',
                'phone': '+91 9876543210',
                'email': 'rajesh@example.com',
                'contact_method': 'WhatsApp',
                'category': 'Tractor',
                'equipment_name': 'Mahindra 575 DI',
                'brand': 'Mahindra',
                'year': 2020,
                'condition': 'Good',
                'power_spec': '65 HP',
                'state': 'Maharashtra',
                'district': 'Pune',
                'village_city': 'Baramati',
                'pincode': '413102',
                'landmark': 'Near Bus Stand',
                'service_radius': 'within 25 km',
                'pricing_type': 'Per day',
                'price': 2500.0,
                'min_duration': '1 day',
                'available_from': '2024-01-01',
                'available_till': None,
                'transport_included': 'Yes',
                'transport_charge': None,
                'title': '65 HP Mahindra Tractor with Trolley',
                'description': 'Well-maintained Mahindra 575 DI tractor available for rent. Comes with trolley. Perfect for farming operations. Regular servicing done. Diesel by renter.',
                'rules': 'Diesel by renter. Operator must be provided. Advance payment required.',
                'main_image': None,
                'additional_images': None
            },
            {
                'user_id': user_id,
                'owner_name': 'Priya Sharma',
                'phone': '+91 9876543211',
                'email': 'priya@example.com',
                'contact_method': 'Call',
                'category': 'Harvester',
                'equipment_name': 'John Deere S685',
                'brand': 'John Deere',
                'year': 2019,
                'condition': 'Good',
                'power_spec': '450 HP',
                'state': 'Maharashtra',
                'district': 'Nashik',
                'village_city': 'Nashik',
                'pincode': '422001',
                'landmark': 'Near Agricultural College',
                'service_radius': 'within 30 km',
                'pricing_type': 'Per acre',
                'price': 3500.0,
                'min_duration': '5 acres',
                'available_from': '2024-01-01',
                'available_till': '2024-12-31',
                'transport_included': 'No',
                'transport_charge': 5000.0,
                'title': 'John Deere Combine Harvester',
                'description': 'High-capacity combine harvester suitable for wheat, rice, and soybean harvesting. Excellent condition with all attachments.',
                'rules': 'Minimum 5 acres. Fuel by renter. Experienced operator available at extra cost.',
                'main_image': None,
                'additional_images': None
            },
            {
                'user_id': user_id,
                'owner_name': 'Amit Patel',
                'phone': '+91 9876543212',
                'email': 'amit@example.com',
                'contact_method': 'WhatsApp',
                'category': 'Sprayer',
                'equipment_name': 'Mahindra 475 DI with Boom Sprayer',
                'brand': 'Mahindra',
                'year': 2021,
                'condition': 'New',
                'power_spec': '47 HP',
                'state': 'Gujarat',
                'district': 'Ahmedabad',
                'village_city': 'Ahmedabad',
                'pincode': '380001',
                'landmark': 'Near Highway',
                'service_radius': 'only local village',
                'pricing_type': 'Per hour',
                'price': 800.0,
                'min_duration': '4 hours',
                'available_from': '2024-01-01',
                'available_till': None,
                'transport_included': 'Yes',
                'transport_charge': None,
                'title': '47 HP Tractor with Boom Sprayer',
                'description': 'New Mahindra 475 DI tractor with advanced boom sprayer. Perfect for pesticide and fertilizer application. Very efficient and easy to operate.',
                'rules': 'Minimum 4 hours. Chemical/fertilizer by renter. Proper cleaning required after use.',
                'main_image': None,
                'additional_images': None
            },
            {
                'user_id': user_id,
                'owner_name': 'Sunita Devi',
                'phone': '+91 9876543213',
                'email': 'sunita@example.com',
                'contact_method': 'SMS',
                'category': 'Pump',
                'equipment_name': 'Kirloskar 5 HP Submersible Pump',
                'brand': 'Kirloskar',
                'year': 2022,
                'condition': 'Good',
                'power_spec': '5 HP',
                'state': 'Punjab',
                'district': 'Ludhiana',
                'village_city': 'Ludhiana',
                'pincode': '141001',
                'landmark': 'Near Canal',
                'service_radius': 'within 20 km',
                'pricing_type': 'Per day',
                'price': 1200.0,
                'min_duration': '1 day',
                'available_from': '2024-01-01',
                'available_till': None,
                'transport_included': 'No',
                'transport_charge': 500.0,
                'title': '5 HP Submersible Water Pump',
                'description': 'High-quality Kirloskar submersible pump for irrigation. Excellent water output. Well maintained and serviced regularly.',
                'rules': 'Electricity connection required. Proper installation needed. Deposit required.',
                'main_image': None,
                'additional_images': None
            },
            {
                'user_id': user_id,
                'owner_name': 'Vikram Singh',
                'phone': '+91 9876543214',
                'email': 'vikram@example.com',
                'contact_method': 'Call',
                'category': 'Tiller',
                'equipment_name': 'Maschio Gaspardo Rotavator',
                'brand': 'Maschio Gaspardo',
                'year': 2020,
                'condition': 'Good',
                'power_spec': '35 HP',
                'state': 'Haryana',
                'district': 'Karnal',
                'village_city': 'Karnal',
                'pincode': '132001',
                'landmark': 'Near Market',
                'service_radius': 'within 15 km',
                'pricing_type': 'Per acre',
                'price': 2000.0,
                'min_duration': '2 acres',
                'available_from': '2024-01-01',
                'available_till': None,
                'transport_included': 'Yes',
                'transport_charge': None,
                'title': 'Rotavator for Land Preparation',
                'description': 'Efficient rotavator for land preparation and tilling. Cuts through hard soil easily. Perfect for preparing seedbeds.',
                'rules': 'Minimum 2 acres. Tractor required (can be arranged separately).',
                'main_image': None,
                'additional_images': None
            },
            {
                'user_id': user_id,
                'owner_name': 'Lakshmi Nair',
                'phone': '+91 9876543215',
                'email': 'lakshmi@example.com',
                'contact_method': 'WhatsApp',
                'category': 'Seed Drill',
                'equipment_name': 'Mahindra Seed Drill 9 Row',
                'brand': 'Mahindra',
                'year': 2021,
                'condition': 'Good',
                'power_spec': '45 HP',
                'state': 'Kerala',
                'district': 'Thrissur',
                'village_city': 'Thrissur',
                'pincode': '680001',
                'landmark': 'Near Agricultural Office',
                'service_radius': 'within 25 km',
                'pricing_type': 'Per acre',
                'price': 1800.0,
                'min_duration': '1 acre',
                'available_from': '2024-01-01',
                'available_till': '2024-06-30',
                'transport_included': 'No',
                'transport_charge': 800.0,
                'title': '9 Row Seed Drill for Precision Sowing',
                'description': 'Modern seed drill for precise seed placement. Suitable for various crops. Well maintained and calibrated.',
                'rules': 'Seeds by renter. Proper calibration required. Advance booking preferred.',
                'main_image': None,
                'additional_images': None
            }
        ]
        
        # Insert sample listings
        for listing in sample_listings:
            conn.execute('''
                INSERT INTO listings (
                    user_id, owner_name, phone, email, contact_method,
                    category, equipment_name, brand, year, condition, power_spec,
                    state, district, village_city, pincode, landmark, service_radius,
                    pricing_type, price, min_duration, available_from, available_till,
                    transport_included, transport_charge, title, description, rules,
                    main_image, additional_images
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing['user_id'], listing['owner_name'], listing['phone'], listing['email'], listing['contact_method'],
                listing['category'], listing['equipment_name'], listing['brand'], listing['year'], listing['condition'], listing['power_spec'],
                listing['state'], listing['district'], listing['village_city'], listing['pincode'], listing['landmark'], listing['service_radius'],
                listing['pricing_type'], listing['price'], listing['min_duration'], listing['available_from'], listing['available_till'],
                listing['transport_included'], listing['transport_charge'], listing['title'], listing['description'], listing['rules'],
                listing['main_image'], listing['additional_images']
            ))
        
        conn.commit()
    conn.close()

# Add default listings on startup (only if empty)
add_default_listings()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash(translate_text('alerts.login_required'), 'warning')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/set_language/<lang_code>')
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

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/market')
def market():
    """Market overview page"""
    return render_template('market.html')

@app.route('/signup', methods=['GET', 'POST'])
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

@app.route('/signin', methods=['GET', 'POST'])
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

@app.route('/signout')
def signout():
    """User logout"""
    session.clear()
    flash(translate_text('auth.signout.success'), 'success')
    return redirect(url_for('index'))

@app.route('/rentdashboard')
@login_required
def rentdashboard():
    """Renting dashboard page"""
    return render_template('rentdashboard.html')

@app.route('/api/my_rentals')
@login_required
def get_my_rentals():
    """Get current user's rentals - filter out rejected rentals older than 5 days"""
    user_id = session['user_id']
    conn = get_db()
    today = datetime.now().date()
    five_days_ago = today - timedelta(days=5)
    
    rentals = conn.execute('''
        SELECT r.*, l.title, l.category, l.equipment_name, l.brand, l.main_image,
               l.price, l.pricing_type, l.state, l.district, l.village_city,
               l.owner_name, l.phone, l.contact_method
        FROM rentals r
        JOIN listings l ON r.listing_id = l.id
        WHERE r.user_id = ?
        AND NOT (r.status = 'Cancelled' AND date(r.created_at) < ?)
        ORDER BY r.created_at DESC
    ''', (user_id, five_days_ago.strftime('%Y-%m-%d'))).fetchall()
    conn.close()
    
    rentals_data = []
    
    for rental in rentals:
        end_date = datetime.strptime(rental['end_date'], '%Y-%m-%d').date()
        is_expired = end_date < today
        days_remaining = (end_date - today).days if not is_expired else 0
        
        # Map status to display text
        status = rental['status']
        if is_expired and status in ('Approved', 'Active'):
            status_display = 'Expired'
        elif status == 'Pending':
            status_display = 'Waiting for approval'
        elif status == 'Approved':
            status_display = 'Approved'
        elif status == 'Cancelled':
            status_display = 'Rejected'
        else:
            status_display = status
        
        rentals_data.append({
            'id': rental['id'],
            'listing_id': rental['listing_id'],
            'title': rental['title'],
            'category': rental['category'],
            'equipment_name': rental['equipment_name'],
            'brand': rental['brand'],
            'main_image': rental['main_image'],
            'start_date': rental['start_date'],
            'end_date': rental['end_date'],
            'days': rental['days'],
            'total_amount': rental['total_amount'],
            'status': rental['status'],
            'status_display': status_display,
            'days_remaining': days_remaining,
            'is_expired': is_expired,
            'price': rental['price'],
            'pricing_type': rental['pricing_type'],
            'location': f"{rental['village_city']}, {rental['district']}, {rental['state']}",
            'owner_name': rental['owner_name'],
            'phone': rental['phone'],
            'contact_method': rental['contact_method'],
            'created_at': rental['created_at'],
            'contract_path': rental['contract_path'] if rental['contract_path'] else None
        })
    
    return jsonify(rentals_data)

@app.route('/listdashboard')
@login_required
def listdashboard():
    """Listing dashboard page"""
    return render_template('listdashboard.html')

@app.route('/listing')
@login_required
def listing():
    """Create listing page"""
    # Check if editing mode
    editing_data = None
    editing_id = None
    if 'editing_listing_data' in session and 'editing_listing_id' in session:
        # Verify ownership before allowing edit
        user_id = session['user_id']
        session_editing_id = session.get('editing_listing_id')
        
        if session_editing_id:
            conn = get_db()
            listing = conn.execute('SELECT * FROM listings WHERE id = ? AND user_id = ?', (session_editing_id, user_id)).fetchone()
            conn.close()
            
            if listing:
                # Only allow editing if user owns the listing
                editing_data = session.pop('editing_listing_data', None)
                editing_id = session.pop('editing_listing_id', None)
            else:
                # Clear invalid session data
                session.pop('editing_listing_data', None)
                session.pop('editing_listing_id', None)
                flash(translate_text('listings.edit.forbidden'), 'danger')
    
    return render_template('listing.html', editing_data=editing_data, editing_id=editing_id)

@app.route('/create_listing', methods=['POST'])
@login_required
def create_listing():
    """Handle listing form submission (create or update)"""
    try:
        user_id = session['user_id']
        editing_id = request.form.get('editing_id')
        is_edit = editing_id and editing_id.strip()
        
        # Get form data
        owner_name = request.form.get('owner_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        contact_method = request.form.get('contact_method', '').strip()
        category = request.form.get('category', '').strip()
        equipment_name = request.form.get('equipment_name', '').strip()
        brand = request.form.get('brand', '').strip()
        year = request.form.get('year')
        condition = request.form.get('condition', '').strip()
        power_spec = request.form.get('power_spec', '').strip()
        state = request.form.get('state', '').strip()
        district = request.form.get('district', '').strip()
        village_city = request.form.get('village_city', '').strip()
        pincode = request.form.get('pincode', '').strip()
        landmark = request.form.get('landmark', '').strip()
        service_radius = request.form.get('service_radius', '').strip()
        pricing_type = request.form.get('pricing_type', '').strip()
        price = request.form.get('price', '0')
        min_duration = request.form.get('min_duration', '').strip()
        available_from = request.form.get('available_from', '').strip()
        available_till = request.form.get('available_till', '').strip()
        transport_included = request.form.get('transport_included', '').strip()
        transport_charge = request.form.get('transport_charge', '0')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        rules = request.form.get('rules', '').strip()
        
        conn = get_db()
        
        # If editing, verify ownership
        if is_edit:
            try:
                editing_id_int = int(editing_id)
            except (ValueError, TypeError):
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Invalid listing ID'
                }), 400
            
            listing = conn.execute('SELECT * FROM listings WHERE id = ? AND user_id = ?', (editing_id_int, user_id)).fetchone()
            if not listing:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Listing not found or you do not have permission to edit it'
                }), 403
        
        # Handle file uploads
        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        main_image_path = None
        if 'main_image' in request.files:
            main_image = request.files['main_image']
            if main_image.filename:
                # Delete old image if editing
                if is_edit and listing['main_image']:
                    try:
                        old_path = os.path.join('static', listing['main_image'])
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except:
                        pass
                
                filename = f"main_{user_id}_{int(os.urandom(4).hex(), 16)}.{main_image.filename.rsplit('.', 1)[1].lower()}"
                filepath = os.path.join(upload_folder, filename)
                main_image.save(filepath)
                main_image_path = f"uploads/{filename}"
            elif is_edit:
                # Keep existing image if no new one uploaded
                main_image_path = listing['main_image']
        
        additional_images_paths = []
        if 'additional_images' in request.files:
            files = request.files.getlist('additional_images')
            if files and any(f.filename for f in files):
                # Delete old additional images if editing
                if is_edit and listing['additional_images']:
                    try:
                        for img_path in listing['additional_images'].split(','):
                            old_path = os.path.join('static', img_path.strip())
                            if os.path.exists(old_path):
                                os.remove(old_path)
                    except:
                        pass
                
                for idx, file in enumerate(files):
                    if file.filename:
                        filename = f"add_{user_id}_{int(os.urandom(4).hex(), 16)}_{idx}.{file.filename.rsplit('.', 1)[1].lower()}"
                        filepath = os.path.join(upload_folder, filename)
                        file.save(filepath)
                        additional_images_paths.append(f"uploads/{filename}")
            elif is_edit and listing['additional_images']:
                # Keep existing images if no new ones uploaded
                additional_images_paths = listing['additional_images'].split(',')
        
        # Save to database
        if is_edit:
            # Update existing listing
            conn.execute('''
                UPDATE listings SET
                    owner_name = ?, phone = ?, email = ?, contact_method = ?,
                    category = ?, equipment_name = ?, brand = ?, year = ?, condition = ?, power_spec = ?,
                    state = ?, district = ?, village_city = ?, pincode = ?, landmark = ?, service_radius = ?,
                    pricing_type = ?, price = ?, min_duration = ?, available_from = ?, available_till = ?,
                    transport_included = ?, transport_charge = ?, title = ?, description = ?, rules = ?,
                    main_image = ?, additional_images = ?
                WHERE id = ? AND user_id = ?
            ''', (
                owner_name, phone, email if email else None, contact_method,
                category, equipment_name, brand, int(year) if year else None, condition, power_spec if power_spec else None,
                state, district, village_city, pincode, landmark if landmark else None, service_radius,
                pricing_type, float(price), min_duration if min_duration else None, available_from, available_till if available_till else None,
                transport_included, float(transport_charge) if transport_charge else None, title, description, rules if rules else None,
                main_image_path, ','.join(additional_images_paths) if additional_images_paths else None,
                editing_id_int, user_id
            ))
            message = 'Your listing has been updated successfully!'
        else:
            # Insert new listing
            conn.execute('''
                INSERT INTO listings (
                    user_id, owner_name, phone, email, contact_method,
                    category, equipment_name, brand, year, condition, power_spec,
                    state, district, village_city, pincode, landmark, service_radius,
                    pricing_type, price, min_duration, available_from, available_till,
                    transport_included, transport_charge, title, description, rules,
                    main_image, additional_images
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, owner_name, phone, email if email else None, contact_method,
                category, equipment_name, brand, int(year) if year else None, condition, power_spec if power_spec else None,
                state, district, village_city, pincode, landmark if landmark else None, service_radius,
                pricing_type, float(price), min_duration if min_duration else None, available_from, available_till if available_till else None,
                transport_included, float(transport_charge) if transport_charge else None, title, description, rules if rules else None,
                main_image_path, ','.join(additional_images_paths) if additional_images_paths else None
            ))
            message = 'Your equipment has been listed successfully!'
        
        # Commit transaction
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
    except Exception as e:
        # Rollback transaction on any error
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error saving listing: {str(e)}'
        }), 500
    finally:
        # Always close connection
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/renting')
@login_required
def renting():
    """Renting page with equipment listings"""
    return render_template('renting.html')

@app.route('/api/listings')
@login_required
def get_listings():
    """Get all available listings - machines should always be visible"""
    conn = get_db()
    # Get all listings - machines are always visible, availability is checked via calendar
    listings = conn.execute('''
        SELECT * FROM listings 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    listings_data = []
    for listing in listings:
        listings_data.append({
            'id': listing['id'],
            'title': listing['title'],
            'category': listing['category'],
            'equipment_name': listing['equipment_name'],
            'brand': listing['brand'],
            'price': listing['price'],
            'pricing_type': listing['pricing_type'],
            'state': listing['state'],
            'district': listing['district'],
            'village_city': listing['village_city'],
            'main_image': listing['main_image'],
            'condition': listing['condition'],
            'power_spec': listing['power_spec'],
            'service_radius': listing['service_radius'],
            'transport_included': listing['transport_included'],
            'transport_charge': listing['transport_charge'],
            'available_from': listing['available_from'],
            'available_till': listing['available_till']
        })
    
    return jsonify(listings_data)

@app.route('/api/listing/<int:listing_id>')
@login_required
def get_listing_details(listing_id):
    """Get detailed information about a specific listing"""
    conn = get_db()
    listing = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
    conn.close()
    
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    
    listing_data = dict(listing)
    # Parse additional images
    if listing_data['additional_images']:
        listing_data['additional_images'] = listing_data['additional_images'].split(',')
    else:
        listing_data['additional_images'] = []
    
    return jsonify(listing_data)

def check_date_conflict(listing_id, start_date, end_date, exclude_rental_id=None):
    """Check if the given date range conflicts with existing rentals"""
    conn = get_db()
    
    # Get all confirmed (Approved/Active) and pending rentals for this listing
    query = '''
        SELECT id, start_date, end_date, status
        FROM rentals 
        WHERE listing_id = ? 
        AND status IN ('Pending', 'Approved', 'Active')
    '''
    params = [listing_id]
    
    if exclude_rental_id:
        query += ' AND id != ?'
        params.append(exclude_rental_id)
    
    query += ' ORDER BY start_date'
    
    rentals = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    
    # Convert input dates
    requested_start = datetime.strptime(start_date, '%Y-%m-%d').date()
    requested_end = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Check for overlaps
    conflicts = []
    for rental in rentals:
        rental_start = datetime.strptime(rental['start_date'], '%Y-%m-%d').date()
        rental_end = datetime.strptime(rental['end_date'], '%Y-%m-%d').date()
        
        # Check if date ranges overlap
        if not (requested_end < rental_start or requested_start > rental_end):
            conflicts.append({
                'id': rental['id'],
                'start_date': rental['start_date'],
                'end_date': rental['end_date'],
                'status': rental['status']
            })
    
    return conflicts

@app.route('/api/listing/<int:listing_id>/availability')
@login_required
def get_listing_availability(listing_id):
    """Get booked dates for a specific listing (separated by status)"""
    conn = get_db()
    
    # Get all rentals for this listing with different statuses
    rentals = conn.execute('''
        SELECT start_date, end_date, status
        FROM rentals 
        WHERE listing_id = ? 
        AND status IN ('Pending', 'Approved', 'Active')
        ORDER BY start_date
    ''', (listing_id,)).fetchall()
    conn.close()
    
    pending_dates = []
    confirmed_dates = []
    
    for rental in rentals:
        start_date = rental['start_date']
        end_date = rental['end_date']
        status = rental['status']
        
        # Generate all dates in the range
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        current_date = start
        while current_date <= end:
            date_string = current_date.strftime('%Y-%m-%d')
            if status == 'Pending':
                if date_string not in pending_dates:
                    pending_dates.append(date_string)
            else:  # Approved or Active
                if date_string not in confirmed_dates:
                    confirmed_dates.append(date_string)
            current_date += timedelta(days=1)
    
    return jsonify({
        'pending_dates': pending_dates,
        'confirmed_dates': confirmed_dates
    })

@app.route('/rent_equipment', methods=['POST'])
@login_required
def rent_equipment():
    """Handle equipment rental request with conflict detection"""
    try:
        user_id = session['user_id']
        listing_id = request.form.get('listing_id')
        days = int(request.form.get('days', 0))
        start_date = request.form.get('start_date')
        
        if not listing_id or not days or not start_date:
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        # Get listing details to calculate total amount
        conn = get_db()
        listing = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
        
        if not listing:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Listing not found'
            }), 404
        
        # Check if user is trying to rent their own equipment
        if listing['user_id'] == user_id:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'You cannot rent your own equipment'
            }), 400
        
        # Calculate end date
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = start + timedelta(days=days)
        end_date = end.strftime('%Y-%m-%d')
        
        # Check for date conflicts with existing rentals
        conflicts = check_date_conflict(listing_id, start_date, end_date)
        
        if conflicts:
            # Check if any conflicts are confirmed (Approved/Active) - these are booked
            confirmed_conflicts = [c for c in conflicts if c['status'] in ('Approved', 'Active')]
            if confirmed_conflicts:
                conn.close()
                conflict_info = confirmed_conflicts[0]
                return jsonify({
                    'success': False,
                    'message': f'Selected dates are already booked ({conflict_info["start_date"]} to {conflict_info["end_date"]}). Please choose different dates.',
                    'conflict': True,
                    'booked': True
                }), 400
        
        # Validate date range against listing availability
        listing_available_from = datetime.strptime(listing['available_from'], '%Y-%m-%d').date()
        listing_available_till = datetime.strptime(listing['available_till'], '%Y-%m-%d').date() if listing['available_till'] else None
        
        requested_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        requested_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if requested_start_date < listing_available_from:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Start date must be on or after {listing["available_from"]}'
            }), 400
        
        if listing_available_till and requested_end_date > listing_available_till:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'End date must be on or before {listing["available_till"]}'
            }), 400
        
        # Calculate total amount
        price = listing['price']
        pricing_type = listing['pricing_type']
        # Handle None transport_charge - convert to 0 if None
        if listing['transport_included'] == 'No' and listing['transport_charge'] is not None:
            transport_charge = float(listing['transport_charge'])
        else:
            transport_charge = 0
        
        if pricing_type == 'Per day':
            total_amount = price * days
        elif pricing_type == 'Per hour':
            total_amount = price * days * 8  # Assuming 8 hours per day
        elif pricing_type == 'Per acre':
            total_amount = price * days  # Assuming days = acres
        else:
            total_amount = price  # Per season
        
        total_amount += transport_charge
        
        # Get additional rental information
        renter_address = request.form.get('renter_address', '').strip()
        location_of_use = request.form.get('location_of_use', '').strip()
        
        # Create rental record with 'Pending' status (provisionally held)
        cursor = conn.execute('''
            INSERT INTO rentals (user_id, listing_id, start_date, end_date, days, total_amount, status, renter_address, location_of_use)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        ''', (user_id, listing_id, start_date, end_date, days, total_amount, renter_address, location_of_use))
        
        # Get rental ID for notification (lastrowid is on cursor, not connection)
        rental_id = cursor.lastrowid
        
        # Get renter name for notification
        renter = conn.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
        renter_name_text = renter['name'] if renter else 'A user'
        
        # Create notification for equipment owner
        owner_id = listing['user_id']
        conn.execute('''
            INSERT INTO notifications (user_id, type, title, message, related_id, related_type)
            VALUES (?, 'rental_request', ?, ?, ?, 'rental')
        ''', (
            owner_id,
            'New Rental Request',
            f'{renter_name_text} has requested to rent "{listing["title"]}" from {start_date} to {end_date} ({days} day{"s" if days != 1 else ""}).',
            rental_id
        ))
        
        # Commit transaction
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rental request submitted successfully! The owner will review and approve your request.',
            'rental_id': rental_id
        }), 200
    except Exception as e:
        # Rollback transaction on any error
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing rental: {str(e)}'
        }), 500
    finally:
        # Always close connection
        if conn:
            conn.close()

@app.route('/api/listings/<int:listing_id>/rental-requests')
@login_required
def get_rental_requests(listing_id):
    """Get all rental requests for a specific listing (owner only)"""
    user_id = session['user_id']
    conn = get_db()
    
    # Verify ownership
    listing = conn.execute('SELECT * FROM listings WHERE id = ? AND user_id = ?', (listing_id, user_id)).fetchone()
    
    if not listing:
        conn.close()
        return jsonify({'error': 'Listing not found or access denied'}), 404
    
    # Get all rental requests for this listing
    rentals = conn.execute('''
        SELECT r.*, u.name as renter_name, u.email as renter_email, u.phone as renter_phone
        FROM rentals r
        JOIN users u ON r.user_id = u.id
        WHERE r.listing_id = ?
        ORDER BY r.created_at DESC
    ''', (listing_id,)).fetchall()
    conn.close()
    
    rentals_data = []
    for rental in rentals:
        rentals_data.append({
            'id': rental['id'],
            'renter_name': rental['renter_name'],
            'renter_email': rental['renter_email'],
            'renter_phone': rental['renter_phone'],
            'start_date': rental['start_date'],
            'end_date': rental['end_date'],
            'days': rental['days'],
            'total_amount': rental['total_amount'],
            'status': rental['status'],
            'created_at': rental['created_at']
        })
    
    return jsonify(rentals_data)

@app.route('/api/rentals/<int:rental_id>/approve', methods=['POST'])
@login_required
def approve_rental(rental_id):
    """Approve a rental request (owner only) - with proper transaction management"""
    user_id = session['user_id']
    conn = None
    try:
        conn = get_db()
        
        # Get rental and verify ownership
        rental = conn.execute('''
            SELECT r.*, l.user_id as owner_id, l.id as listing_id
            FROM rentals r
            JOIN listings l ON r.listing_id = l.id
            WHERE r.id = ?
        ''', (rental_id,)).fetchone()
        
        if not rental:
            return jsonify({'success': False, 'message': 'Rental request not found'}), 404
        
        if rental['owner_id'] != user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if rental['status'] != 'Pending':
            return jsonify({
                'success': False,
                'message': f'Rental request is already {rental["status"]}'
            }), 400
        
        # Check for conflicts with other confirmed bookings
        conflicts = check_date_conflict(rental['listing_id'], rental['start_date'], rental['end_date'], exclude_rental_id=rental_id)
        confirmed_conflicts = [c for c in conflicts if c['status'] in ('Approved', 'Active')]
        
        if confirmed_conflicts:
            return jsonify({
                'success': False,
                'message': 'Cannot approve: dates conflict with another confirmed booking'
            }), 400
        
        # Begin transaction - all operations must succeed or all must fail
        # Update rental status to 'Approved' (confirmed/locked)
        conn.execute('''
            UPDATE rentals SET status = 'Approved' WHERE id = ?
        ''', (rental_id,))
        
        # Get renter info for notification
        renter = conn.execute('SELECT u.name, u.id FROM users u JOIN rentals r ON u.id = r.user_id WHERE r.id = ?', (rental_id,)).fetchone()
        listing_info = conn.execute('SELECT title FROM listings WHERE id = ?', (rental['listing_id'],)).fetchone()
        
        # Create notification for renter
        if renter and listing_info:
            conn.execute('''
                INSERT INTO notifications (user_id, type, title, message, related_id, related_type)
                VALUES (?, 'rental_approved', ?, ?, ?, 'rental')
            ''', (
                renter['id'],
                'Rental Request Approved',
                f'Your rental request for "{listing_info["title"]}" from {rental["start_date"]} to {rental["end_date"]} has been approved!',
                rental_id
            ))
        
        # Cancel any other pending requests that conflict with this approved rental
        cancelled_rentals = conn.execute('''
            SELECT id, user_id FROM rentals 
            WHERE listing_id = ? 
            AND status = 'Pending'
            AND id != ?
            AND (
                (start_date <= ? AND end_date >= ?) OR
                (start_date <= ? AND end_date >= ?) OR
                (start_date >= ? AND end_date <= ?)
            )
        ''', (
            rental['listing_id'],
            rental_id,
            rental['end_date'], rental['start_date'],  # Overlap check 1
            rental['start_date'], rental['end_date'],  # Overlap check 2
            rental['start_date'], rental['end_date']   # Overlap check 3
        )).fetchall()
        
        # Update cancelled rentals and notify users
        for cancelled in cancelled_rentals:
            conn.execute('UPDATE rentals SET status = "Cancelled" WHERE id = ?', (cancelled['id'],))
            
            # Notify user about cancellation
            if listing_info:
                conn.execute('''
                    INSERT INTO notifications (user_id, type, title, message, related_id, related_type)
                    VALUES (?, 'rental_cancelled', ?, ?, ?, 'rental')
                ''', (
                    cancelled['user_id'],
                    'Rental Request Cancelled',
                    f'Your rental request for "{listing_info["title"]}" was cancelled due to another approved booking.',
                    cancelled['id']
                ))
        
        # Commit transaction - all updates succeed together
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rental request approved successfully'
        })
    except Exception as e:
        # Rollback transaction on any error
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error approving rental: {str(e)}'
        }), 500
    finally:
        # Always close connection
        if conn:
            conn.close()

@app.route('/api/rentals/<int:rental_id>/reject', methods=['POST'])
@login_required
def reject_rental(rental_id):
    """Reject a rental request (owner only) - with proper transaction management"""
    user_id = session['user_id']
    conn = None
    try:
        conn = get_db()
        
        # Get rental and verify ownership
        rental = conn.execute('''
            SELECT r.*, l.user_id as owner_id
            FROM rentals r
            JOIN listings l ON r.listing_id = l.id
            WHERE r.id = ?
        ''', (rental_id,)).fetchone()
        
        if not rental:
            return jsonify({'success': False, 'message': 'Rental request not found'}), 404
        
        if rental['owner_id'] != user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        if rental['status'] != 'Pending':
            return jsonify({
                'success': False,
                'message': f'Rental request is already {rental["status"]}'
            }), 400
        
        # Update rental status to 'Cancelled'
        conn.execute('''
            UPDATE rentals SET status = 'Cancelled' WHERE id = ?
        ''', (rental_id,))
        
        # Get renter info for notification
        renter = conn.execute('SELECT u.name, u.id FROM users u JOIN rentals r ON u.id = r.user_id WHERE r.id = ?', (rental_id,)).fetchone()
        listing_info = conn.execute('SELECT title FROM listings WHERE id = ?', (rental['listing_id'],)).fetchone()
        
        # Create notification for renter
        if renter and listing_info:
            conn.execute('''
                INSERT INTO notifications (user_id, type, title, message, related_id, related_type)
                VALUES (?, 'rental_rejected', ?, ?, ?, 'rental')
            ''', (
                renter['id'],
                'Rental Request Rejected',
                f'Your rental request for "{listing_info["title"]}" from {rental["start_date"]} to {rental["end_date"]} has been rejected by the owner.',
                rental_id
            ))
        
        # Commit transaction
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rental request rejected'
        })
        
        return jsonify({
            'success': True,
            'message': 'Rental request rejected'
        })
    except Exception as e:
        # Rollback transaction on any error
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error rejecting rental: {str(e)}'
        }), 500
    finally:
        # Always close connection
        if conn:
            conn.close()

@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get all notifications for current user"""
    user_id = session['user_id']
    conn = get_db()
    
    notifications = conn.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (user_id,)).fetchall()
    conn.close()
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif['id'],
            'type': notif['type'],
            'title': notif['title'],
            'message': notif['message'],
            'related_id': notif['related_id'],
            'related_type': notif['related_type'],
            'is_read': bool(notif['is_read']),
            'created_at': notif['created_at']
        })
    
    return jsonify(notifications_data)

@app.route('/api/notifications/count')
@login_required
def get_notification_count():
    """Get count of unread notifications"""
    user_id = session['user_id']
    conn = get_db()
    
    count = conn.execute('''
        SELECT COUNT(*) as count FROM notifications 
        WHERE user_id = ? AND is_read = 0
    ''', (user_id,)).fetchone()
    conn.close()
    
    return jsonify({'count': count['count'] if count else 0})

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    user_id = session['user_id']
    conn = None
    try:
        conn = get_db()
        
        # Verify ownership
        notif = conn.execute('SELECT * FROM notifications WHERE id = ? AND user_id = ?', (notification_id, user_id)).fetchone()
        if not notif:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        # Mark as read
        conn.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    user_id = session['user_id']
    conn = None
    try:
        conn = get_db()
        conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()

def generate_rental_agreement_pdf(rental_data):
    """Generate PDF rental agreement from rental data"""
    if not REPORTLAB_AVAILABLE:
        raise Exception("ReportLab library is not installed. Please install it using: pip install reportlab")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    story = []
    
    # Title
    story.append(Paragraph("MACHINERY RENTAL AGREEMENT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Agreement Date
    agreement_date = rental_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    story.append(Paragraph(f"This Agreement is entered into on {agreement_date}.", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Parties Section
    story.append(Paragraph("PARTIES:", heading_style))
    story.append(Paragraph(f"<b>Owner/Lessor:</b>", normal_style))
    story.append(Paragraph(f"Name: {rental_data.get('owner_name', '[Owner Name]')}", normal_style))
    story.append(Paragraph(f"Address: {rental_data.get('owner_address', '[Owner Address]')}", normal_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph(f"<b>Renter/Lessee:</b>", normal_style))
    story.append(Paragraph(f"Name: {rental_data.get('renter_name', '[Renter Name]')}", normal_style))
    story.append(Paragraph(f"Address: {rental_data.get('renter_address', '[Renter Address]')}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Machinery Details
    story.append(Paragraph("MACHINERY DETAILS:", heading_style))
    story.append(Paragraph(f"Machine Name: {rental_data.get('machine_name', '[Machine Name]')}", normal_style))
    story.append(Paragraph(f"Machine Model: {rental_data.get('machine_model', '[Machine Model]')}", normal_style))
    if rental_data.get('brand'):
        story.append(Paragraph(f"Brand: {rental_data.get('brand')}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Rental Terms
    story.append(Paragraph("RENTAL TERMS:", heading_style))
    story.append(Paragraph(f"Rental Amount: ₹{rental_data.get('total_amount', '[Rent Amount]')}", normal_style))
    story.append(Paragraph(f"Rental Period: {rental_data.get('start_date', '[Start Date]')} to {rental_data.get('end_date', '[End Date]')}", normal_style))
    story.append(Paragraph(f"Number of Days: {rental_data.get('days', '[Days]')}", normal_style))
    story.append(Paragraph(f"Location of Use: {rental_data.get('location_of_use', '[Location]')}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Terms and Conditions
    story.append(Paragraph("TERMS AND CONDITIONS:", heading_style))
    
    terms = [
        ("1. PAYMENT TERMS", "The renter shall pay the rent amount as specified above. Payment is due on or before the rental start date."),
        ("2. LIABILITY AND DAMAGE", "The renter is responsible for any damage caused to the machinery during the rental period due to misuse, negligence, or improper handling. Normal wear and tear is excepted."),
        ("3. TERMS FOR DAMAGE", "In case of damage, the renter shall notify the owner within 24 hours. Repair costs shall be borne by the renter unless damage is due to manufacturing defects."),
        ("4. TERMS FOR DELAY", "If the machinery is not returned on the rental end date, a late fee of 10% of daily rent will be charged for each day of delay."),
        ("5. MISUSE CLAUSE", "The renter agrees to use the machinery only for the intended purpose and in accordance with manufacturer's guidelines. Unauthorized modifications are strictly prohibited."),
        ("6. MAINTENANCE", "The owner is responsible for basic maintenance and safe operation. The owner shall assist with major repairs at the owner's discretion."),
        ("7. RETURN CONDITIONS", "The machinery must be returned in the same condition as received. Any missing parts or accessories will be charged to the renter.")
    ]
    
    for title, content in terms:
        story.append(Paragraph(f"<b>{title}</b>", normal_style))
        story.append(Paragraph(content, normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Signatures
    story.append(Paragraph("SIGNATURES:", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    signature_data = [
        ["Owner/Lessor Signature: ____________________", "Date: ________"],
        ["", ""],
        ["Renter/Lessee Signature: ____________________", "Date: ________"],
        ["", ""],
        ["Witness Name: ____________________", "Signature: ____________________"]
    ]
    
    sig_table = Table(signature_data, colWidths=[3.5*inch, 2*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/api/rentals/<int:rental_id>/generate-contract', methods=['POST'])
@login_required
def generate_contract(rental_id):
    """Generate and download PDF contract for a rental"""
    if not REPORTLAB_AVAILABLE:
        return jsonify({'success': False, 'message': 'PDF generation library not available'}), 500
    
    user_id = session['user_id']
    conn = get_db()
    
    # Get rental details
    rental = conn.execute('''
        SELECT r.*, l.title, l.equipment_name, l.brand, l.user_id as owner_id,
               l.village_city, l.district, l.state, l.pincode,
               u1.name as renter_name, u1.email as renter_email,
               u2.name as owner_name, u2.email as owner_email
        FROM rentals r
        JOIN listings l ON r.listing_id = l.id
        JOIN users u1 ON r.user_id = u1.id
        JOIN users u2 ON l.user_id = u2.id
        WHERE r.id = ?
    ''', (rental_id,)).fetchone()
    
    if not rental:
        conn.close()
        return jsonify({'success': False, 'message': 'Rental not found'}), 404
    
    # Verify user has access (either owner or renter)
    if rental['user_id'] != user_id and rental['owner_id'] != user_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Get owner address from listing (SQLite Row objects use dictionary-style access)
    village_city = rental['village_city'] if rental['village_city'] else ''
    district = rental['district'] if rental['district'] else ''
    state = rental['state'] if rental['state'] else ''
    pincode = rental['pincode'] if rental['pincode'] else ''
    owner_address = f"{village_city}, {district}, {state}"
    if pincode:
        owner_address += f" - {pincode}"
    
    # Prepare rental data for PDF
    rental_data = {
        'owner_name': rental['owner_name'],
        'owner_address': owner_address,
        'renter_name': rental['renter_name'],
        'renter_address': rental['renter_address'] if rental['renter_address'] else 'Not provided',
        'machine_name': rental['equipment_name'],
        'machine_model': rental['brand'] if rental['brand'] else '',
        'brand': rental['brand'] if rental['brand'] else '',
        'total_amount': f"{rental['total_amount']:.2f}",
        'start_date': rental['start_date'],
        'end_date': rental['end_date'],
        'days': rental['days'],
        'location_of_use': rental['location_of_use'] if rental['location_of_use'] else 'Not specified'
    }
    
    # Generate PDF
    pdf_buffer = generate_rental_agreement_pdf(rental_data)
    
    # Save PDF to contracts directory
    contracts_dir = 'contracts'
    os.makedirs(contracts_dir, exist_ok=True)
    
    filename = f"Rental_Agreement_{rental_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    contract_path = os.path.join(contracts_dir, filename)
    
    with open(contract_path, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    # Update rental record with contract path
    conn.execute('UPDATE rentals SET contract_path = ? WHERE id = ?', (contract_path, rental_id))
    conn.commit()
    conn.close()
    
    # Return PDF for download
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Rental_Agreement_{rental_id}.pdf",
        mimetype='application/pdf'
    )

@app.route('/api/rentals/<int:rental_id>/contract-preview', methods=['GET'])
@login_required
def preview_contract_data(rental_id):
    """Get contract data for preview (before rental is created)"""
    conn = None
    try:
        user_id = session['user_id']
        conn = get_db()
        
        # Get listing details
        listing_id = request.args.get('listing_id')
        if not listing_id:
            return jsonify({'success': False, 'message': 'Listing ID required'}), 400
        
        listing = conn.execute('''
            SELECT l.*, u.name as owner_name, u.email as owner_email
            FROM listings l
            JOIN users u ON l.user_id = u.id
            WHERE l.id = ?
        ''', (listing_id,)).fetchone()
        
        if not listing:
            return jsonify({'success': False, 'message': 'Listing not found'}), 404
        
        # Get renter details
        renter = conn.execute('SELECT name, email FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not renter:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get form data
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        days = request.args.get('days')
        total_amount = request.args.get('total_amount')
        renter_address = request.args.get('renter_address', '')
        location_of_use = request.args.get('location_of_use', '')
        
        # Build owner address safely (SQLite Row objects use dictionary-style access)
        village_city = listing['village_city'] if listing['village_city'] else ''
        district = listing['district'] if listing['district'] else ''
        state = listing['state'] if listing['state'] else ''
        pincode = listing['pincode'] if listing['pincode'] else ''
        owner_address = f"{village_city}, {district}, {state}"
        if pincode:
            owner_address += f" - {pincode}"
        
        contract_data = {
            'owner_name': listing['owner_name'] if listing['owner_name'] else 'Owner',
            'owner_address': owner_address or 'Address not provided',
            'renter_name': renter['name'] if renter['name'] else 'Renter',
            'renter_address': renter_address or 'Not provided',
            'machine_name': listing['equipment_name'] if listing['equipment_name'] else 'Equipment',
            'machine_model': listing['brand'] if listing['brand'] else '',
            'brand': listing['brand'] if listing['brand'] else '',
            'total_amount': total_amount or '0.00',
            'start_date': start_date or '',
            'end_date': end_date or '',
            'days': days or '0',
            'location_of_use': location_of_use or 'Not specified'
        }
        
        return jsonify({'success': True, 'data': contract_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading preview: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/my_listings')
@login_required
def get_my_listings():
    """Get current user's listings"""
    user_id = session['user_id']
    conn = get_db()
    listings = conn.execute('''
        SELECT * FROM listings 
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    
    listings_data = []
    for listing in listings:
        listings_data.append({
            'id': listing['id'],
            'title': listing['title'],
            'category': listing['category'],
            'equipment_name': listing['equipment_name'],
            'brand': listing['brand'],
            'price': listing['price'],
            'pricing_type': listing['pricing_type'],
            'state': listing['state'],
            'district': listing['district'],
            'village_city': listing['village_city'],
            'main_image': listing['main_image'],
            'condition': listing['condition'],
            'power_spec': listing['power_spec'],
            'available_from': listing['available_from'],
            'available_till': listing['available_till'],
            'created_at': listing['created_at']
        })
    
    return jsonify(listings_data)

@app.route('/delete_listing/<int:listing_id>', methods=['DELETE', 'POST'])
@login_required
def delete_listing(listing_id):
    """Delete a listing"""
    try:
        user_id = session['user_id']
        conn = get_db()
        
        # Verify ownership
        listing = conn.execute('SELECT * FROM listings WHERE id = ? AND user_id = ?', (listing_id, user_id)).fetchone()
        
        if not listing:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Listing not found or you do not have permission to delete it'
            }), 404
        
        # Delete associated images if they exist
        if listing['main_image']:
            try:
                image_path = os.path.join('static', listing['main_image'])
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass  # Continue even if image deletion fails
        
        if listing['additional_images']:
            try:
                for img_path in listing['additional_images'].split(','):
                    image_path = os.path.join('static', img_path.strip())
                    if os.path.exists(image_path):
                        os.remove(image_path)
            except:
                pass  # Continue even if image deletion fails
        
        # Delete listing from database
        conn.execute('DELETE FROM listings WHERE id = ? AND user_id = ?', (listing_id, user_id))
        
        # Commit transaction
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Listing deleted successfully'
        }), 200
    except Exception as e:
        # Rollback transaction on any error
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting listing: {str(e)}'
        }), 500
    finally:
        # Always close connection
        if conn:
            conn.close()

@app.route('/edit_listing/<int:listing_id>')
@login_required
def edit_listing(listing_id):
    """Edit listing page - redirects to listing.html with edit mode"""
    user_id = session['user_id']
    conn = get_db()
    listing = conn.execute('SELECT * FROM listings WHERE id = ? AND user_id = ?', (listing_id, user_id)).fetchone()
    conn.close()
    
    if not listing:
        flash(translate_text('listings.edit.not_found'), 'danger')
        return redirect(url_for('listdashboard'))
    
    # Store listing data in session for pre-filling form
    session['editing_listing_id'] = listing_id
    session['editing_listing_data'] = dict(listing)
    
    return redirect(url_for('listing'))


def get_mechanic_for_user(user_id):
    """Fetch mechanic profile associated with the logged-in user"""
    conn = get_db()
    mechanic = conn.execute(
        'SELECT * FROM mechanics WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    return mechanic


@app.route('/mechanics/register', methods=['GET', 'POST'])
def mechanic_register():
    """Mechanic registration page"""
    form_data = {}
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        experience_years = request.form.get('experience_years', '').strip()
        specialization = request.form.get('specialization', '').strip()
        service_locations = request.form.get('service_locations', '').strip()
        base_charge = request.form.get('base_charge', '').strip()
        description = request.form.get('description', '').strip()
        is_available = 1 if request.form.get('is_available') == 'on' else 0
        user_id = session.get('user_id')

        form_data = {
            'full_name': full_name,
            'phone': phone,
            'email': email,
            'experience_years': experience_years,
            'specialization': specialization,
            'service_locations': service_locations,
            'base_charge': base_charge,
            'description': description,
            'is_available': 'checked' if is_available else ''
        }

        errors = []

        if not full_name:
            errors.append(translate_text('mechanic.register.errors.full_name'))
        if not phone:
            errors.append(translate_text('mechanic.register.errors.phone'))
        if specialization not in MECHANIC_SPECIALIZATIONS:
            errors.append(translate_text('mechanic.register.errors.specialization'))
        if not service_locations:
            errors.append(translate_text('mechanic.register.errors.locations'))
        if not base_charge:
            errors.append(translate_text('mechanic.register.errors.base_charge'))

        if base_charge:
            try:
                float(base_charge)
            except ValueError:
                errors.append(translate_text('mechanic.register.errors.base_charge_number'))

        if experience_years:
            try:
                int(experience_years)
            except ValueError:
                errors.append(translate_text('mechanic.register.errors.experience_number'))

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'mechanic_register.html',
                specializations=MECHANIC_SPECIALIZATIONS,
                form_data=form_data
            )

        conn = None
        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO mechanics (
                    user_id, full_name, phone, email, experience_years,
                    specialization, service_locations, base_charge, description, is_available
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                full_name,
                phone,
                email if email else None,
                int(experience_years) if experience_years else None,
                specialization,
                service_locations,
                float(base_charge),
                description if description else None,
                is_available
            ))
            conn.commit()
            conn.close()
            flash(translate_text('mechanic.register.success'), 'success')
            return redirect(url_for('mechanics_list'))
        except Exception as e:
            if conn:
                conn.close()
            flash(translate_text('mechanic.register.failure'), 'danger')

    return render_template(
        'mechanic_register.html',
        specializations=MECHANIC_SPECIALIZATIONS,
        form_data=form_data
    )


@app.route('/mechanics')
def mechanics_list():
    """Mechanics listing and filter page"""
    search = request.args.get('q', '').strip()
    specialization = request.args.get('specialization', '').strip()
    available_only = request.args.get('available_only', '').strip().lower() in ('true', '1', 'on')

    query = 'SELECT * FROM mechanics WHERE 1=1'
    params = []

    if search:
        query += ' AND (LOWER(service_locations) LIKE ? OR LOWER(full_name) LIKE ?)'
        like_term = f'%{search.lower()}%'
        params.extend([like_term, like_term])

    if specialization and specialization in MECHANIC_SPECIALIZATIONS:
        query += ' AND specialization = ?'
        params.append(specialization)

    if available_only:
        query += ' AND is_available = 1'

    query += ' ORDER BY created_at DESC'

    conn = get_db()
    mechanics = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        'mechanics_list.html',
        mechanics=mechanics,
        filters={
            'search': search,
            'specialization': specialization,
            'available_only': available_only
        },
        specializations=MECHANIC_SPECIALIZATIONS
    )


@app.route('/mechanics/<int:mechanic_id>/request', methods=['POST'])
def mechanic_service_request(mechanic_id):
    """Create a new service request for a mechanic"""
    farmer_name = request.form.get('farmer_name', '').strip()
    phone = request.form.get('phone', '').strip()
    location = request.form.get('location', '').strip()
    issue_description = request.form.get('issue_description', '').strip()

    if not farmer_name or not phone or not location or not issue_description:
        return jsonify({'success': False, 'message': translate_text('mechanic.requests.missing_fields')}), 400

    conn = get_db()
    try:
        mechanic = conn.execute('SELECT id FROM mechanics WHERE id = ?', (mechanic_id,)).fetchone()

        if not mechanic:
            return jsonify({'success': False, 'message': translate_text('mechanic.requests.not_found')}), 404

        conn.execute('''
            INSERT INTO mechanic_requests (mechanic_id, farmer_name, phone, location, issue_description)
            VALUES (?, ?, ?, ?, ?)
        ''', (mechanic_id, farmer_name, phone, location, issue_description))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': translate_text('mechanic.requests.created')}), 200


@app.route('/mechanic/dashboard')
@login_required
def mechanic_dashboard():
    """Dashboard for mechanics to view and manage requests"""
    user_id = session['user_id']
    conn = get_db()
    mechanic = conn.execute(
        'SELECT * FROM mechanics WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()

    requests_data = []
    if mechanic:
        requests_data = conn.execute('''
            SELECT * FROM mechanic_requests
            WHERE mechanic_id = ?
            ORDER BY created_at DESC
        ''', (mechanic['id'],)).fetchall()

    conn.close()

    return render_template(
        'mechanic_dashboard.html',
        mechanic=mechanic,
        service_requests=requests_data,
        request_statuses=MECHANIC_REQUEST_STATUSES
    )


@app.route('/api/mechanic/availability', methods=['POST'])
@login_required
def update_mechanic_availability():
    """Toggle mechanic availability status"""
    user_id = session['user_id']
    payload = request.get_json(silent=True) or {}
    form_value = request.form.get('is_available')
    raw_value = payload.get('is_available') if payload else form_value

    is_available = 1 if str(raw_value).lower() in ('true', '1', 'on') else 0

    conn = get_db()
    mechanic = conn.execute(
        'SELECT id FROM mechanics WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()

    if not mechanic:
        conn.close()
        return jsonify({'success': False, 'message': 'Mechanic profile not found.'}), 404

    conn.execute('''
        UPDATE mechanics
        SET is_available = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (is_available, mechanic['id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'is_available': bool(is_available)})


@app.route('/api/mechanic/requests/<int:request_id>/status', methods=['POST'])
@login_required
def update_mechanic_request_status(request_id):
    """Update the status of a mechanic service request"""
    payload = request.get_json(silent=True) or {}
    new_status = payload.get('status') or request.form.get('status')

    if new_status not in MECHANIC_REQUEST_STATUSES:
        return jsonify({'success': False, 'message': 'Invalid status selected.'}), 400

    user_id = session['user_id']
    conn = get_db()
    mechanic = conn.execute(
        'SELECT id FROM mechanics WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()

    if not mechanic:
        conn.close()
        return jsonify({'success': False, 'message': 'Mechanic profile not found.'}), 404

    request_row = conn.execute(
        'SELECT id FROM mechanic_requests WHERE id = ? AND mechanic_id = ?',
        (request_id, mechanic['id'])
    ).fetchone()

    if not request_row:
        conn.close()
        return jsonify({'success': False, 'message': 'Request not found.'}), 404

    conn.execute('''
        UPDATE mechanic_requests
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_status, request_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'status': new_status})


@app.route('/heatmap')
def heatmap():
    """Heatmap visualization page"""
    return render_template('heatmap.html')


@app.route('/api/heatmap_locations')
def get_heatmap_locations():
    """Get aggregated location data for heatmap"""
    conn = get_db()
    # Group by location fields to get density. 
    # Using village_city, district, state to form a unique address.
    locations = conn.execute('''
        SELECT village_city, district, state, COUNT(*) as count
        FROM listings
        GROUP BY village_city, district, state
    ''').fetchall()
    conn.close()

    result = []
    for loc in locations:
        # Construct a clean address string parts
        result.append({
            'address': f"{loc['village_city']}, {loc['district']}, {loc['state']}, India",
            'weight': loc['count']
        })
    
    return jsonify(result)


# ============================================
# CONFIGURATION: Set your Gemini API key here
# ============================================
# Check for API key in environment variable
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Set the API key in environment (for compatibility)
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

# Initialize the Gemini client with API key
client = genai.Client(api_key=GEMINI_API_KEY)

# System prompt for AgroRent chatbot
PLATFORM_DATA = """
AgroRent Platform Information:

About AgroRent:
AgroRent is a comprehensive agricultural equipment rental platform connecting farmers with equipment owners. We make farming more affordable and accessible by enabling equipment sharing.

Services Offered:
1. Equipment Rental - Tractors, harvesters, plows, seeders, sprayers
2. Booking System - Easy online booking with calendar availability
3. Delivery Service - Equipment delivered to your farm
4. Maintenance Support - All equipment is well-maintained and insured
5. Flexible Pricing - Hourly, daily, and weekly rental options

How to Book:
1. Browse available equipment
2. Check availability calendar
3. Select rental duration
4. Complete payment
5. Equipment delivered to your location

Websites links for traversal:
Renting: https://agrorent-r3i4.onrender.com/renting
About: https://agrorent-r3i4.onrender.com/about
Market overview: https://agrorent-r3i4.onrender.com/market
Listings: https://agrorent-r3i4.onrender.com/listing
Heatmap: https://agrorent-r3i4.onrender.com/heatmap
Mechanics: https://agrorent-r3i4.onrender.com/mechanics

Contact Information:
- Phone: +91 9930235462
- Email: parthmahadik752@gmail.com
- Hours: 24/7 customer support

Coverage Area:
We serve rural and agricultural areas across multiple states. Check availability in your region.

Benefits:
- Save money on expensive equipment purchases
- Access latest farming technology
- No maintenance hassles
- Flexible rental periods
- Trained operators available on request
"""

AGRORENT_SYSTEM_PROMPT = f"""You are a helpful assistant for AgroRent, an agricultural equipment rental platform.

{PLATFORM_DATA}

Instructions:
- Be friendly, helpful, and concise
- Answer questions about equipment, pricing, booking, and services
- Any farming related questions, answer them with the most relevant information from your intelligence example:" have x acres of land what equipemnt should i rent".
- If asked about something not in the data, politely say you'll connect them with support
- Keep responses brief (2-3 sentences) unless detailed information is requested
- Use a warm, professional tone suitable for farmers
- If someone wants to book, guide them through the process
- If someone wants to rent equipment, guide them through the process and provide links from platform data
- IMPORTANT: When providing links, include the full URL (e.g., https://agrorent-r3i4.onrender.com/renting) so they become clickable. You can use markdown format [link text](url) or just include the URL directly."""

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Combine system prompt with user message
        full_prompt = f"{AGRORENT_SYSTEM_PROMPT}\n\nUser: {user_message}\nAssistant:"
        
        # Generate response using Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        
        # Extract the response text
        bot_response = response.text if hasattr(response, 'text') else str(response)
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}',
            'status': 'error'
        }), 500


# Machine Condition Analysis
ANALYSIS_PROMPT = """You are an AI machinery condition inspector. Analyze the machine shown in the image.

Tasks:
1. Identify all visible issues such as rust, dents, scratches, broken parts, worn tires, paint fade, leaks, or structural damage.
2. Based on your analysis, generate a "Condition Score" from 0 to 10:
   - 9–10: Excellent condition, almost no damage
   - 7–8: Good condition, minor cosmetic issues
   - 5–6: Moderate condition, noticeable wear or rust
   - 3–4: Poor condition, obvious damage, maintenance needed
   - 0–2: Very bad condition, unsafe or unusable
3. Provide a detailed explanation of why you gave that score.
4. Keep output in structured JSON format:

{
  "condition_score": <number>,
  "issues_found": [list of problems - keep each very short, max 5 items],
  "summary": "Short explanation of condition (one sentence)",
  "recommendation": "What the renter should know (one sentence)"
}

Analyze only what is visible in the image. Keep issues_found list items very brief (3-5 words each)."""

@app.route('/api/analyze-condition/<int:listing_id>', methods=['POST'])
@login_required
def analyze_machine_condition(listing_id):
    """Analyze machine condition from listing image"""
    try:
        conn = get_db()
        listing = conn.execute('SELECT * FROM listings WHERE id = ?', (listing_id,)).fetchone()
        conn.close()
        
        if not listing:
            return jsonify({'error': 'Listing not found'}), 404
        
        if not listing['main_image']:
            return jsonify({'error': 'No image available for analysis'}), 400
        
        # Read image from file system
        image_path = os.path.join('static', listing['main_image'])
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Determine MIME type from file extension
        file_ext = os.path.splitext(image_path)[1].lower()
        mime_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_type_map.get(file_ext, 'image/jpeg')
        
        # Create image part for Gemini
        image = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type
        )
        
        # Generate content with Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[ANALYSIS_PROMPT, image],
        )
        
        # Parse the response
        response_text = response.text
        
        # Try to extract JSON from the response
        # Gemini might wrap JSON in markdown code blocks
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group(0)
            try:
                result = json.loads(json_str)
                # Ensure all required fields exist
                if 'condition_score' not in result:
                    result['condition_score'] = None
                if 'issues_found' not in result:
                    result['issues_found'] = []
                if 'summary' not in result:
                    result['summary'] = response_text[:100] if response_text else 'Analysis completed'
                if 'recommendation' not in result:
                    result['recommendation'] = 'Review the equipment before renting'
                
                return jsonify(result)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured response with raw text
                return jsonify({
                    'condition_score': None,
                    'issues_found': [],
                    'summary': response_text[:150] if len(response_text) > 150 else response_text,
                    'recommendation': 'Could not parse structured response. Please review the equipment manually.',
                    'raw_response': response_text
                })
        else:
            # If no JSON found, return structured response
            return jsonify({
                'condition_score': None,
                'issues_found': [],
                'summary': response_text[:150] if len(response_text) > 150 else response_text,
                'recommendation': 'Could not parse structured response. Please review the equipment manually.',
                'raw_response': response_text
            })
            
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


if __name__ == '__main__':
    # Check if API key is set
    if GEMINI_API_KEY == "your-api-key-here" or not GEMINI_API_KEY:
        print("Warning: Please set your GEMINI_API_KEY in the code!")
        print("Edit app.py and replace 'your-api-key-here' with your actual API key.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)


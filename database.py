import sqlite3
from config import DATABASE_PATH

DATABASE = DATABASE_PATH

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
            payment_id TEXT,
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
        if 'payment_id' not in columns:
            conn.execute('ALTER TABLE rentals ADD COLUMN payment_id TEXT')
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

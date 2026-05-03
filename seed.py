import sys

from database import get_db, init_db

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def seed_demo_data():
    """Seed database with demo listings if empty"""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    conn = get_db()

    # Check if data already exists
    count = conn.execute('SELECT COUNT(*) FROM listings').fetchone()[0]
    if count > 0:
        print(f"✅ Database already has {count} listings, skipping seed")
        conn.close()
        return

    print("🌱 Seeding demo data...")

    # Create demo owner user
    conn.execute('''
        INSERT OR IGNORE INTO users
        (id, name, email, phone, password)
        VALUES
        (1, 'Parth Mahadik', 'parth@agrorent.com', '9930235462', 'demo123'),
        (2, 'Arnav Shelke', 'arnav@agrorent.com', '9876543210', 'demo123'),
        (3, 'Ghanshyam Das', 'ghanshyam@agrorent.com', '9823456789', 'demo123')
    ''')

    # Create demo listings
    conn.execute('''
        INSERT OR IGNORE INTO listings
        (id, user_id, owner_name, phone, email, contact_method, category,
         equipment_name, brand, year, condition, power_spec, state, district,
         village_city, pincode, service_radius, pricing_type, price,
         min_duration, available_from, transport_included, title, description,
         status)
        VALUES
        (1, 1, 'Parth Mahadik', '9930235462', 'parth@agrorent.com', 'both',
         'tractor', 'Tractor', 'Mahindra', 2020, 'Good', '45 HP',
         'Maharashtra', 'Pune', 'Mulshi', '412108', '20 km',
         'per day', 900.0, '1 day', '2026-01-01', 'Yes',
         'Mahindra Tractor 575', 'Well maintained Mahindra 575 tractor available for rent',
         'available'),

        (2, 2, 'Arnav Shelke', '9876543210', 'arnav@agrorent.com', 'both',
         'tractor', 'Tractor', 'Swaraj', 2019, 'Good', '50 HP',
         'Maharashtra', 'Nashik', 'Nashik', '422001', '25 km',
         'per day', 1000.0, '1 day', '2026-01-01', 'No',
         'Swaraj 744E Tractor', 'Swaraj 744E tractor in excellent condition',
         'available'),

        (3, 3, 'Ghanshyam Das', '9823456789', 'ghanshyam@agrorent.com', 'both',
         'tractor', 'Tractor', 'John Deere', 2021, 'Excellent', '55 HP',
         'Maharashtra', 'Pune', 'Mulshi', '412108', '15 km',
         'per day', 1200.0, '1 day', '2026-01-01', 'Yes',
         'John Deere 5050D Tractor', 'Premium John Deere tractor for heavy duty work',
         'available'),

        (4, 1, 'Parth Mahadik', '9930235462', 'parth@agrorent.com', 'both',
         'harvester', 'Harvester', 'New Holland', 2021, 'Excellent', '100 HP',
         'Maharashtra', 'Pune', 'Mulshi', '412108', '30 km',
         'per day', 2500.0, '1 day', '2026-01-01', 'Yes',
         'New Holland TC5.30 Harvester', 'High capacity combine harvester for wheat and rice',
         'available'),

        (5, 2, 'Arnav Shelke', '9876543210', 'arnav@agrorent.com', 'both',
         'harvester', 'Harvester', 'John Deere', 2020, 'Good', '90 HP',
         'Maharashtra', 'Nashik', 'Nashik', '422001', '20 km',
         'per day', 2200.0, '1 day', '2026-01-01', 'No',
         'John Deere W70 Harvester', 'Reliable combine harvester available for seasonal work',
         'available'),

        (6, 3, 'Ghanshyam Das', '9823456789', 'ghanshyam@agrorent.com', 'both',
         'pump', 'Water Pump', 'Kirloskar', 2022, 'Excellent', '5 HP',
         'Maharashtra', 'Pune', 'Mulshi', '412108', '10 km',
         'per day', 300.0, '1 day', '2026-01-01', 'Yes',
         'Kirloskar 5HP Water Pump', 'High efficiency water pump for irrigation',
         'available'),

        (7, 1, 'Parth Mahadik', '9930235462', 'parth@agrorent.com', 'both',
         'sprayer', 'Sprayer', 'Aspee', 2021, 'Good', '16L Tank',
         'Maharashtra', 'Pune', 'Mulshi', '412108', '15 km',
         'per day', 200.0, '1 day', '2026-01-01', 'No',
         'Aspee Power Sprayer', 'Motorized power sprayer for pesticide application',
         'available')
    ''')

    conn.commit()
    conn.close()
    print("✅ Demo data seeded successfully!")


if __name__ == '__main__':
    init_db()
    seed_demo_data()

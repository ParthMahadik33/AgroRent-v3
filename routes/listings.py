import os
from datetime import datetime, timedelta
from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from database import get_db
from utils.auth import login_required
from utils.translations import translate_text

bp = Blueprint('listings', __name__)

@bp.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

@bp.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)

@bp.route('/listing')
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

@bp.route('/create_listing', methods=['POST'])
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

@bp.route('/api/listings')
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

@bp.route('/api/listing/<int:listing_id>')
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

@bp.route('/api/listing/<int:listing_id>/availability')
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

@bp.route('/api/my_listings')
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

@bp.route('/delete_listing/<int:listing_id>', methods=['DELETE', 'POST'])
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

@bp.route('/edit_listing/<int:listing_id>')
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

@bp.route('/api/heatmap_locations')
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

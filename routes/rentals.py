import io
import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, send_file, session
from database import get_db
from utils.auth import login_required
from routes.listings import check_date_conflict
from ai.chatbot import chat
from ai.condition_check import analyze_machine_condition

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

bp = Blueprint('rentals', __name__)

@bp.route('/api/my_rentals')
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

@bp.route('/rent_equipment', methods=['POST'])
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
            'rental_id': rental_id,
            'total_amount': total_amount,
            'message': 'Booking created, proceed to payment',
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

@bp.route('/api/listings/<int:listing_id>/rental-requests')
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

@bp.route('/api/rentals/<int:rental_id>/approve', methods=['POST'])
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

@bp.route('/api/rentals/<int:rental_id>/reject', methods=['POST'])
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

@bp.route('/api/rentals/<int:rental_id>/generate-contract', methods=['POST'])
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

@bp.route('/api/rentals/<int:rental_id>/contract-preview', methods=['GET'])
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

@bp.route('/chat', methods=['POST'])
def chat_route():
    return chat()

@bp.route('/api/analyze-condition/<int:listing_id>', methods=['POST'])
@login_required
def analyze_machine_condition_route(listing_id):
    return analyze_machine_condition(listing_id)

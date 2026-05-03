from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from config import MECHANIC_REQUEST_STATUSES, MECHANIC_SPECIALIZATIONS
from database import get_db
from utils.auth import login_required
from utils.translations import translate_text

bp = Blueprint('mechanics', __name__)

def get_mechanic_for_user(user_id):
    """Fetch mechanic profile associated with the logged-in user"""
    conn = get_db()
    mechanic = conn.execute(
        'SELECT * FROM mechanics WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    return mechanic

@bp.route('/mechanics/register', methods=['GET', 'POST'])
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

@bp.route('/mechanics')
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

@bp.route('/mechanics/<int:mechanic_id>/request', methods=['POST'])
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

@bp.route('/mechanic/dashboard')
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

@bp.route('/api/mechanic/availability', methods=['POST'])
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

@bp.route('/api/mechanic/requests/<int:request_id>/status', methods=['POST'])
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

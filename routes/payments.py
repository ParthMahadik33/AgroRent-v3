import hmac
import hashlib
from datetime import datetime, timedelta

import razorpay
from flask import Blueprint, jsonify, request, session

from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from database import get_db
from utils.auth import login_required

payments_bp = Blueprint('payments', __name__)

_client = None


def _get_razorpay_client():
    global _client
    if _client is None:
        if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
            raise RuntimeError('RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not configured')
        _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    return _client


def _parse_sqlite_datetime(val):
    s = str(val)
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f'Unparseable datetime: {val!r}')


def initiate_refund_for_rental(rental_row):
    """Issue Razorpay refund for a paid rental. rental_row must support dict-like access."""
    row = dict(rental_row)
    pid = row.get('payment_id')
    if not pid:
        return None
    client = _get_razorpay_client()
    rid = row['id']
    amt = row['total_amount']
    paise = int(round(float(amt) * 100))
    return client.payment.refund(
        pid,
        {
            'amount': paise,
            'notes': {
                'reason': 'Owner cancelled booking',
                'rental_id': str(rid),
            },
        },
    )


@payments_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    """Create Razorpay order after booking is created"""
    try:
        data = request.get_json(silent=True) or {}
        rental_id = data.get('rental_id')
        amount = data.get('amount')

        if rental_id is None or amount is None:
            return jsonify({'success': False, 'error': 'Missing rental_id or amount'}), 400

        user_id = session['user_id']
        conn = get_db()
        rental = conn.execute(
            'SELECT id, user_id, total_amount, status FROM rentals WHERE id = ?',
            (int(rental_id),),
        ).fetchone()
        conn.close()

        if not rental or rental['user_id'] != user_id:
            return jsonify({'success': False, 'error': 'Rental not found'}), 404

        expected = float(rental['total_amount'])
        received = float(amount)
        if abs(expected - received) > 0.01:
            return jsonify({'success': False, 'error': 'Amount mismatch'}), 400

        client = _get_razorpay_client()
        order = client.order.create({
            'amount': int(round(float(amount) * 100)),
            'currency': 'INR',
            'receipt': f'rental_{rental_id}',
            'notes': {'rental_id': str(rental_id)},
        })

        return jsonify({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key': RAZORPAY_KEY_ID,
        })
    except RuntimeError as e:
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        print(f'Order creation error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@payments_bp.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    """Verify payment and activate rental"""
    conn = None
    try:
        data = request.get_json(silent=True) or {}

        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        rental_id = data.get('rental_id')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, rental_id]):
            return jsonify({'success': False, 'error': 'Missing payment fields'}), 400

        if not RAZORPAY_KEY_SECRET:
            return jsonify({'success': False, 'error': 'Payment not configured'}), 503

        msg = f'{razorpay_order_id}|{razorpay_payment_id}'
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, str(razorpay_signature)):
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400

        user_id = session['user_id']
        conn = get_db()
        rental = conn.execute(
            'SELECT id, user_id FROM rentals WHERE id = ?',
            (int(rental_id),),
        ).fetchone()

        if not rental or rental['user_id'] != user_id:
            conn.close()
            return jsonify({'success': False, 'error': 'Rental not found'}), 404

        rid = int(rental_id)
        conn.execute(
            '''
            UPDATE rentals
            SET status = 'Active', payment_id = ?
            WHERE id = ?
            ''',
            (razorpay_payment_id, rid),
        )
        conn.commit()

        full = conn.execute(
            '''
            SELECT r.*, l.title, l.phone AS owner_phone,
                   l.owner_name, u.name AS farmer_name, u.phone AS farmer_phone
            FROM rentals r
            JOIN listings l ON r.listing_id = l.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
            ''',
            (rid,),
        ).fetchone()
        conn.close()
        conn = None

        if full:
            from bot.notifications import notify_owner_new_booking

            try:
                notify_owner_new_booking(dict(full))
            except Exception as notify_err:
                print(f'Owner WhatsApp notify error: {notify_err}')

        return jsonify({'success': True})

    except Exception as e:
        print(f'Payment verification error: {e}')
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


@payments_bp.route('/cancel_booking/<int:rental_id>', methods=['POST'])
@login_required
def cancel_booking(rental_id):
    """Owner cancels booking — initiates refund within 2 hours of payment."""
    conn = None
    try:
        conn = get_db()
        rental = conn.execute(
            '''
            SELECT r.*, l.user_id AS owner_id, l.title,
                   l.owner_name, u.name AS farmer_name, u.phone AS farmer_phone
            FROM rentals r
            JOIN listings l ON r.listing_id = l.id
            JOIN users u ON r.user_id = u.id
            WHERE r.id = ?
            ''',
            (rental_id,),
        ).fetchone()

        if not rental:
            conn.close()
            return jsonify({'success': False, 'error': 'Rental not found'}), 404

        if session.get('user_id') != rental['owner_id']:
            conn.close()
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        created_at = _parse_sqlite_datetime(rental['created_at'])
        if datetime.now() - created_at > timedelta(hours=2):
            conn.close()
            return jsonify({'success': False, 'error': 'Cancellation window expired (2 hours)'}), 400

        if rental['payment_id']:
            try:
                initiate_refund_for_rental(rental)
            except Exception as refund_err:
                conn.close()
                print(f'Refund error: {refund_err}')
                return jsonify({'success': False, 'error': f'Refund failed: {refund_err}'}), 502

        conn.execute(
            'UPDATE rentals SET status = ? WHERE id = ?',
            ('Cancelled', rental_id),
        )
        conn.commit()
        conn.close()
        conn = None

        from bot.notifications import notify_farmer_cancelled

        try:
            notify_farmer_cancelled(dict(rental))
        except Exception as notify_err:
            print(f'Farmer WhatsApp notify error: {notify_err}')

        return jsonify({'success': True, 'message': 'Booking cancelled and refund initiated'})

    except ValueError as ve:
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        print(f'Cancellation error: {e}')
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import Blueprint, jsonify, session
from database import get_db
from utils.auth import login_required

bp = Blueprint('notifications', __name__)

@bp.route('/api/notifications')
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

@bp.route('/api/notifications/count')
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

@bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
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

@bp.route('/api/notifications/read-all', methods=['POST'])
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

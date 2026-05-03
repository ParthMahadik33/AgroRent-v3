// Notification System

let notificationInterval = null;

// Load notification count on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('notification-btn')) {
        loadNotificationCount();
        // Auto-refresh notifications every 30 seconds
        notificationInterval = setInterval(loadNotificationCount, 30000);
    }
});

// Load notification count
async function loadNotificationCount() {
    try {
        const response = await fetch('/api/notifications/count');
        const data = await response.json();
        const badge = document.getElementById('notification-badge');
        
        if (data.count > 0) {
            badge.textContent = data.count > 99 ? '99+' : data.count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading notification count:', error);
    }
}

// Toggle notifications dropdown
window.toggleNotifications = function() {
    const menu = document.getElementById('notification-menu');
    const isActive = menu.classList.contains('active');
    
    // Close other dropdowns
    const profileMenu = document.getElementById('dropdown-menu');
    if (profileMenu) {
        profileMenu.classList.remove('active');
    }
    
    if (isActive) {
        menu.classList.remove('active');
    } else {
        menu.classList.add('active');
        loadNotifications();
    }
}

// Load notifications
async function loadNotifications() {
    const list = document.getElementById('notification-list');
    const empty = document.getElementById('notification-empty');
    const markAllBtn = document.getElementById('mark-all-read-btn');
    
    list.innerHTML = '<div class="notification-loading">Loading notifications...</div>';
    empty.style.display = 'none';
    
    try {
        const response = await fetch('/api/notifications');
        const notifications = await response.json();
        
        if (notifications.length === 0) {
            list.innerHTML = '';
            empty.style.display = 'block';
            markAllBtn.style.display = 'none';
        } else {
            list.innerHTML = '';
            const hasUnread = notifications.some(n => !n.is_read);
            markAllBtn.style.display = hasUnread ? 'block' : 'none';
            
            notifications.forEach(notif => {
                const item = createNotificationItem(notif);
                list.appendChild(item);
            });
        }
        
        // Update count after loading
        loadNotificationCount();
    } catch (error) {
        console.error('Error loading notifications:', error);
        list.innerHTML = '<div class="notification-loading" style="color: #dc3545;">Error loading notifications</div>';
    }
}

// Create notification item element
function createNotificationItem(notif) {
    const item = document.createElement('div');
    item.className = `notification-item ${notif.is_read ? '' : 'unread'}`;
    item.onclick = () => markNotificationRead(notif.id, notif);
    
    // Get icon based on type
    let icon = 'fa-bell';
    if (notif.type === 'rental_request') {
        icon = 'fa-calendar-plus';
    } else if (notif.type === 'rental_approved') {
        icon = 'fa-check-circle';
    } else if (notif.type === 'rental_rejected') {
        icon = 'fa-times-circle';
    } else if (notif.type === 'rental_cancelled') {
        icon = 'fa-ban';
    }
    
    // Format time
    const time = formatNotificationTime(notif.created_at);
    
    item.innerHTML = `
        <i class="fas ${icon} notification-icon"></i>
        <div class="notification-content">
            <div class="notification-title">${escapeHtml(notif.title)}</div>
            <div class="notification-message">${escapeHtml(notif.message)}</div>
            <div class="notification-time">${time}</div>
        </div>
    `;
    
    return item;
}

// Mark notification as read
async function markNotificationRead(notificationId, notif) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Update UI
            const item = event.target.closest('.notification-item');
            if (item) {
                item.classList.remove('unread');
            }
            
            // If it's a rental notification, navigate to appropriate page
            if (notif.related_type === 'rental') {
                if (notif.type === 'rental_request') {
                    // Navigate to listing dashboard
                    window.location.href = '/listdashboard';
                } else {
                    // Navigate to rent dashboard
                    window.location.href = '/rentdashboard';
                }
            }
            
            // Update count
            loadNotificationCount();
        }
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Mark all notifications as read
window.markAllNotificationsRead = async function() {
    try {
        const response = await fetch('/api/notifications/read-all', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Update UI
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            
            document.getElementById('mark-all-read-btn').style.display = 'none';
            loadNotificationCount();
        }
    } catch (error) {
        console.error('Error marking all notifications as read:', error);
    }
}

// Format notification time
function formatNotificationTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) {
        return 'Just now';
    } else if (minutes < 60) {
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    } else if (hours < 24) {
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    } else if (days < 7) {
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString();
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close notifications when clicking outside
document.addEventListener('click', function(event) {
    const notificationDropdown = document.querySelector('.notification-dropdown');
    const notificationMenu = document.getElementById('notification-menu');
    
    if (notificationDropdown && notificationMenu && 
        !notificationDropdown.contains(event.target) && 
        notificationMenu.classList.contains('active')) {
        notificationMenu.classList.remove('active');
    }
});


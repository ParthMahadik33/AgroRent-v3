// Listing Dashboard Functionality

document.addEventListener('DOMContentLoaded', function() {
    let listings = [];
    let listingToDelete = null;

    // Load user's listings
    loadMyListings();
    initEventListeners();

    // Load listings from API
    async function loadMyListings() {
        const loadingState = document.getElementById('loading-state');
        const emptyState = document.getElementById('empty-state');
        const listingsGrid = document.getElementById('listings-grid');

        try {
            loadingState.style.display = 'block';
            listingsGrid.innerHTML = '';
            emptyState.style.display = 'none';

            const response = await fetch('/api/my_listings');
            const data = await response.json();

            listings = data;

            if (listings.length === 0) {
                emptyState.style.display = 'block';
                listingsGrid.innerHTML = '';
            } else {
                displayListings(listings);
            }
        } catch (error) {
            console.error('Error loading listings:', error);
            listingsGrid.innerHTML = '<p style="text-align: center; color: #c94843; padding: 2rem;">Error loading listings. Please try again.</p>';
        } finally {
            loadingState.style.display = 'none';
        }
    }

    // Display listings as cards
    function displayListings(listings) {
        const listingsGrid = document.getElementById('listings-grid');
        listingsGrid.innerHTML = '';

        listings.forEach(listing => {
            const card = createListingCard(listing);
            listingsGrid.appendChild(card);
        });
    }

    // Create listing card
    function createListingCard(listing) {
        const card = document.createElement('div');
        card.className = 'listing-card';
        
        const imageUrl = listing.main_image ? `/static/${listing.main_image}` : '/assets/carousel1.jpg';
        const priceDisplay = `₹${listing.price.toLocaleString()}`;
        
        // Determine status
        const today = new Date();
        const availableFrom = new Date(listing.available_from);
        const availableTill = listing.available_till ? new Date(listing.available_till) : null;
        
        let status = 'Active';
        let statusClass = '';
        if (availableFrom > today) {
            status = 'Upcoming';
        } else if (availableTill && availableTill < today) {
            status = 'Expired';
            statusClass = 'inactive';
        }

        // Format date
        const createdDate = new Date(listing.created_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        card.innerHTML = `
            <div class="card-image-wrapper">
                <img src="${imageUrl}" alt="${listing.title}" class="card-image" onerror="this.src='/assets/carousel1.jpg'">
                <div class="card-status ${statusClass}">${status}</div>
            </div>
            <div class="card-body">
                <div class="card-category">${listing.category}</div>
                <h3 class="card-title">${listing.title}</h3>
                <div class="card-details">
                    <div class="card-detail">
                        <i class="fas fa-tag"></i>
                        <span>${listing.equipment_name}</span>
                    </div>
                    <div class="card-detail">
                        <i class="fas fa-industry"></i>
                        <span>${listing.brand}</span>
                    </div>
                    ${listing.power_spec ? `
                    <div class="card-detail">
                        <i class="fas fa-bolt"></i>
                        <span>${listing.power_spec}</span>
                    </div>
                    ` : ''}
                    <div class="card-detail">
                        <i class="fas fa-check-circle"></i>
                        <span>${listing.condition}</span>
                    </div>
                </div>
                <div class="card-price">
                    ${priceDisplay}
                    <span class="card-price-type">/${listing.pricing_type}</span>
                </div>
                <div class="card-location">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${listing.village_city}, ${listing.district}, ${listing.state}</span>
                </div>
                <div class="card-date">
                    <i class="fas fa-calendar"></i> Listed on ${createdDate}
                </div>
            </div>
            <div class="card-footer">
                <button class="btn-view-requests" onclick="viewRentalRequests(${listing.id})">
                    <i class="fas fa-calendar-check"></i> View Requests
                </button>
                <button class="btn-edit" onclick="editListing(${listing.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-delete" onclick="confirmDelete(${listing.id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        `;

        return card;
    }

    // Edit listing
    window.editListing = function(listingId) {
        window.location.href = `/edit_listing/${listingId}`;
    };

    // Confirm delete
    window.confirmDelete = function(listingId) {
        listingToDelete = listingId;
        const modal = document.getElementById('delete-modal');
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    };

    // Initialize event listeners
    function initEventListeners() {
        // Cancel delete
        document.getElementById('cancel-delete').addEventListener('click', function() {
            document.getElementById('delete-modal').classList.remove('show');
            document.body.style.overflow = 'visible';
            listingToDelete = null;
        });

        // Confirm delete
        document.getElementById('confirm-delete').addEventListener('click', async function() {
            if (!listingToDelete) return;

            const btn = this;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

            try {
                const response = await fetch(`/delete_listing/${listingToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    // Close modal
                    document.getElementById('delete-modal').classList.remove('show');
                    document.body.style.overflow = 'visible';
                    
                    // Reload listings
                    await loadMyListings();
                    
                    // Show success message
                    showNotification('Listing deleted successfully', 'success');
                } else {
                    alert('Error: ' + (data.message || 'Failed to delete listing'));
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            } catch (error) {
                console.error('Error deleting listing:', error);
                alert('An error occurred. Please try again.');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }

            listingToDelete = null;
        });

        // Close modal on overlay click
        document.querySelector('.delete-modal .modal-overlay').addEventListener('click', function(e) {
            if (e.target === this) {
                document.getElementById('delete-modal').classList.remove('show');
                document.body.style.overflow = 'visible';
                listingToDelete = null;
            }
        });
    }

    // View rental requests
    window.viewRentalRequests = async function(listingId) {
        try {
            const response = await fetch(`/api/listings/${listingId}/rental-requests`);
            const requests = await response.json();
            
            showRentalRequestsModal(listingId, requests);
        } catch (error) {
            console.error('Error loading rental requests:', error);
            alert('Error loading rental requests. Please try again.');
        }
    };

    // Show rental requests modal
    function showRentalRequestsModal(listingId, requests) {
        const modal = document.createElement('div');
        modal.className = 'rental-requests-modal show';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <button class="modal-close" onclick="this.closest('.rental-requests-modal').remove(); document.body.style.overflow = 'visible';">
                    <i class="fas fa-times"></i>
                </button>
                <h2><i class="fas fa-calendar-check"></i> Rental Requests</h2>
                <div class="rental-requests-list" id="rental-requests-list-${listingId}">
                    ${requests.length === 0 ? '<p style="text-align: center; padding: 2rem; color: #7a8c6a;">No rental requests yet.</p>' : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        
        // Render requests
        const requestsList = document.getElementById(`rental-requests-list-${listingId}`);
        if (requestsList && requests.length > 0) {
            requests.forEach(request => {
                const requestCard = createRequestCard(listingId, request);
                requestsList.appendChild(requestCard);
            });
        }
        
        // Close on overlay click
        modal.querySelector('.modal-overlay').addEventListener('click', function() {
            modal.remove();
            document.body.style.overflow = 'visible';
        });
    };

    // Create request card
    function createRequestCard(listingId, request) {
        const card = document.createElement('div');
        card.className = 'rental-request-card';
        
        const statusClass = request.status.toLowerCase();
        
        // Parse dates without timezone conversion to avoid day shift
        const parseDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };
        
        const startDate = parseDate(request.start_date).toLocaleDateString();
        const endDate = parseDate(request.end_date).toLocaleDateString();
        const createdDate = new Date(request.created_at).toLocaleDateString();
        
        let actionButtons = '';
        if (request.status === 'Pending') {
            actionButtons = `
                <div class="request-actions">
                    <button class="btn-approve" onclick="approveRental(${request.id}, ${listingId})">
                        <i class="fas fa-check"></i> Approve
                    </button>
                    <button class="btn-reject" onclick="rejectRental(${request.id}, ${listingId})">
                        <i class="fas fa-times"></i> Reject
                    </button>
                </div>
            `;
        } else if (request.status === 'Approved' || request.status === 'Active') {
            actionButtons = `
                <div class="request-actions">
                    <button class="btn-download-contract" onclick="downloadContract(${request.id})">
                        <i class="fas fa-file-pdf"></i> Download Contract
                    </button>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="request-header">
                <div>
                    <h4>${request.renter_name}</h4>
                    <div class="request-meta">
                        <i class="fas fa-phone"></i> ${request.renter_phone}
                        ${request.renter_email ? ` | <i class="fas fa-envelope"></i> ${request.renter_email}` : ''}
                    </div>
                </div>
                <span class="status-badge status-${statusClass}">${request.status}</span>
            </div>
            <div class="request-details">
                <div class="request-detail">
                    <i class="fas fa-calendar-alt"></i>
                    <span><strong>Dates:</strong> ${startDate} to ${endDate}</span>
                </div>
                <div class="request-detail">
                    <i class="fas fa-clock"></i>
                    <span><strong>Duration:</strong> ${request.days} day${request.days !== 1 ? 's' : ''}</span>
                </div>
                <div class="request-detail">
                    <i class="fas fa-rupee-sign"></i>
                    <span><strong>Total Amount:</strong> ₹${request.total_amount.toLocaleString()}</span>
                </div>
                <div class="request-detail">
                    <i class="fas fa-calendar"></i>
                    <span><strong>Requested:</strong> ${createdDate}</span>
                </div>
            </div>
            ${actionButtons}
        `;
        
        return card;
    };

    // Approve rental
    window.approveRental = async function(rentalId, listingId) {
        if (!confirm('Are you sure you want to approve this rental request? This will lock the dates and cancel any conflicting pending requests.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/rentals/${rentalId}/approve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Rental request approved successfully', 'success');
                // Reload requests
                viewRentalRequests(listingId);
            } else {
                alert('Error: ' + (data.message || 'Failed to approve request'));
            }
        } catch (error) {
            console.error('Error approving rental:', error);
            alert('An error occurred. Please try again.');
        }
    };

    // Reject rental
    window.rejectRental = async function(rentalId, listingId) {
        if (!confirm('Are you sure you want to reject this rental request?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/rentals/${rentalId}/reject`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Rental request rejected', 'success');
                // Reload requests
                viewRentalRequests(listingId);
            } else {
                alert('Error: ' + (data.message || 'Failed to reject request'));
            }
        } catch (error) {
            console.error('Error rejecting rental:', error);
            alert('An error occurred. Please try again.');
        }
    };

    // Download contract
    window.downloadContract = async function(rentalId) {
        try {
            const response = await fetch(`/api/rentals/${rentalId}/generate-contract`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Rental_Agreement_${rentalId}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await response.json();
                alert('Error: ' + (data.message || 'Failed to download contract'));
            }
        } catch (error) {
            console.error('Error downloading contract:', error);
            alert('An error occurred while downloading the contract. Please try again.');
        }
    };

    // Show notification
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#4a7c2c' : '#c94843'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10002;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});






// Rent Dashboard Functionality

document.addEventListener('DOMContentLoaded', function() {
    let rentals = [];

    // Load user's rentals
    loadMyRentals();

    // Load rentals from API
    async function loadMyRentals() {
        const loadingState = document.getElementById('loading-state');
        const emptyState = document.getElementById('empty-state');
        const rentalsGrid = document.getElementById('rentals-grid');

        try {
            loadingState.style.display = 'block';
            rentalsGrid.innerHTML = '';
            emptyState.style.display = 'none';

            const response = await fetch('/api/my_rentals');
            const data = await response.json();

            rentals = data;

            if (rentals.length === 0) {
                emptyState.style.display = 'block';
                rentalsGrid.innerHTML = '';
            } else {
                displayRentals(rentals);
            }
        } catch (error) {
            console.error('Error loading rentals:', error);
            rentalsGrid.innerHTML = '<p style="text-align: center; color: #c94843; padding: 2rem;">Error loading rentals. Please try again.</p>';
        } finally {
            loadingState.style.display = 'none';
        }
    }

    // Display rentals as cards
    function displayRentals(rentals) {
        const rentalsGrid = document.getElementById('rentals-grid');
        rentalsGrid.innerHTML = '';

        rentals.forEach(rental => {
            const card = createRentalCard(rental);
            rentalsGrid.appendChild(card);
        });
    }

    // Create rental card
    function createRentalCard(rental) {
        const card = document.createElement('div');
        card.className = 'rental-card';
        
        const imageUrl = rental.main_image ? `/static/${rental.main_image}` : '/assets/carousel1.jpg';
        
        // Format dates (parse without timezone conversion to avoid day shift)
        const parseDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };
        
        const startDate = parseDate(rental.start_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        const endDate = parseDate(rental.end_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        // Determine status and styling based on rental status
        let statusClass = '';
        let statusText = rental.status_display || rental.status;
        let expiryClass = '';
        let expiryText = '';
        
        // Map status to display and styling
        if (rental.status === 'Pending') {
            statusClass = 'pending';
            statusText = 'Waiting for approval';
            expiryClass = 'pending';
            expiryText = 'Waiting for owner approval';
        } else if (rental.status === 'Approved') {
            if (rental.is_expired) {
                statusClass = 'expired';
                statusText = 'Expired';
                expiryClass = 'expired';
                expiryText = 'Expired';
            } else if (rental.days_remaining <= 3) {
                statusClass = 'expiring-soon';
                statusText = 'Approved';
                expiryClass = 'expiring-soon';
                expiryText = `${rental.days_remaining} day${rental.days_remaining !== 1 ? 's' : ''} left`;
            } else {
                statusClass = 'approved';
                statusText = 'Approved';
                expiryClass = 'active';
                expiryText = `${rental.days_remaining} day${rental.days_remaining !== 1 ? 's' : ''} remaining`;
            }
        } else if (rental.status === 'Cancelled') {
            statusClass = 'rejected';
            statusText = 'Rejected';
            expiryClass = 'rejected';
            expiryText = 'Request was rejected';
        } else if (rental.status === 'Active') {
            if (rental.is_expired) {
                statusClass = 'expired';
                statusText = 'Expired';
                expiryClass = 'expired';
                expiryText = 'Expired';
            } else if (rental.days_remaining <= 3) {
                statusClass = 'expiring-soon';
                statusText = 'Active';
                expiryClass = 'expiring-soon';
                expiryText = `${rental.days_remaining} day${rental.days_remaining !== 1 ? 's' : ''} left`;
            } else {
                statusClass = 'active';
                statusText = 'Active';
                expiryClass = 'active';
                expiryText = `${rental.days_remaining} day${rental.days_remaining !== 1 ? 's' : ''} remaining`;
            }
        } else {
            // Fallback for other statuses
            statusClass = '';
            statusText = rental.status;
            expiryClass = '';
            expiryText = rental.status;
        }
        
        card.innerHTML = `
            <div class="card-image-wrapper">
                <img src="${imageUrl}" alt="${rental.title}" class="card-image" onerror="this.src='/assets/carousel1.jpg'">
                <div class="card-status ${statusClass}">${statusText}</div>
            </div>
            <div class="card-body">
                <div class="card-category">${rental.category}</div>
                <h3 class="card-title">${rental.title}</h3>
                <div class="card-details">
                    <div class="card-detail">
                        <i class="fas fa-tag"></i>
                        <span>${rental.equipment_name}</span>
                    </div>
                    <div class="card-detail">
                        <i class="fas fa-industry"></i>
                        <span>${rental.brand}</span>
                    </div>
                </div>
                <div class="card-price">
                    ₹${rental.total_amount.toLocaleString()}
                    <span class="card-price-type">Total Amount</span>
                </div>
                <div class="card-location">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${rental.location}</span>
                </div>
                <div class="rental-dates">
                    <div class="rental-dates-header">
                        <i class="fas fa-calendar-alt"></i>
                        Rental Period
                    </div>
                    <div class="date-row">
                        <span class="date-label">Start Date:</span>
                        <span class="date-value">${startDate}</span>
                    </div>
                    <div class="date-row">
                        <span class="date-label">End Date:</span>
                        <span class="date-value">${endDate}</span>
                    </div>
                    <div class="date-row">
                        <span class="date-label">Duration:</span>
                        <span class="date-value">${rental.days} day${rental.days !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="expiry-info">
                        <span class="expiry-label">Status:</span>
                        <span class="expiry-value ${expiryClass}">${expiryText}</span>
                    </div>
                </div>
                <div class="owner-info">
                    <div class="owner-info-header">
                        <i class="fas fa-user"></i>
                        Owner Information
                    </div>
                    <div class="owner-detail">
                        <i class="fas fa-user-circle"></i>
                        <span>${rental.owner_name}</span>
                    </div>
                    <div class="owner-detail">
                        <i class="fas fa-phone"></i>
                        <span>${rental.phone} (${rental.contact_method})</span>
                    </div>
                </div>
            </div>
            <div class="card-footer">
                ${rental.status === 'Approved' || rental.status === 'Active' ? `
                <button class="btn-download-contract" onclick="downloadContract(${rental.id})">
                    <i class="fas fa-file-pdf"></i> Download Contract
                </button>
                ` : ''}
                <a href="/renting" class="btn-view-listing">
                    <i class="fas fa-search"></i> Rent More Equipment
                </a>
            </div>
        `;

        return card;
    }
    
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
});



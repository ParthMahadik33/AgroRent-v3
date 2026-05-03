// Renting Page Functionality

// Global state for date selection (must be outside DOMContentLoaded for global functions)
let selectedStartDate = null;
let selectedEndDate = null;
let isSelectingRange = false;

document.addEventListener('DOMContentLoaded', function () {
    let allListings = [];
    let currentListing = null;

    // Initialize
    loadListings();
    initEventListeners();

    // Load listings from API
    async function loadListings() {
        const loadingState = document.getElementById('loading-state');
        const emptyState = document.getElementById('empty-state');
        const listingsGrid = document.getElementById('listings-grid');

        try {
            loadingState.style.display = 'block';
            listingsGrid.innerHTML = '';
            toggleEmptyState(false);

            const response = await fetch('/api/listings');
            const listings = await response.json();

            allListings = listings;

            if (listings.length === 0) {
                toggleEmptyState(true);
                listingsGrid.innerHTML = '';
            } else {
                displayListings(listings);
                toggleEmptyState(false);
            }
        } catch (error) {
            console.error('Error loading listings:', error);
            listingsGrid.innerHTML = '<p style="text-align: center; color: #c94843;">Error loading listings. Please try again.</p>';
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

        card.innerHTML = `
            <img src="${imageUrl}" alt="${listing.title}" class="card-image" onerror="this.src='/assets/carousel1.jpg'">
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
            </div>
            <div class="card-footer">
                <button class="btn-view-details" onclick="viewDetails(${listing.id})">
                    <i class="fas fa-info-circle"></i> View More Details
                </button>
            </div>
        `;

        return card;
    }

    // View listing details
    window.viewDetails = async function (listingId) {
        try {
            const response = await fetch(`/api/listing/${listingId}`);
            const listing = await response.json();

            currentListing = listing;
            showDetailsModal(listing);
        } catch (error) {
            console.error('Error loading listing details:', error);
            alert('Error loading listing details. Please try again.');
        }
    };

    // Show details modal
    async function showDetailsModal(listing) {
        const modal = document.getElementById('details-modal');
        const modalBody = document.getElementById('modal-body');

        const mainImageUrl = listing.main_image ? `/static/${listing.main_image}` : '/assets/carousel1.jpg';
        const additionalImages = listing.additional_images || [];
        const allImages = [mainImageUrl, ...additionalImages.map(img => `/static/${img}`)].filter(Boolean);

        // Fetch availability data
        let pendingDates = [];
        let confirmedDates = [];
        try {
            const availabilityResponse = await fetch(`/api/listing/${listing.id}/availability`);
            const availabilityData = await availabilityResponse.json();
            pendingDates = availabilityData.pending_dates || [];
            confirmedDates = availabilityData.confirmed_dates || [];
        } catch (error) {
            console.error('Error loading availability:', error);
        }

        modalBody.innerHTML = `
            <div class="modal-image-gallery">
                <img src="${allImages[0]}" alt="${listing.title}" class="modal-main-image" id="main-modal-image">
                ${allImages.length > 1 ? `
                <div class="modal-thumbnails">
                    ${allImages.slice(1, 5).map((img, idx) => `
                        <img src="${img}" alt="Thumbnail ${idx + 1}" class="modal-thumbnail" onclick="changeMainImage('${img}')">
                    `).join('')}
                </div>
                ` : ''}
            </div>
            <h2 class="modal-title">${listing.title}</h2>
            <div class="modal-info-grid">
                <div class="modal-info-item">
                    <i class="fas fa-tag"></i>
                    <div>
                        <div class="modal-info-label">Equipment</div>
                        <div class="modal-info-value">${listing.equipment_name}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-industry"></i>
                    <div>
                        <div class="modal-info-label">Brand</div>
                        <div class="modal-info-value">${listing.brand}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-calendar"></i>
                    <div>
                        <div class="modal-info-label">Year</div>
                        <div class="modal-info-value">${listing.year || 'N/A'}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-check-circle"></i>
                    <div>
                        <div class="modal-info-label">Condition</div>
                        <div class="modal-info-value">${listing.condition}</div>
                    </div>
                </div>
                ${listing.power_spec ? `
                <div class="modal-info-item">
                    <i class="fas fa-bolt"></i>
                    <div>
                        <div class="modal-info-label">Power/Spec</div>
                        <div class="modal-info-value">${listing.power_spec}</div>
                    </div>
                </div>
                ` : ''}
                <div class="modal-info-item">
                    <i class="fas fa-rupee-sign"></i>
                    <div>
                        <div class="modal-info-label">Price</div>
                        <div class="modal-info-value">₹${listing.price.toLocaleString()} / ${listing.pricing_type}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <div>
                        <div class="modal-info-label">Location</div>
                        <div class="modal-info-value">${listing.village_city}, ${listing.district}, ${listing.state} - ${listing.pincode}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-route"></i>
                    <div>
                        <div class="modal-info-label">Service Radius</div>
                        <div class="modal-info-value">${listing.service_radius}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-truck"></i>
                    <div>
                        <div class="modal-info-label">Transport</div>
                        <div class="modal-info-value">${listing.transport_included === 'Yes' ? 'Included' : 'Not Included'}${listing.transport_charge ? ` (₹${listing.transport_charge})` : ''}</div>
                    </div>
                </div>
                <div class="modal-info-item">
                    <i class="fas fa-calendar-check"></i>
                    <div>
                        <div class="modal-info-label">Available From</div>
                        <div class="modal-info-value">${new Date(listing.available_from).toLocaleDateString()}</div>
                    </div>
                </div>
                ${listing.available_till ? `
                <div class="modal-info-item">
                    <i class="fas fa-calendar-times"></i>
                    <div>
                        <div class="modal-info-label">Available Till</div>
                        <div class="modal-info-value">${new Date(listing.available_till).toLocaleDateString()}</div>
                    </div>
                </div>
                ` : ''}
                <div class="modal-info-item">
                    <i class="fas fa-phone"></i>
                    <div>
                        <div class="modal-info-label">Contact</div>
                        <div class="modal-info-value">${listing.phone} (${listing.contact_method})</div>
                    </div>
                </div>
                
                <div class="modal-ai-section">
                    <h3><i class="fas fa-robot"></i> AI Condition Analysis</h3>
                    <div id="ai-analysis-container-${listing.id}" class="ai-analysis-container">
                        <button class="btn-ai-analyze" onclick="analyzeCondition('${mainImageUrl}', ${listing.id})">
                            <i class="fas fa-search"></i> Check Condition Score
                        </button>
                    </div>
                </div>
            </div>
            <div class="modal-availability-calendar">
                <h3><i class="fas fa-calendar-alt"></i> Select Rental Dates</h3>
                <p class="calendar-instruction">Click on available dates to select your rental period</p>
                <div class="calendar-container" id="availability-calendar-${listing.id}"></div>
                <div class="calendar-legend">
                    <div class="legend-item">
                        <span class="legend-available"></span>
                        <span>Available</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-pending"></span>
                        <span>Pending Approval</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-confirmed"></span>
                        <span>Confirmed/Booked</span>
                    </div>
                </div>
                <div id="rent-button-container-${listing.id}" class="rent-button-container"></div>
            </div>
            <div class="modal-description">
                <h3>Description</h3>
                <p>${listing.description}</p>
            </div>
            ${listing.rules ? `
            <div class="modal-rules">
                <h3>Rules & Terms</h3>
                <p>${listing.rules}</p>
            </div>
            ` : ''}
            <div class="modal-actions">
                <button class="btn-rent" onclick="scrollToCalendar(${listing.id})">
                    <i class="fas fa-calendar-check"></i> Select Dates to Rent
                </button>
            </div>
        `;

        // Reset selection when opening modal
        selectedStartDate = null;
        selectedEndDate = null;

        // Render calendar after modal is shown
        setTimeout(() => {
            renderAvailabilityCalendar(listing.id, pendingDates, confirmedDates, listing.available_from, listing.available_till);
            updateRentButtonState(listing.id);
        }, 100);

        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    // Render availability calendar with interactive date selection
    function renderAvailabilityCalendar(listingId, pendingDates, confirmedDates, availableFrom, availableTill) {
        const calendarContainer = document.getElementById(`availability-calendar-${listingId}`);
        if (!calendarContainer) return;

        const pendingDatesSet = new Set(pendingDates);
        const confirmedDatesSet = new Set(confirmedDates);
        const today = new Date();
        const currentMonth = today.getMonth();
        const currentYear = today.getFullYear();

        // Parse available dates
        const availableFromDate = availableFrom ? new Date(availableFrom) : today;
        const availableTillDate = availableTill ? new Date(availableTill) : null;

        // Generate calendar for current month and next 2 months
        let calendarHTML = '';

        for (let monthOffset = 0; monthOffset < 3; monthOffset++) {
            const month = (currentMonth + monthOffset) % 12;
            const year = currentYear + Math.floor((currentMonth + monthOffset) / 12);
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const daysInMonth = lastDay.getDate();
            const startingDayOfWeek = firstDay.getDay();

            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'];

            calendarHTML += `
                <div class="calendar-month">
                    <div class="calendar-month-header">
                        <h4>${monthNames[month]} ${year}</h4>
                    </div>
                    <div class="calendar-weekdays">
                        <div class="calendar-weekday">Sun</div>
                        <div class="calendar-weekday">Mon</div>
                        <div class="calendar-weekday">Tue</div>
                        <div class="calendar-weekday">Wed</div>
                        <div class="calendar-weekday">Thu</div>
                        <div class="calendar-weekday">Fri</div>
                        <div class="calendar-weekday">Sat</div>
                    </div>
                    <div class="calendar-days">
            `;

            // Add empty cells for days before the first day of the month
            for (let i = 0; i < startingDayOfWeek; i++) {
                calendarHTML += '<div class="calendar-day empty"></div>';
            }

            // Add days of the month
            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month, day);
                date.setHours(0, 0, 0, 0);
                const todayNormalized = new Date(today);
                todayNormalized.setHours(0, 0, 0, 0);
                // Format date as YYYY-MM-DD without timezone conversion
                const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

                const isPending = pendingDatesSet.has(dateString);
                const isConfirmed = confirmedDatesSet.has(dateString);
                const isPast = date < todayNormalized;
                const isBeforeAvailable = availableFromDate && date < availableFromDate;
                const isAfterAvailable = availableTillDate && date > availableTillDate;
                const isAvailable = !isPast && !isPending && !isConfirmed && !isBeforeAvailable && !isAfterAvailable;

                // Check if date is in selected range
                let isSelected = false;
                let isStartDate = false;
                let isEndDate = false;
                let isInRange = false;

                if (selectedStartDate && selectedEndDate) {
                    const start = new Date(selectedStartDate);
                    const end = new Date(selectedEndDate);
                    if (dateString === selectedStartDate) {
                        isStartDate = true;
                        isSelected = true;
                    } else if (dateString === selectedEndDate) {
                        isEndDate = true;
                        isSelected = true;
                    } else if (date >= start && date <= end) {
                        isInRange = true;
                    }
                } else if (selectedStartDate && dateString === selectedStartDate) {
                    isStartDate = true;
                    isSelected = true;
                }

                let dayClass = 'calendar-day';
                let title = '';
                let clickable = false;

                if (isPast || isBeforeAvailable || isAfterAvailable) {
                    dayClass += ' disabled';
                    title = 'Not Available';
                } else if (isConfirmed) {
                    dayClass += ' confirmed';
                    title = 'Confirmed/Booked';
                } else if (isPending) {
                    dayClass += ' pending';
                    title = 'Pending Approval';
                } else {
                    dayClass += ' available';
                    title = 'Available - Click to select';
                    clickable = true;
                }

                // Add selection classes - all dates in range get same color
                if (isStartDate || isEndDate || isInRange) {
                    dayClass += ' selected-range';
                    if (isStartDate) {
                        dayClass += ' selected-start';
                    }
                    if (isEndDate) {
                        dayClass += ' selected-end';
                    }
                }

                // Add click handler for available dates
                const clickHandler = clickable ? `onclick="selectDate('${dateString}', ${listingId})"` : '';

                calendarHTML += `<div class="${dayClass}" data-date="${dateString}" ${clickHandler} title="${title}">${day}</div>`;
            }

            calendarHTML += `
                    </div>
                </div>
            `;
        }

        calendarContainer.innerHTML = calendarHTML;

        // Update rent button state
        updateRentButtonState(listingId);
    }

    // Handle date selection with double-click to unselect
    window.selectDate = function (dateString, listingId) {
        // Parse date without timezone conversion to avoid day shift
        const parseDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };

        const date = parseDate(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Don't allow selecting past dates or booked dates
        if (date < today) return;

        // Check if date is available (not booked or pending)
        const dayElement = document.querySelector(`[data-date="${dateString}"]`);
        if (!dayElement || dayElement.classList.contains('confirmed') || dayElement.classList.contains('disabled')) {
            return;
        }

        // Check for double-click to unselect
        const now = Date.now();
        const lastClickTime = window.lastDateClickTime || 0;
        const lastClickDate = window.lastDateClickDate || '';

        if (dateString === lastClickDate && (now - lastClickTime) < 300) {
            // Double-click detected - unselect
            if (selectedStartDate === dateString) {
                selectedStartDate = null;
                selectedEndDate = null;
            } else if (selectedEndDate === dateString) {
                selectedEndDate = null;
            } else if (selectedStartDate && selectedEndDate) {
                // Check if clicked date is in the range
                const parseDate = (dateStr) => {
                    const [year, month, day] = dateStr.split('-').map(Number);
                    return new Date(year, month - 1, day);
                };
                const start = parseDate(selectedStartDate);
                const end = parseDate(selectedEndDate);
                const clicked = parseDate(dateString);

                if (clicked >= start && clicked <= end) {
                    // If clicking in the middle of range, reset selection
                    selectedStartDate = null;
                    selectedEndDate = null;
                }
            }

            window.lastDateClickTime = 0;
            window.lastDateClickDate = '';

            // Re-render calendar
            const listing = currentListing;
            if (listing) {
                fetchAvailabilityAndRender(listing.id, listing.available_from, listing.available_till);
                setTimeout(() => updateRentButtonState(listing.id), 150);
            }
            return;
        }

        // Track click for double-click detection
        window.lastDateClickTime = now;
        window.lastDateClickDate = dateString;

        if (!selectedStartDate) {
            // First date selected - set as start date
            selectedStartDate = dateString;
            selectedEndDate = null;
            isSelectingRange = true;
        } else if (!selectedEndDate) {
            // Second date selected - set as end date
            const parseDate = (dateStr) => {
                const [year, month, day] = dateStr.split('-').map(Number);
                return new Date(year, month - 1, day);
            };
            const start = parseDate(selectedStartDate);
            const end = parseDate(dateString);

            if (end < start) {
                // If end is before start, swap them
                selectedEndDate = selectedStartDate;
                selectedStartDate = dateString;
            } else {
                selectedEndDate = dateString;
            }

            // Validate the range doesn't include booked dates
            if (validateDateRange(selectedStartDate, selectedEndDate, listingId)) {
                isSelectingRange = false;
            } else {
                // Reset if range is invalid
                selectedStartDate = null;
                selectedEndDate = null;
                alert('Selected date range includes booked dates. Please select a different range.');
                return;
            }
        } else {
            // New selection - reset and start over
            selectedStartDate = dateString;
            selectedEndDate = null;
            isSelectingRange = true;
        }

        // Re-render calendar with selection
        const listing = currentListing;
        if (listing) {
            // Re-fetch availability and re-render
            fetchAvailabilityAndRender(listing.id, listing.available_from, listing.available_till);
            // Update rent button state after a short delay to ensure DOM is updated
            setTimeout(() => updateRentButtonState(listing.id), 150);
        }
    };

    // Validate date range doesn't include booked dates
    async function validateDateRange(startDate, endDate, listingId) {
        try {
            const response = await fetch(`/api/listing/${listingId}/availability`);
            const data = await response.json();

            const confirmedDates = new Set(data.confirmed_dates || []);

            const parseDate = (dateStr) => {
                const [year, month, day] = dateStr.split('-').map(Number);
                return new Date(year, month - 1, day);
            };
            const start = parseDate(startDate);
            const end = parseDate(endDate);
            const current = new Date(start);

            while (current <= end) {
                // Format date as YYYY-MM-DD without timezone conversion
                const year = current.getFullYear();
                const month = String(current.getMonth() + 1).padStart(2, '0');
                const day = String(current.getDate()).padStart(2, '0');
                const dateString = `${year}-${month}-${day}`;
                if (confirmedDates.has(dateString)) {
                    return false; // Range includes booked date
                }
                current.setDate(current.getDate() + 1);
            }

            return true; // Range is valid
        } catch (error) {
            console.error('Error validating date range:', error);
            return false;
        }
    }

    // Fetch availability and re-render calendar
    async function fetchAvailabilityAndRender(listingId, availableFrom, availableTill) {
        try {
            const response = await fetch(`/api/listing/${listingId}/availability`);
            const data = await response.json();
            renderAvailabilityCalendar(listingId, data.pending_dates || [], data.confirmed_dates || [], availableFrom, availableTill);
        } catch (error) {
            console.error('Error fetching availability:', error);
        }
    }

    // Update rent button state based on selection
    function updateRentButtonState(listingId) {
        const rentButtonContainer = document.getElementById(`rent-button-container-${listingId}`);
        if (!rentButtonContainer) {
            // Container might not exist yet, try again after a short delay
            setTimeout(() => updateRentButtonState(listingId), 100);
            return;
        }

        if (selectedStartDate && selectedEndDate) {
            // Parse dates without timezone conversion (YYYY-MM-DD format)
            const parseDate = (dateStr) => {
                const [year, month, day] = dateStr.split('-').map(Number);
                return new Date(year, month - 1, day);
            };

            const start = parseDate(selectedStartDate);
            const end = parseDate(selectedEndDate);
            const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

            // Format dates for display
            const startFormatted = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const endFormatted = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

            rentButtonContainer.innerHTML = `
                <div class="selected-dates-summary">
                    <div class="selected-dates-info">
                        <i class="fas fa-calendar-check"></i>
                        <div>
                            <div class="dates-range">${startFormatted} - ${endFormatted}</div>
                            <div class="days-count">${days} day${days !== 1 ? 's' : ''}</div>
                        </div>
                    </div>
                    <div class="selected-dates-actions">
                        <button class="btn-clear-selection" onclick="clearDateSelection(${listingId})" title="Clear selection">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn-rent-calendar" onclick="completeRentalFromCalendar(${listingId})">
                            <i class="fas fa-check"></i> Rent Now
                        </button>
                    </div>
                </div>
            `;
        } else if (selectedStartDate) {
            rentButtonContainer.innerHTML = `
                <div class="selected-dates-summary">
                    <div class="selected-dates-info">
                        <i class="fas fa-calendar"></i>
                        <div>
                            <div class="dates-range">Select end date</div>
                            <div class="days-count">Start: ${(function () {
                    const [year, month, day] = selectedStartDate.split('-').map(Number);
                    const date = new Date(year, month - 1, day);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                })()}</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            rentButtonContainer.innerHTML = `
                <div class="selected-dates-summary">
                    <div class="selected-dates-info">
                        <i class="fas fa-mouse-pointer"></i>
                        <div>
                            <div class="dates-range">Select dates on calendar</div>
                            <div class="days-count">Click start date, then end date</div>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // Clear date selection
    window.clearDateSelection = function (listingId) {
        selectedStartDate = null;
        selectedEndDate = null;
        const listing = currentListing;
        if (listing) {
            fetchAvailabilityAndRender(listing.id, listing.available_from, listing.available_till);
        }
    };

    // Complete rental from calendar selection
    window.completeRentalFromCalendar = async function (listingId) {
        if (!selectedStartDate || !selectedEndDate) {
            alert('Please select a date range on the calendar');
            return;
        }

        const listing = currentListing;
        if (!listing) return;

        // Calculate days (parse dates without timezone conversion)
        const parseDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };
        const start = parseDate(selectedStartDate);
        const end = parseDate(selectedEndDate);
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;

        // Validate one more time
        const isValid = await validateDateRange(selectedStartDate, selectedEndDate, listingId);
        if (!isValid) {
            alert('Selected dates are already booked. Please choose different dates.');
            return;
        }

        // Calculate total amount
        const price = parseFloat(listing.price);
        const pricingType = listing.pricing_type;
        let totalAmount = 0;

        if (pricingType === 'Per day') {
            totalAmount = price * days;
        } else if (pricingType === 'Per hour') {
            totalAmount = price * days * 8;
        } else if (pricingType === 'Per acre') {
            totalAmount = price * days;
        } else {
            totalAmount = price;
        }

        // Add transport charge if applicable
        if (listing.transport_included === 'No' && listing.transport_charge) {
            totalAmount += parseFloat(listing.transport_charge);
        }

        // Show agreement preview modal
        showAgreementPreview(listingId, listing, selectedStartDate, selectedEndDate, days, totalAmount);
    };

    // Show agreement preview modal
    async function showAgreementPreview(listingId, listing, startDate, endDate, days, totalAmount) {
        // Fetch contract preview data
        try {
            const url = `/api/rentals/0/contract-preview?listing_id=${listingId}&start_date=${startDate}&end_date=${endDate}&days=${days}&total_amount=${totalAmount}`;
            const response = await fetch(url);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Network error' }));
                alert('Error loading agreement preview: ' + (errorData.message || `HTTP ${response.status}`));
                return;
            }

            const data = await response.json();

            if (!data.success) {
                alert('Error loading agreement preview: ' + (data.message || 'Unknown error'));
                return;
            }

            const contractData = data.data;

            // Create agreement preview modal
            const modal = document.createElement('div');
            modal.className = 'agreement-modal';
            modal.id = 'agreement-modal';
            modal.innerHTML = `
                <div class="agreement-modal-content">
                    <div class="agreement-modal-header">
                        <h2><i class="fas fa-file-contract"></i> Rental Agreement Preview</h2>
                        <button class="close-agreement-modal" onclick="closeAgreementModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="agreement-preview-container">
                        <div class="agreement-preview">
                            <div class="agreement-section">
                                <h3>Owner/Lessor Details</h3>
                                <p><strong>Name:</strong> ${escapeHtml(contractData.owner_name)}</p>
                                <p><strong>Address:</strong> ${escapeHtml(contractData.owner_address)}</p>
                            </div>
                            <div class="agreement-section">
                                <h3>Renter/Lessee Details</h3>
                                <p><strong>Name:</strong> ${escapeHtml(contractData.renter_name)}</p>
                                <div class="form-group">
                                    <label for="renter-address">Your Address <span class="required">*</span></label>
                                    <textarea id="renter-address" placeholder="Enter your complete address" required></textarea>
                                </div>
                            </div>
                            <div class="agreement-section">
                                <h3>Machinery Details</h3>
                                <p><strong>Machine Name:</strong> ${escapeHtml(contractData.machine_name)}</p>
                                <p><strong>Brand/Model:</strong> ${escapeHtml(contractData.brand || contractData.machine_model)}</p>
                            </div>
                            <div class="agreement-section">
                                <h3>Rental Terms</h3>
                                <p><strong>Rental Amount:</strong> ₹${parseFloat(contractData.total_amount).toFixed(2)}</p>
                                <p><strong>Rental Period:</strong> ${contractData.start_date} to ${contractData.end_date}</p>
                                <p><strong>Number of Days:</strong> ${contractData.days}</p>
                                <div class="form-group">
                                    <label for="location-of-use">Location of Use <span class="required">*</span></label>
                                    <input type="text" id="location-of-use" placeholder="Where will you use this equipment?" required>
                                </div>
                            </div>
                            <div class="agreement-section">
                                <h3>Terms & Conditions</h3>
                                <ul class="terms-list">
                                    <li>Payment is due on or before the rental start date</li>
                                    <li>You are responsible for any damage due to misuse or negligence</li>
                                    <li>Late return will incur a 10% daily fee</li>
                                    <li>Equipment must be returned in the same condition</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="agreement-modal-actions">
                        <button class="btn-cancel" onclick="closeAgreementModal()">Cancel</button>
                        <button class="btn-submit-rental" onclick="submitRentalWithAgreement(${listingId}, '${startDate}', ${days}, ${totalAmount})">
                            <i class="fas fa-check"></i> Submit Rental Request
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            setTimeout(() => modal.classList.add('show'), 10);
            document.body.style.overflow = 'hidden';
        } catch (error) {
            console.error('Error loading agreement preview:', error);
            alert('Error loading agreement preview: ' + (error.message || 'Please try again.'));
        }
    }

    // Close agreement modal
    window.closeAgreementModal = function () {
        const modal = document.getElementById('agreement-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
                document.body.style.overflow = 'visible';
            }, 300);
        }
    }

    // Submit rental with agreement data
    window.submitRentalWithAgreement = async function (listingId, startDate, days, totalAmount) {
        const renterAddress = document.getElementById('renter-address').value.trim();
        const locationOfUse = document.getElementById('location-of-use').value.trim();

        if (!renterAddress) {
            alert('Please enter your address');
            return;
        }

        if (!locationOfUse) {
            alert('Please specify the location where you will use the equipment');
            return;
        }

        const formData = new FormData();
        formData.append('listing_id', listingId);
        formData.append('start_date', startDate);
        formData.append('days', days);
        formData.append('renter_address', renterAddress);
        formData.append('location_of_use', locationOfUse);

        try {
            const response = await fetch('/rent_equipment', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Close agreement modal
                closeAgreementModal();

                // Show success message with contract download option
                if (confirm('Rental request submitted successfully! The owner will review and approve your request.\n\nWould you like to download a draft copy of the agreement?')) {
                    // Generate and download contract (use POST method)
                    try {
                        const contractResponse = await fetch(`/api/rentals/${data.rental_id}/generate-contract`, {
                            method: 'POST'
                        });

                        if (contractResponse.ok) {
                            const blob = await contractResponse.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `Rental_Agreement_${data.rental_id}.pdf`;
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            document.body.removeChild(a);
                        } else {
                            const errorData = await contractResponse.json().catch(() => ({ message: 'Failed to download contract' }));
                            alert('Error downloading contract: ' + (errorData.message || 'Unknown error'));
                        }
                    } catch (error) {
                        console.error('Error downloading contract:', error);
                        alert('An error occurred while downloading the contract.');
                    }
                }

                // Reset selection
                selectedStartDate = null;
                selectedEndDate = null;
                // Close details modal
                document.getElementById('details-modal').classList.remove('show');
                document.body.style.overflow = 'visible';
                // Reload listings
                if (typeof loadListings === 'function') {
                    loadListings();
                }
            } else {
                const errorMessage = data.message || 'Failed to submit rental request';
                if (data.booked) {
                    alert('These dates are already booked. ' + errorMessage);
                    // Reset selection
                    selectedStartDate = null;
                    selectedEndDate = null;
                    // Re-render calendar
                    const listing = currentListing;
                    if (listing) {
                        fetchAvailabilityAndRender(listing.id, listing.available_from, listing.available_till);
                    }
                    closeAgreementModal();
                } else {
                    alert('Error: ' + errorMessage);
                }
            }
        } catch (error) {
            console.error('Error submitting rental:', error);
            alert('An error occurred. Please try again.');
        }
    }

    // Escape HTML helper
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Submit rental from calendar
    async function submitRentalFromCalendar(listingId, startDate, days) {
        const formData = new FormData();
        formData.append('listing_id', listingId);
        formData.append('start_date', startDate);
        formData.append('days', days);

        try {
            const response = await fetch('/rent_equipment', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                alert('Rental request submitted successfully! The owner will review and approve your request.');
                // Reset selection
                selectedStartDate = null;
                selectedEndDate = null;
                // Close modal
                document.getElementById('details-modal').classList.remove('show');
                document.body.style.overflow = 'visible';
                // Reload listings
                if (typeof loadListings === 'function') {
                    loadListings();
                }
            } else {
                const errorMessage = data.message || 'Failed to submit rental request';
                if (data.booked) {
                    alert('These dates are already booked. ' + errorMessage);
                    // Reset selection
                    selectedStartDate = null;
                    selectedEndDate = null;
                    // Re-render calendar
                    const listing = currentListing;
                    if (listing) {
                        fetchAvailabilityAndRender(listing.id, listing.available_from, listing.available_till);
                    }
                } else {
                    alert('Error: ' + errorMessage);
                }
            }
        } catch (error) {
            console.error('Error submitting rental:', error);
            alert('An error occurred. Please try again.');
        }
    }

    // Scroll to calendar
    window.scrollToCalendar = function (listingId) {
        const calendarSection = document.querySelector('.modal-availability-calendar');
        if (calendarSection) {
            calendarSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Highlight calendar briefly
            calendarSection.style.animation = 'pulse 0.5s ease';
            setTimeout(() => {
                calendarSection.style.animation = '';
            }, 500);
        }
    };

    // Change main image in modal
    window.changeMainImage = function (imageUrl) {
        const mainImage = document.getElementById('main-modal-image');
        if (mainImage) {
            mainImage.src = imageUrl;
        }
        // Update active thumbnail
        document.querySelectorAll('.modal-thumbnail').forEach(thumb => {
            thumb.classList.remove('active');
            if (thumb.src.includes(imageUrl)) {
                thumb.classList.add('active');
            }
        });
    };

    // Open rental form
    window.openRentalForm = function (listingId) {
        if (!currentListing || currentListing.id !== listingId) {
            // Reload listing details if needed
            viewDetails(listingId);
            setTimeout(() => showRentalForm(listingId), 500);
        } else {
            showRentalForm(listingId);
        }
    };

    // Show rental form
    function showRentalForm(listingId) {
        const listing = currentListing;
        if (!listing) return;

        const rentalModal = document.getElementById('rental-modal');
        const rentalFormContainer = document.getElementById('rental-form-container');

        // Format today's date as YYYY-MM-DD without timezone conversion
        const todayDate = new Date();
        const todayYear = todayDate.getFullYear();
        const todayMonth = String(todayDate.getMonth() + 1).padStart(2, '0');
        const todayDay = String(todayDate.getDate()).padStart(2, '0');
        const today = `${todayYear}-${todayMonth}-${todayDay}`;

        // Format max date if available
        let maxDate = '';
        if (listing.available_till) {
            const maxDateObj = new Date(listing.available_till);
            const maxYear = maxDateObj.getFullYear();
            const maxMonth = String(maxDateObj.getMonth() + 1).padStart(2, '0');
            const maxDay = String(maxDateObj.getDate()).padStart(2, '0');
            maxDate = `${maxYear}-${maxMonth}-${maxDay}`;
        }

        rentalFormContainer.innerHTML = `
            <div class="rental-form">
                <h2><i class="fas fa-calendar-check"></i> Rent Equipment</h2>
                <form id="rental-form" onsubmit="submitRental(event, ${listing.id})">
                    <div class="rental-form-group">
                        <label for="start_date">Start Date <span style="color: #c94843;">*</span></label>
                        <input type="date" id="start_date" name="start_date" required min="${today}" ${maxDate ? `max="${maxDate}"` : ''} onchange="checkDateConflict(${listing.id})">
                    </div>
                    <div class="rental-form-group">
                        <label for="days">Number of Days <span style="color: #c94843;">*</span></label>
                        <input type="number" id="days" name="days" min="1" required onchange="calculateTotal(${listing.price}, '${listing.pricing_type}', ${listing.transport_charge || 0}, '${listing.transport_included}'); checkDateConflict(${listing.id})">
                    </div>
                    <div id="conflict-warning" class="conflict-warning" style="display: none;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span id="conflict-message"></span>
                    </div>
                    <div class="rental-summary" id="rental-summary">
                        <div class="rental-summary-item">
                            <span>Price per ${listing.pricing_type}:</span>
                            <span>₹${listing.price.toLocaleString()}</span>
                        </div>
                        ${listing.transport_included === 'No' && listing.transport_charge ? `
                        <div class="rental-summary-item" id="transport-item" style="display: none;">
                            <span>Transport Charge:</span>
                            <span>₹${listing.transport_charge.toLocaleString()}</span>
                        </div>
                        ` : ''}
                        <div class="rental-summary-item" id="total-item">
                            <span>Total Amount:</span>
                            <span id="total-amount">₹0</span>
                        </div>
                    </div>
                    <button type="submit" class="btn-rent" id="submit-rental-btn">
                        <i class="fas fa-check"></i> Submit Rental Request
                    </button>
                </form>
            </div>
        `;

        // Close details modal and show rental modal
        document.getElementById('details-modal').classList.remove('show');
        rentalModal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    // Check for date conflicts in real-time
    window.checkDateConflict = async function (listingId) {
        const startDateInput = document.getElementById('start_date');
        const daysInput = document.getElementById('days');
        const conflictWarning = document.getElementById('conflict-warning');
        const conflictMessage = document.getElementById('conflict-message');
        const submitBtn = document.getElementById('submit-rental-btn');

        if (!startDateInput.value || !daysInput.value) {
            conflictWarning.style.display = 'none';
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        const startDate = startDateInput.value;
        const days = parseInt(daysInput.value);
        // Parse date without timezone conversion
        const parseDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };
        const start = parseDate(startDate);
        const end = new Date(start);
        end.setDate(end.getDate() + days);
        // Format end date as YYYY-MM-DD without timezone conversion
        const endYear = end.getFullYear();
        const endMonth = String(end.getMonth() + 1).padStart(2, '0');
        const endDay = String(end.getDate()).padStart(2, '0');
        const endDate = `${endYear}-${endMonth}-${endDay}`;

        try {
            // Fetch current availability
            const response = await fetch(`/api/listing/${listingId}/availability`);
            const data = await response.json();

            const pendingDates = new Set(data.pending_dates || []);
            const confirmedDates = new Set(data.confirmed_dates || []);

            // Check for conflicts
            let hasConflict = false;
            let conflictType = '';
            let conflictDate = '';

            // Generate all dates in the requested range
            const requestedDates = [];
            const currentDate = new Date(start);
            while (currentDate <= end) {
                // Format date as YYYY-MM-DD without timezone conversion
                const year = currentDate.getFullYear();
                const month = String(currentDate.getMonth() + 1).padStart(2, '0');
                const day = String(currentDate.getDate()).padStart(2, '0');
                const dateString = `${year}-${month}-${day}`;
                requestedDates.push(dateString);
                currentDate.setDate(currentDate.getDate() + 1);
            }

            // Check for confirmed conflicts
            for (const date of requestedDates) {
                if (confirmedDates.has(date)) {
                    hasConflict = true;
                    conflictType = 'confirmed';
                    conflictDate = date;
                    break;
                }
            }

            // Check for pending conflicts
            if (!hasConflict) {
                for (const date of requestedDates) {
                    if (pendingDates.has(date)) {
                        hasConflict = true;
                        conflictType = 'pending';
                        conflictDate = date;
                        break;
                    }
                }
            }

            if (hasConflict) {
                conflictWarning.style.display = 'flex';
                if (conflictType === 'confirmed') {
                    conflictMessage.textContent = `Selected dates conflict with a confirmed booking on ${new Date(conflictDate).toLocaleDateString()}. Please choose different dates.`;
                    conflictWarning.className = 'conflict-warning error';
                    if (submitBtn) submitBtn.disabled = true;
                } else {
                    conflictMessage.textContent = `Selected dates overlap with a pending request. You can still submit, but the owner will review all requests.`;
                    conflictWarning.className = 'conflict-warning warning';
                    if (submitBtn) submitBtn.disabled = false;
                }
            } else {
                conflictWarning.style.display = 'none';
                if (submitBtn) submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Error checking conflicts:', error);
            conflictWarning.style.display = 'none';
            if (submitBtn) submitBtn.disabled = false;
        }
    };

    // Calculate total
    window.calculateTotal = function (price, pricingType, transportCharge, transportIncluded) {
        const days = parseInt(document.getElementById('days').value) || 0;
        let total = 0;

        if (pricingType === 'Per day') {
            total = price * days;
        } else if (pricingType === 'Per hour') {
            total = price * days * 8; // Assuming 8 hours per day
        } else if (pricingType === 'Per acre') {
            total = price * days; // Assuming days = acres
        } else {
            total = price; // Per season
        }

        if (transportIncluded === 'No' && transportCharge) {
            const transportItem = document.getElementById('transport-item');
            if (transportItem) {
                transportItem.style.display = 'flex';
            }
            total += transportCharge;
        }

        const totalAmount = document.getElementById('total-amount');
        if (totalAmount) {
            totalAmount.textContent = `₹${total.toLocaleString()}`;
        }
    };

    // Submit rental
    window.submitRental = async function (event, listingId) {
        event.preventDefault();

        const formData = new FormData(event.target);
        formData.append('listing_id', listingId);
        formData.append('days', document.getElementById('days').value);

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

        try {
            const response = await fetch('/rent_equipment', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                alert('Rental request submitted successfully! The owner will review and approve your request.');
                document.getElementById('rental-modal').classList.remove('show');
                document.body.style.overflow = 'visible';
                // Reload listings to update calendar
                if (typeof loadListings === 'function') {
                    loadListings();
                }
            } else {
                const errorMessage = data.message || 'Failed to submit rental request';
                if (data.booked) {
                    alert('These dates are already booked. ' + errorMessage);
                } else {
                    alert('Error: ' + errorMessage);
                }
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        } catch (error) {
            console.error('Error submitting rental:', error);
            alert('An error occurred. Please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    };

    // Initialize event listeners
    function initEventListeners() {
        // Close modals
        document.getElementById('close-modal').addEventListener('click', function () {
            document.getElementById('details-modal').classList.remove('show');
            document.body.style.overflow = 'visible';
        });

        document.getElementById('close-rental-modal').addEventListener('click', function () {
            document.getElementById('rental-modal').classList.remove('show');
            document.body.style.overflow = 'visible';
        });

        // Close on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', function (e) {
                if (e.target === overlay) {
                    overlay.closest('.details-modal, .rental-modal').classList.remove('show');
                    document.body.style.overflow = 'visible';
                }
            });
        });

        const searchInput = document.getElementById('search-filter');
        const clearSearchBtn = document.getElementById('clear-search');
        const categorySelect = document.getElementById('category-filter');
        const locationInput = document.getElementById('location-filter');
        const priceMinInput = document.getElementById('price-min');
        const priceMaxInput = document.getElementById('price-max');
        const sortSelect = document.getElementById('sort-order');
        const applyBtn = document.getElementById('apply-filters');
        const resetBtn = document.getElementById('clear-filters');

        const debouncedFilter = debounce(applyFilters, 250);

        applyBtn.addEventListener('click', applyFilters);
        searchInput.addEventListener('input', debouncedFilter);
        locationInput.addEventListener('input', debouncedFilter);
        categorySelect.addEventListener('change', applyFilters);
        sortSelect.addEventListener('change', applyFilters);
        priceMinInput.addEventListener('input', debouncedFilter);
        priceMaxInput.addEventListener('input', debouncedFilter);

        clearSearchBtn.addEventListener('click', function () {
            if (searchInput.value.trim() === '') return;
            searchInput.value = '';
            applyFilters();
        });

        resetBtn.addEventListener('click', function () {
            resetFilters({
                searchInput,
                categorySelect,
                locationInput,
                priceMinInput,
                priceMaxInput,
                sortSelect
            });
        });

        locationInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilters();
            }
        });
    }

    // Apply filters
    function applyFilters() {
        const categoryFilter = document.getElementById('category-filter').value.toLowerCase();
        const locationFilter = document.getElementById('location-filter').value.trim().toLowerCase();
        const searchQuery = document.getElementById('search-filter').value.trim().toLowerCase();
        const priceMin = parseInt(document.getElementById('price-min').value, 10);
        const priceMax = parseInt(document.getElementById('price-max').value, 10);
        const sortOption = document.getElementById('sort-order').value;

        let filtered = [...allListings];

        if (categoryFilter) {
            filtered = filtered.filter(listing =>
                listing.category && listing.category.toLowerCase() === categoryFilter
            );
        }

        if (locationFilter) {
            filtered = filtered.filter(listing => {
                const locations = [
                    listing.state,
                    listing.district,
                    listing.village_city
                ].filter(Boolean).map(loc => loc.toLowerCase());
                return locations.some(loc => loc.includes(locationFilter));
            });
        }

        if (searchQuery) {
            filtered = filtered.filter(listing => {
                const searchableFields = [
                    listing.title,
                    listing.equipment_name,
                    listing.brand,
                    listing.description,
                    listing.category
                ];

                return searchableFields.filter(Boolean).some(field =>
                    field.toLowerCase().includes(searchQuery)
                );
            });
        }

        if (!isNaN(priceMin)) {
            filtered = filtered.filter(listing => listing.price >= priceMin);
        }

        if (!isNaN(priceMax)) {
            filtered = filtered.filter(listing => listing.price <= priceMax);
        }

        filtered = sortListings(filtered, sortOption);

        displayListings(filtered);
        toggleEmptyState(filtered.length === 0);
    }

    function sortListings(listings, sortOption) {
        const sorted = [...listings];

        switch (sortOption) {
            case 'price-asc':
                return sorted.sort((a, b) => a.price - b.price);
            case 'price-desc':
                return sorted.sort((a, b) => b.price - a.price);
            case 'newest':
                return sorted.sort((a, b) => getListingTimestamp(b) - getListingTimestamp(a));
            default:
                return sorted;
        }
    }

    function getListingTimestamp(listing) {
        const candidates = [listing.created_at, listing.updated_at, listing.available_from];
        for (const value of candidates) {
            const timestamp = value ? new Date(value).getTime() : NaN;
            if (!isNaN(timestamp)) {
                return timestamp;
            }
        }
        return 0;
    }

    function toggleEmptyState(showEmpty) {
        const emptyState = document.getElementById('empty-state');
        emptyState.style.display = showEmpty ? 'block' : 'none';
    }

    function resetFilters(elements) {
        elements.searchInput.value = '';
        elements.categorySelect.value = '';
        elements.locationInput.value = '';
        elements.priceMinInput.value = '';
        elements.priceMaxInput.value = '';
        elements.sortSelect.value = 'recommended';
        applyFilters();
    }

    function debounce(fn, delay = 250) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    }
});

// AI Condition Analysis
window.analyzeCondition = async function (imageUrl, listingId) {
    const container = document.getElementById(`ai-analysis-container-${listingId}`);
    if (!container) return;

    // Show loading state
    container.innerHTML = `
        <div class="ai-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Analyzing equipment condition...</span>
        </div>
    `;

    try {
        // Call backend API
        const response = await fetch(`/api/analyze-condition/${listingId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const result = await response.json();

        // Extract data
        const score = result.condition_score;
        const issues = result.issues_found || [];
        const summary = result.summary || 'Analysis completed';
        const recommendation = result.recommendation || 'Review equipment before renting';

        // Determine score color (0-10 scale)
        let scoreColor;
        let scoreLabel;
        if (score === null || score === undefined) {
            scoreColor = '#999';
            scoreLabel = 'N/A';
        } else if (score >= 9) {
            scoreColor = '#4CAF50'; // Green - Excellent
            scoreLabel = 'Excellent';
        } else if (score >= 7) {
            scoreColor = '#8BC34A'; // Light Green - Good
            scoreLabel = 'Good';
        } else if (score >= 5) {
            scoreColor = '#FFC107'; // Yellow - Moderate
            scoreLabel = 'Moderate';
        } else if (score >= 3) {
            scoreColor = '#FF9800'; // Orange - Poor
            scoreLabel = 'Poor';
        } else {
            scoreColor = '#F44336'; // Red - Very Bad
            scoreLabel = 'Very Poor';
        }

        // Calculate percentage for display (0-10 scale to 0-100%)
        const scorePercent = score !== null && score !== undefined ? (score / 10) * 100 : 0;

        // Render Result
        container.innerHTML = `
            <div class="ai-result" style="border-left: 4px solid ${scoreColor}; background: #f9f9f9; padding: 1rem; border-radius: 8px; margin-top: 10px;">
                <div style="display: flex; align-items: flex-start; gap: 15px; margin-bottom: 12px;">
                    <div style="position: relative; width: 70px; height: 70px; flex-shrink: 0;">
                        <svg viewBox="0 0 36 36" style="width: 100%; height: 100%; transform: rotate(-90deg);">
                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#eee" stroke-width="3" />
                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="${scoreColor}" stroke-width="3" stroke-dasharray="${scorePercent}, 100" />
                        </svg>
                        <span style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 16px; color: ${scoreColor};">${score !== null && score !== undefined ? score.toFixed(1) : 'N/A'}</span>
                    </div>
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 8px 0; color: #333; font-size: 16px;">
                            <i class="fas fa-robot" style="color: ${scoreColor};"></i> Condition Score: ${scoreLabel}
                        </h4>
                        ${issues.length > 0 ? `
                        <div style="margin-bottom: 8px;">
                            <strong style="font-size: 13px; color: #666;">Issues Found:</strong>
                            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 12px; color: #555;">
                                ${issues.slice(0, 5).map(issue => `<li>${escapeHtml(issue)}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                        <div style="margin-bottom: 6px;">
                            <strong style="font-size: 13px; color: #666;">Summary:</strong>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #555; line-height: 1.4;">${escapeHtml(summary)}</p>
                        </div>
                        <div>
                            <strong style="font-size: 13px; color: #666;">Suggestion:</strong>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #555; line-height: 1.4;">${escapeHtml(recommendation)}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('AI Analysis Error:', error);
        container.innerHTML = `
            <div class="ai-error" style="color: #d32f2f; padding: 10px; background: #ffebee; border-radius: 5px; margin-top: 10px;">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Analysis failed: ${error.message}</span>
                <div style="margin-top: 5px;">
                    <button style="border: none; background: transparent; color: #d32f2f; text-decoration: underline; cursor: pointer; font-size: 12px;" onclick="analyzeCondition('${imageUrl}', ${listingId})">Retry</button>
                </div>
            </div>
        `;
    }
};

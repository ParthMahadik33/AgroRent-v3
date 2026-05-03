// Multi-step Listing Form Functionality

document.addEventListener('DOMContentLoaded', function() {
    let currentStep = 1;
    const totalSteps = 6;
    const form = document.getElementById('listing-form');
    const steps = document.querySelectorAll('.form-step');
    const stepIndicators = document.querySelectorAll('.step-indicator');
    const progressFill = document.getElementById('progress-fill');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    const bodyDataset = document.body ? document.body.dataset : {};
    const editingData = parseEditingData(bodyDataset ? bodyDataset.listingEditing : null);

    // Initialize form
    updateStepDisplay();
    initImagePreviews();
    initTransportToggle();
    initDateValidation();

    // Previous button click
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (validateCurrentStep()) {
                goToPreviousStep();
            }
        });
    }

    // Next button click
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (validateCurrentStep()) {
                goToNextStep();
            }
        });
    }

    // Form submission
    if (form) {
        form.addEventListener('submit', function(e) {
            if (currentStep !== totalSteps) {
                e.preventDefault();
                goToStep(totalSteps);
            } else {
                if (!validateCurrentStep()) {
                    e.preventDefault();
                } else {
                    // Prevent default form submission
                    e.preventDefault();
                    // Submit form via AJAX
                    submitFormAjax();
                }
            }
        });
    }

    // Step indicator clicks
    stepIndicators.forEach((indicator, index) => {
        indicator.addEventListener('click', function() {
            const targetStep = index + 1;
            if (targetStep <= currentStep || isStepCompleted(targetStep - 1)) {
                goToStep(targetStep);
            }
        });
    });

    // Go to next step
    function goToNextStep() {
        if (currentStep < totalSteps) {
            currentStep++;
            updateStepDisplay();
        }
    }

    // Go to previous step
    function goToPreviousStep() {
        if (currentStep > 1) {
            currentStep--;
            updateStepDisplay();
        }
    }

    // Go to specific step
    function goToStep(step) {
        if (step >= 1 && step <= totalSteps) {
            currentStep = step;
            updateStepDisplay();
        }
    }

    // Update step display
    function updateStepDisplay() {
        // Hide all steps
        steps.forEach((step, index) => {
            if (index + 1 === currentStep) {
                step.classList.add('active');
            } else {
                step.classList.remove('active');
            }
        });

        // Update step indicators
        stepIndicators.forEach((indicator, index) => {
            const stepNum = index + 1;
            indicator.classList.remove('active', 'completed');
            
            if (stepNum === currentStep) {
                indicator.classList.add('active');
            } else if (stepNum < currentStep) {
                indicator.classList.add('completed');
            }
        });

        // Update progress bar
        const progress = (currentStep / totalSteps) * 100;
        if (progressFill) {
            progressFill.style.width = progress + '%';
        }

        // Update navigation buttons
        if (prevBtn) {
            prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none';
        }
        
        if (nextBtn) {
            nextBtn.style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
        }
        
        if (submitBtn) {
            submitBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
        }

        // Scroll to top of form
        const formContainer = document.querySelector('.listing-container');
        if (formContainer) {
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // Validate current step
    function validateCurrentStep() {
        const currentStepElement = document.getElementById(`step-${currentStep}`);
        if (!currentStepElement) return true;

        const requiredFields = currentStepElement.querySelectorAll('[required]');
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach(field => {
            // Skip hidden fields
            if (field.offsetParent === null) return;

            // Remove previous error styling
            field.classList.remove('error');
            const errorMsg = field.parentElement.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.remove();
            }

            // Validate field
            if (!field.value.trim()) {
                isValid = false;
                showFieldError(field, 'This field is required');
                if (!firstInvalidField) {
                    firstInvalidField = field;
                }
            } else {
                // Additional validations
                if (field.type === 'email' && field.value) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(field.value)) {
                        isValid = false;
                        showFieldError(field, 'Please enter a valid email address');
                        if (!firstInvalidField) {
                            firstInvalidField = field;
                        }
                    }
                }

                if (field.type === 'tel' && field.value) {
                    const phoneRegex = /^[\d\s\+\-\(\)]+$/;
                    if (!phoneRegex.test(field.value) || field.value.length < 10) {
                        isValid = false;
                        showFieldError(field, 'Please enter a valid phone number');
                        if (!firstInvalidField) {
                            firstInvalidField = field;
                        }
                    }
                }

                if (field.id === 'pincode' && field.value) {
                    const pincodeRegex = /^\d{6}$/;
                    if (!pincodeRegex.test(field.value)) {
                        isValid = false;
                        showFieldError(field, 'Pincode must be 6 digits');
                        if (!firstInvalidField) {
                            firstInvalidField = field;
                        }
                    }
                }

                if (field.type === 'date' && field.value) {
                    const selectedDate = new Date(field.value);
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    
                    if (field.id === 'available_from' && selectedDate < today) {
                        isValid = false;
                        showFieldError(field, 'Available from date cannot be in the past');
                        if (!firstInvalidField) {
                            firstInvalidField = field;
                        }
                    }

                    if (field.id === 'available_till' && field.value) {
                        const fromDate = document.getElementById('available_from').value;
                        if (fromDate && selectedDate < new Date(fromDate)) {
                            isValid = false;
                            showFieldError(field, 'Available till date must be after available from date');
                            if (!firstInvalidField) {
                                firstInvalidField = field;
                            }
                        }
                    }
                }
            }
        });

        // Special validation for step 6 (images)
        if (currentStep === 6) {
            const mainImage = document.getElementById('main_image');
            if (mainImage && !mainImage.files.length) {
                isValid = false;
                showFieldError(mainImage, 'Main image is required');
                if (!firstInvalidField) {
                    firstInvalidField = mainImage;
                }
            }
        }

        // Focus on first invalid field
        if (firstInvalidField) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        return isValid;
    }

    // Show field error
    function showFieldError(field, message) {
        field.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        field.parentElement.appendChild(errorDiv);
    }

    // Check if step is completed
    function isStepCompleted(step) {
        const stepElement = document.getElementById(`step-${step + 1}`);
        if (!stepElement) return false;

        const requiredFields = stepElement.querySelectorAll('[required]');
        for (let field of requiredFields) {
            if (field.offsetParent === null) continue; // Skip hidden fields
            if (!field.value.trim()) {
                return false;
            }
        }
        return true;
    }

    // Initialize image previews
    function initImagePreviews() {
        const mainImageInput = document.getElementById('main_image');
        const additionalImagesInput = document.getElementById('additional_images');

        if (mainImageInput) {
            mainImageInput.addEventListener('change', function(e) {
                handleImagePreview(e.target.files[0], 'main-preview', true);
            });
        }

        if (additionalImagesInput) {
            additionalImagesInput.addEventListener('change', function(e) {
                handleMultipleImagePreview(e.target.files, 'additional-preview');
            });
        }
    }

    // Handle single image preview
    function handleImagePreview(file, previewId, isMain = false) {
        const preview = document.getElementById(previewId);
        if (!preview || !file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        // Validate file size (5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Image size must be less than 5MB');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            if (isMain) {
                preview.innerHTML = `
                    <div class="preview-image-main">
                        <img src="${e.target.result}" alt="Main image preview">
                        <button type="button" class="remove-image" onclick="removeMainImage()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
            } else {
                preview.innerHTML = `
                    <div class="preview-image">
                        <img src="${e.target.result}" alt="Image preview">
                        <button type="button" class="remove-image" onclick="removeImage(this)">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
            }
        };
        reader.readAsDataURL(file);
    }

    // Handle multiple image previews
    function handleMultipleImagePreview(files, previewId) {
        const preview = document.getElementById(previewId);
        if (!preview) return;

        Array.from(files).forEach((file, index) => {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                alert(`${file.name} is not an image file`);
                return;
            }

            // Validate file size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                alert(`${file.name} is too large. Maximum size is 5MB`);
                return;
            }

            const reader = new FileReader();
            reader.onload = function(e) {
                const imageDiv = document.createElement('div');
                imageDiv.className = 'preview-image-item';
                imageDiv.innerHTML = `
                    <img src="${e.target.result}" alt="Preview ${index + 1}">
                    <button type="button" class="remove-image" onclick="removeImageItem(this)">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                preview.appendChild(imageDiv);
            };
            reader.readAsDataURL(file);
        });
    }

    // Remove main image
    window.removeMainImage = function() {
        const mainImageInput = document.getElementById('main_image');
        const preview = document.getElementById('main-preview');
        if (mainImageInput) mainImageInput.value = '';
        if (preview) preview.innerHTML = '';
    };

    // Remove image item
    window.removeImageItem = function(button) {
        button.parentElement.remove();
        // Note: This doesn't remove from FileList, but prevents submission
        // For full functionality, you'd need to use DataTransfer API
    };

    // Initialize transport toggle
    function initTransportToggle() {
        const transportSelect = document.getElementById('transport_included');
        const transportChargeGroup = document.getElementById('transport-charge-group');

        if (transportSelect && transportChargeGroup) {
            transportSelect.addEventListener('change', function() {
                if (this.value === 'Yes') {
                    transportChargeGroup.style.display = 'block';
                } else {
                    transportChargeGroup.style.display = 'none';
                    const transportCharge = document.getElementById('transport_charge');
                    if (transportCharge) transportCharge.value = '';
                }
            });
        }
    }

    // Initialize date validation
    function initDateValidation() {
        const availableFrom = document.getElementById('available_from');
        const availableTill = document.getElementById('available_till');

        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        if (availableFrom) {
            availableFrom.setAttribute('min', today);
            availableFrom.addEventListener('change', function() {
                if (availableTill && this.value) {
                    availableTill.setAttribute('min', this.value);
                }
            });
        }
    }

    // Real-time validation on input
    document.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('blur', function() {
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.classList.add('error');
            } else {
                this.classList.remove('error');
                const errorMsg = this.parentElement.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });

        field.addEventListener('input', function() {
            if (this.classList.contains('error') && this.value.trim()) {
                this.classList.remove('error');
                const errorMsg = this.parentElement.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });
    });

    // Auto-save form data to localStorage (optional feature)
    function autoSaveFormData() {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (key !== 'main_image' && key !== 'additional_images') {
                data[key] = value;
            }
        }
        localStorage.setItem('listing_form_data', JSON.stringify(data));
    }

    // Load saved form data (optional feature)
    function loadSavedFormData() {
        const savedData = localStorage.getItem('listing_form_data');
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = document.querySelector(`[name="${key}"]`);
                    if (field && field.type !== 'file') {
                        field.value = data[key];
                    }
                });
            } catch (e) {
                console.error('Error loading saved form data:', e);
            }
        }
    }

    // Auto-save on input (debounced)
    let saveTimeout;
    if (form) {
        form.addEventListener('input', function() {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(autoSaveFormData, 1000);
        });
    }

    // Load saved data on page load
    loadSavedFormData();

    // Pre-fill form if editing
    if (editingData) {
        prefillEditForm(editingData);
    }

    // Submit form via AJAX
    function submitFormAjax() {
        const formData = new FormData(form);
        const submitBtn = document.getElementById('submit-btn');
        
        // Disable submit button and show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        }

        // Submit form via fetch API
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success modal
                showSuccessModal();
                // Clear saved form data
                localStorage.removeItem('listing_form_data');
            } else {
                // Handle error
                alert('Error: ' + (data.message || 'Failed to submit listing'));
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-check"></i> Submit Listing';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while submitting the form. Please try again.');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check"></i> Submit Listing';
            }
        });
    }

    // Show success modal
    function showSuccessModal() {
        const modal = document.getElementById('success-modal');
        if (modal) {
            modal.classList.add('show');
            // Prevent body scrolling when modal is open
            document.body.style.overflow = 'hidden';
        }
    }

    // Close modal on overlay click (optional)
    const modalOverlay = document.querySelector('.modal-overlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function(e) {
            // Don't close on overlay click - user must click the button
            // This ensures they see the dashboard link
        });
    }

    // Pre-fill form for editing
    function prefillEditForm(data) {
        // Step 1: Owner & Contact
        if (data.owner_name) document.getElementById('owner_name').value = data.owner_name;
        if (data.phone) document.getElementById('phone').value = data.phone;
        if (data.email) document.getElementById('email').value = data.email;
        if (data.contact_method) document.getElementById('contact_method').value = data.contact_method;

        // Step 2: Equipment Details
        if (data.category) document.getElementById('category').value = data.category;
        if (data.equipment_name) document.getElementById('equipment_name').value = data.equipment_name;
        if (data.brand) document.getElementById('brand').value = data.brand;
        if (data.year) document.getElementById('year').value = data.year;
        if (data.condition) document.getElementById('condition').value = data.condition;
        if (data.power_spec) document.getElementById('power_spec').value = data.power_spec;

        // Step 3: Location
        if (data.state) document.getElementById('state').value = data.state;
        if (data.district) document.getElementById('district').value = data.district;
        if (data.village_city) document.getElementById('village_city').value = data.village_city;
        if (data.pincode) document.getElementById('pincode').value = data.pincode;
        if (data.landmark) document.getElementById('landmark').value = data.landmark;
        if (data.service_radius) document.getElementById('service_radius').value = data.service_radius;

        // Step 4: Pricing & Availability
        if (data.pricing_type) document.getElementById('pricing_type').value = data.pricing_type;
        if (data.price) document.getElementById('price').value = data.price;
        if (data.min_duration) document.getElementById('min_duration').value = data.min_duration;
        if (data.available_from) document.getElementById('available_from').value = data.available_from;
        if (data.available_till) document.getElementById('available_till').value = data.available_till;
        if (data.transport_included) {
            document.getElementById('transport_included').value = data.transport_included;
            // Trigger transport toggle
            const transportSelect = document.getElementById('transport_included');
            if (transportSelect) {
                transportSelect.dispatchEvent(new Event('change'));
            }
        }
        if (data.transport_charge) document.getElementById('transport_charge').value = data.transport_charge;

        // Step 5: Rules & Description
        if (data.title) document.getElementById('title').value = data.title;
        if (data.description) document.getElementById('description').value = data.description;
        if (data.rules) document.getElementById('rules').value = data.rules;

        // Step 6: Images (show existing images if any)
        if (data.main_image) {
            const mainPreview = document.getElementById('main-preview');
            if (mainPreview) {
                mainPreview.innerHTML = `
                    <div class="preview-image-main">
                        <img src="/static/${data.main_image}" alt="Current main image">
                        <p style="margin-top: 0.5rem; font-size: 0.85rem; color: #7a8c6a;">Current image (upload new to replace)</p>
                    </div>
                `;
            }
        }

        if (data.additional_images) {
            const additionalPreview = document.getElementById('additional-preview');
            if (additionalPreview) {
                const images = data.additional_images.split(',');
                additionalPreview.innerHTML = images.map(img => `
                    <div class="preview-image-item">
                        <img src="/static/${img.trim()}" alt="Current image">
                        <p style="margin-top: 0.5rem; font-size: 0.85rem; color: #7a8c6a;">Current image</p>
                    </div>
                `).join('');
            }
        }

        // Mark all filled fields as having value for floating labels
        document.querySelectorAll('.form-input-modern').forEach(input => {
            if (input.value) {
                input.classList.add('has-value');
            }
        });
    }

    function parseEditingData(rawValue) {
        if (!rawValue || rawValue === 'null') {
            return null;
        }
        try {
            return JSON.parse(rawValue);
        } catch (error) {
            console.error('Failed to parse editing data:', error);
            return null;
        }
    }
});


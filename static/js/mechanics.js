window.mechanicDashboard = window.mechanicDashboard || {};

document.addEventListener('DOMContentLoaded', () => {
    const detailsModal = document.getElementById('detailsModal');
    const requestModal = document.getElementById('requestModal');
    const requestForm = document.getElementById('requestForm');
    const requestFeedback = document.getElementById('requestFeedback');

    const openModal = (modal) => modal && modal.classList.add('active');
    const closeModal = (modal) => modal && modal.classList.remove('active');
    const detailLabels = detailsModal ? detailsModal.dataset : {};
    const requestsList = document.querySelector('.requests-list');

    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.closest('.modal')));
    });

    [detailsModal, requestModal].forEach(modal => {
        if (!modal) return;
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });

    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!detailsModal) return;
            const nameEl = document.getElementById('detailsName');
            const specializationEl = document.getElementById('detailsSpecialization');
            const experienceEl = document.getElementById('detailsExperience');
            const chargeEl = document.getElementById('detailsCharge');
            const locationsEl = document.getElementById('detailsLocations');
            const descriptionEl = document.getElementById('detailsDescription');

            const specializationLabel = detailLabels.labelSpecialization || 'Specialization';
            const experienceLabel = detailLabels.labelExperience || 'Experience';
            const chargeLabel = detailLabels.labelCharge || 'Base visit';
            const locationLabel = detailLabels.labelLocations || 'Service areas';

            nameEl.textContent = btn.dataset.name;
            specializationEl.textContent = `${specializationLabel}: ${btn.dataset.specialization}`;
            const experienceText = btn.dataset.experienceText || detailLabels.labelExperienceMissing || '';
            experienceEl.textContent = `${experienceLabel}: ${experienceText}`;
            chargeEl.textContent = btn.dataset.chargeDisplay || `${chargeLabel}: ${btn.dataset.charge || ''}`;
            locationsEl.textContent = btn.dataset.locationDisplay || `${locationLabel}: ${btn.dataset.location || ''}`;
            descriptionEl.textContent = btn.dataset.description || '';
            openModal(detailsModal);
        });
    });

    const mechanicNameLabel = document.getElementById('requestMechanicName');
    document.querySelectorAll('.request-service-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!requestForm) return;
            requestForm.reset();
            if (mechanicNameLabel) {
                const template = mechanicNameLabel.dataset.labelTemplate || '{name}';
                mechanicNameLabel.textContent = template.replace('__NAME__', btn.dataset.mechanicName);
            }
            document.getElementById('requestMechanicId').value = btn.dataset.mechanicId;
            if (requestFeedback) requestFeedback.textContent = '';
            openModal(requestModal);
        });
    });

    if (requestForm) {
        requestForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (requestFeedback) {
                requestFeedback.textContent = requestForm.dataset.sendingText || 'Sending request...';
                requestFeedback.style.color = '#1f2933';
            }
            const mechanicId = document.getElementById('requestMechanicId').value;
            const formData = new FormData(requestForm);
            try {
                const response = await fetch(`/mechanics/${mechanicId}/request`, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (requestFeedback) {
                    requestFeedback.textContent = data.message;
                    requestFeedback.style.color = data.success ? '#2e7d32' : '#b91c1c';
                }
                if (data.success) {
                    requestForm.reset();
                    setTimeout(() => closeModal(requestModal), 1500);
                }
            } catch (error) {
                if (requestFeedback) {
                    requestFeedback.textContent = requestForm.dataset.errorText || 'Unable to send request at the moment.';
                    requestFeedback.style.color = '#b91c1c';
                }
            }
        });
    }

    const availabilityToggle = document.getElementById('availabilityToggle');
    const availabilityStatus = document.getElementById('availabilityStatus');
    if (availabilityToggle && window.mechanicDashboard?.hasProfile) {
        availabilityToggle.addEventListener('change', async () => {
            const desiredState = availabilityToggle.checked;
            const visibleLabel = availabilityStatus?.dataset.visibleLabel || 'Currently visible on listing';
            const hiddenLabel = availabilityStatus?.dataset.hiddenLabel || 'Hidden from listing';
            const updatingLabel = availabilityStatus?.dataset.updatingLabel || 'Updating...';
            const errorLabel = availabilityStatus?.dataset.errorLabel || 'Update failed, please retry.';
            availabilityStatus.textContent = updatingLabel;
            try {
                const res = await fetch(window.mechanicDashboard.availabilityEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_available: desiredState })
                });
                const data = await res.json();
                if (!data.success) {
                    throw new Error(data.message || 'Failed');
                }
                availabilityStatus.textContent = data.is_available ? visibleLabel : hiddenLabel;
            } catch (error) {
                availabilityToggle.checked = !desiredState;
                availabilityStatus.textContent = errorLabel;
            }
        });
    }

    document.querySelectorAll('.request-status-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const requestCard = btn.closest('.request-card');
            if (!requestCard || !window.mechanicDashboard?.requestEndpointTemplate) return;
            const requestId = requestCard.dataset.requestId;
            const targetStatus = btn.dataset.status;
            const statusPill = requestCard.querySelector('.status-pill');
            const endpoint = window.mechanicDashboard.requestEndpointTemplate.replace('/0/', `/${requestId}/`);

            btn.textContent = availabilityStatus?.dataset.updatingLabel || 'Updating...';
            btn.disabled = true;
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: targetStatus })
                });
                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.message || 'Failed to update');
                }
                const localizedStatus = window.mechanicDashboard?.statusLabels?.[data.status] || data.status;
                statusPill.textContent = localizedStatus;
                statusPill.className = `status-pill ${data.status}`;
                requestCard.querySelectorAll('.request-status-btn').forEach(actionBtn => {
                    if (data.status === 'Completed') {
                        actionBtn.remove();
                    } else if (actionBtn.dataset.status === data.status) {
                        actionBtn.remove();
                    } else {
                        const label = actionBtn.dataset.status === 'Accepted'
                            ? requestsList?.dataset.acceptLabel
                            : requestsList?.dataset.completeLabel;
                        actionBtn.textContent = label || actionBtn.textContent;
                        actionBtn.disabled = false;
                    }
                });
            } catch (error) {
                const retryTemplate = requestsList?.dataset.retryLabel || 'Retry {status}';
                const targetLabel = window.mechanicDashboard?.statusLabels?.[targetStatus] || targetStatus;
                btn.textContent = retryTemplate.replace('__STATUS__', targetLabel).replace('{status}', targetLabel);
                btn.disabled = false;
            }
        });
    });
});


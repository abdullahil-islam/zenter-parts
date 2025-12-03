/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.CustomerRegistrationForm = publicWidget.Widget.extend({
    selector: '.o-vendor-form',
    events: {
        'change #country_select': '_onCountryChange',
        'change #state_select': '_onStateChange',
        'blur .email-field': '_onEmailBlur',
        'input .email-field': '_onEmailInput',
        'submit form': '_onFormSubmit',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this.countrySelect = this.el.querySelector('#country_select');
        this.stateSelect = this.el.querySelector('#state_select');

        // Store all state options for filtering
        this.allStateOptions = Array.from(this.stateSelect.options).slice(1); // Skip "-- Select --"

        // Email regex pattern (RFC 5322 simplified)
        this.emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        return this._super.apply(this, arguments);
    },

    /**
     * Filter states based on selected country
     * @private
     * @param {String|Number} countryId - The country ID to filter by
     */
    _filterStatesByCountry: function(countryId) {
        // Clear current options except the first one
        this.stateSelect.innerHTML = '<option value="">-- Select --</option>';

        if (!countryId) {
            // If no country selected, show all states
            this.allStateOptions.forEach(option => {
                this.stateSelect.appendChild(option.cloneNode(true));
            });
        } else {
            // Check if the selected country has state or not
            const hasState = this.allStateOptions.filter(state => state.getAttribute('data-country-id') == countryId).length > 0;
            const requiredIcon = this.stateSelect.closest('.col-md-6').querySelector('.text-danger');

            this.stateSelect.required = hasState;

            if ((hasState && requiredIcon.classList.contains('d-none')) || (!hasState && !requiredIcon.classList.contains('d-none'))) {
                requiredIcon.classList.toggle('d-none');
            }
            // Filter and add only states from selected country
            this.allStateOptions.forEach(option => {
                if (option.getAttribute('data-country-id') == countryId) {
                    this.stateSelect.appendChild(option.cloneNode(true));
                }
            });
        }
    },

    /**
     * Handle country selection change
     * @private
     * @param {Event} ev
     */
    _onCountryChange: function(ev) {
        const selectedCountry = ev.currentTarget.value;

        // Reset state selection
        this.stateSelect.value = '';

        // Filter states
        this._filterStatesByCountry(selectedCountry);
    },

    /**
     * Handle state selection change
     * @private
     * @param {Event} ev
     */
    _onStateChange: function(ev) {
        const selectedStateValue = ev.currentTarget.value;
        const selectedStateOption = ev.currentTarget.options[ev.currentTarget.selectedIndex];

        if (ev.currentTarget.value) {
            // Get the country ID from the selected state
            const stateCountryId = selectedStateOption.getAttribute('data-country-id');

            // If country is different or not selected, update it
            if (this.countrySelect.value != stateCountryId) {
                this.countrySelect.value = stateCountryId;
                // Filter states for the newly selected country
                this._filterStatesByCountry(stateCountryId);
                // Re-select the state (since filtering recreates options)
                setTimeout(() => {
                    this.stateSelect.value = selectedStateValue;
                }, 0);
            }
        }
    },

    /**
     * Validate email format
     * @private
     * @param {String} email - Email to validate
     * @returns {Boolean}
     */
    _isValidEmail: function(email) {
        return this.emailPattern.test(email);
    },

    /**
     * Show validation error message
     * @private
     * @param {HTMLElement} input - Input element
     * @param {String} message - Error message
     */
    _showEmailError: function(input, message) {
        // Remove any existing error
        this._clearEmailError(input);

        // Add invalid class
        input.classList.add('is-invalid');

        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;
        errorDiv.setAttribute('data-email-error', 'true');

        // Insert after input
        input.parentNode.appendChild(errorDiv);
    },

    /**
     * Clear validation error message
     * @private
     * @param {HTMLElement} input - Input element
     */
    _clearEmailError: function(input) {
        input.classList.remove('is-invalid');
        input.classList.remove('is-valid');

        // Remove error message if exists
        const existingError = input.parentNode.querySelector('[data-email-error="true"]');
        if (existingError) {
            existingError.remove();
        }
    },

    /**
     * Show validation success
     * @private
     * @param {HTMLElement} input - Input element
     */
    _showEmailSuccess: function(input) {
        this._clearEmailError(input);
        input.classList.add('is-valid');
    },

    /**
     * Handle email field blur event
     * @private
     * @param {Event} ev
     */
    _onEmailBlur: function(ev) {
        const input = ev.currentTarget;
        const email = input.value.trim();

        // Only validate if field has value
        if (email) {
            if (!this._isValidEmail(email)) {
                this._showEmailError(input, 'Please enter a valid email address (e.g., example@domain.com)');
            } else {
                this._showEmailSuccess(input);
            }
        } else if (input.hasAttribute('required')) {
            this._showEmailError(input, 'This field is required');
        } else {
            this._clearEmailError(input);
        }
    },

    /**
     * Handle email field input event (clear error on typing)
     * @private
     * @param {Event} ev
     */
    _onEmailInput: function(ev) {
        const input = ev.currentTarget;
        const email = input.value.trim();

        // Clear error if user is typing and email becomes valid
        if (email && this._isValidEmail(email)) {
            this._showEmailSuccess(input);
        } else if (input.classList.contains('is-invalid') || input.classList.contains('is-valid')) {
            // Keep showing real-time validation if already validated
            if (email && !this._isValidEmail(email)) {
                this._showEmailError(input, 'Please enter a valid email address (e.g., example@domain.com)');
            } else if (!email && input.hasAttribute('required')) {
                this._showEmailError(input, 'This field is required');
            }
        }
    },

    /**
     * Validate all email fields before form submission
     * @private
     * @param {Event} ev
     */
    _onFormSubmit: function(ev) {
        const emailFields = this.el.querySelectorAll('.email-field');
        let isValid = true;

        emailFields.forEach(input => {
            const email = input.value.trim();

            if (input.hasAttribute('required') && !email) {
                this._showEmailError(input, 'This field is required');
                isValid = false;
            } else if (email && !this._isValidEmail(email)) {
                this._showEmailError(input, 'Please enter a valid email address (e.g., example@domain.com)');
                isValid = false;
            }
        });

        if (!isValid) {
            ev.preventDefault();
            // Scroll to first error
            const firstError = this.el.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    },
});

export default publicWidget.registry.CustomerRegistrationForm;

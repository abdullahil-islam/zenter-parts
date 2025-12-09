/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from '@web/core/network/rpc';

publicWidget.registry.CustomerRegistrationForm = publicWidget.Widget.extend({
    selector: '.o-vendor-form',
    events: {
        'change #country_select': '_onCountryChange',
        'change #state_select': '_onStateChange',
        'blur .email-field': '_onEmailBlur',
        'input .email-field': '_onEmailInput',
        'blur input[name="company_reg_no"]': '_onVatBlur',
        'input input[name="company_reg_no"]': '_onVatInput',
        'change select[name="country"]': '_onCompCountryChange',
        'submit form': '_onFormSubmit',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this.countrySelect = this.el.querySelector('#country_select');
        this.stateSelect = this.el.querySelector('#state_select');
        this.vatField = this.el.querySelector('input[name="company_reg_no"]');
        this.compCountrySelect = this.el.querySelector('select[name="country"]');

        // Store all state options for filtering
        this.allStateOptions = Array.from(this.stateSelect.options).slice(1);

        // Email regex pattern (RFC 5322 simplified)
        this.emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        // VAT validation state
        this.vatValidationPending = false;
        this.vatValidationTimeout = null;

        return this._super.apply(this, arguments);
    },

    // ==================== VAT VALIDATION METHODS ====================

    /**
     * Validate VAT via server-side RPC call
     * @private
     * @param {String} vat - VAT number to validate
     * @param {String|Number} countryId - Country ID for validation
     * @returns {Promise}
     */
    async _validateVatServer(vat, countryId) {
        try {
            const result = await rpc('/customer/validate_vat', {
                vat: vat,
                country_id: countryId || false,
            });
            return result;
        } catch (error) {
            console.error('VAT validation error:', error);
            // On error, allow form submission (fail open) but warn user
            return { valid: true, message: '', error: true };
        }
    },

    /**
     * Show VAT validation error message
     * @private
     * @param {HTMLElement} input - Input element
     * @param {String} message - Error message
     */
    _showVatError: function(input, message) {
        this._clearVatValidation(input);
        input.classList.add('is-invalid');

        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;
        errorDiv.setAttribute('data-vat-error', 'true');

        input.parentNode.appendChild(errorDiv);
    },

    /**
     * Clear VAT validation state
     * @private
     * @param {HTMLElement} input - Input element
     */
    _clearVatValidation: function(input) {
        input.classList.remove('is-invalid');
        input.classList.remove('is-valid');

        const existingError = input.parentNode.querySelector('[data-vat-error="true"]');
        if (existingError) {
            existingError.remove();
        }

        // Remove loading indicator if exists
        const loadingIndicator = input.parentNode.querySelector('.vat-loading');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    },

    /**
     * Show VAT validation success
     * @private
     * @param {HTMLElement} input - Input element
     */
    _showVatSuccess: function(input) {
        this._clearVatValidation(input);
        input.classList.add('is-valid');
    },

    /**
     * Show loading indicator during VAT validation
     * @private
     * @param {HTMLElement} input - Input element
     */
    _showVatLoading: function(input) {
        this._clearVatValidation(input);
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'vat-loading text-muted small mt-1';
        loadingDiv.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>Validating VAT...';
        
        input.parentNode.appendChild(loadingDiv);
    },

    /**
     * Handle VAT field blur event
     * @private
     * @param {Event} ev
     */
    async _onVatBlur(ev) {
        const input = ev.currentTarget;
        const vat = input.value.trim();
        const countryId = this.compCountrySelect ? this.compCountrySelect.value : '';

        if (!vat) {
            if (input.hasAttribute('required')) {
                this._showVatError(input, 'This field is required');
            } else {
                this._clearVatValidation(input);
            }
            return;
        }

        // Skip validation for single character (as per Odoo's logic)
        if (vat.length <= 1) {
            this._clearVatValidation(input);
            return;
        }

        // Show loading state
        this._showVatLoading(input);
        this.vatValidationPending = true;

        // Validate via server
        const result = await this._validateVatServer(vat, countryId);
        this.vatValidationPending = false;

        if (result.valid) {
            this._showVatSuccess(input);
        } else {
            this._showVatError(input, result.message || 'Invalid VAT number');
        }
    },

    /**
     * Handle VAT field input event (debounced validation)
     * @private
     * @param {Event} ev
     */
    _onVatInput: function(ev) {
        const input = ev.currentTarget;
        
        // Clear any pending validation
        if (this.vatValidationTimeout) {
            clearTimeout(this.vatValidationTimeout);
        }

        // If field was already validated and user is typing, clear validation state
        if (input.classList.contains('is-invalid') || input.classList.contains('is-valid')) {
            this._clearVatValidation(input);
        }

        // Debounce: validate after user stops typing for 800ms
        const vat = input.value.trim();
        if (vat && vat.length > 1) {
            this.vatValidationTimeout = setTimeout(() => {
                this._onVatBlur({ currentTarget: input });
            }, 800);
        }
    },

    /**
     * Re-validate VAT when company country changes
     * @private
     * @param {Event} ev
     */
    _onCompCountryChange: function(ev) {
        const vatValue = this.vatField ? this.vatField.value.trim() : '';
        
        // If VAT has a value, re-validate with new country
        if (vatValue && vatValue.length > 1) {
            // Clear current validation
            this._clearVatValidation(this.vatField);
            
            // Trigger re-validation after a short delay
            setTimeout(() => {
                this._onVatBlur({ currentTarget: this.vatField });
            }, 300);
        }
    },

    // ==================== STATE/COUNTRY VALIDATIONS ====================

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

	// ==================== EMAIL VALIDATION METHODS ====================
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

    // ==================== FORM SUBMISSION ====================

    /**
     * Validate all email fields before form submission
     * @private
     * @param {Event} ev
     */
    async _onFormSubmit(ev) {
        let isValid = true;

        // Validate email fields
        const emailFields = this.el.querySelectorAll('.email-field');
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

        // Validate VAT field
        if (this.vatField) {
            const vat = this.vatField.value.trim();
            const countryId = this.compCountrySelect ? this.compCountrySelect.value : '';

            if (this.vatField.hasAttribute('required') && !vat) {
                this._showVatError(this.vatField, 'This field is required');
                isValid = false;
            } else if (vat && vat.length > 1) {
                // Prevent form submission while validating
                ev.preventDefault();
                
                this._showVatLoading(this.vatField);
                const result = await this._validateVatServer(vat, countryId);

                if (!result.valid) {
                    this._showVatError(this.vatField, result.message || 'Invalid VAT number');
                    isValid = false;
                } else {
                    this._showVatSuccess(this.vatField);
                }

                // If all validations pass, submit the form programmatically
                if (isValid) {
                    // Remove the event listener temporarily to avoid infinite loop
                    const form = this.el.querySelector('form');
                    form.submit();
                    return;
                }
            }
        }

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

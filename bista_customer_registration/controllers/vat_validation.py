# controllers/main.py

from odoo import http
from odoo.http import request


class CustomerRegistrationController(http.Controller):

    @http.route('/customer/validate_vat', type='json', auth='public', website=True)
    def validate_vat(self, vat, country_id=False):
        """
        Validate VAT number using Odoo's base_vat validation.

        :param vat: VAT number string
        :param country_id: Optional country ID for country-specific validation
        :return: dict with 'valid' boolean and 'message' string
        """
        if not vat or len(vat) <= 1:
            # Skip validation for empty or single character VAT (as per Odoo's logic)
            return {'valid': True, 'message': ''}

        Partner = request.env['res.partner'].sudo()

        # Get country record if provided
        country = False
        if country_id:
            country = request.env['res.country'].sudo().browse(int(country_id))
            if not country.exists():
                country = False

        # Run the actual VAT test
        is_valid = Partner._run_vat_test(vat, country, partner_is_company=True)

        if is_valid is False:
            # Build error message
            country_code = country.code.lower() if country else None
            error_msg = self._build_vat_error_message(vat, country_code)
            error_msg = Partner._build_vat_error_message(country_code, vat, 'False')
            return {'valid': False, 'message': error_msg}

        return {'valid': True, 'message': ''}

    def _build_vat_error_message(self, vat, country_code):
        """Build a user-friendly VAT error message."""
        if country_code:
            return f"The VAT number '{vat}' does not appear to be valid for country '{country_code.upper()}'. Please verify the number."
        return f"The VAT number '{vat}' does not appear to be valid. Please verify the number or select a country for country-specific validation."

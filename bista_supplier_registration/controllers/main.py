import base64
from odoo import http
from odoo.http import request

class VendorRegistrationController(http.Controller):

    @http.route("/vendor/apply", type="http", auth="public", website=True, sitemap=False)
    def vendor_apply(self, **kwargs):
        state_ids = request.env['res.country.state'].sudo().search([])
        country_ids = request.env['res.country'].sudo().search([])
        currency_ids = request.env['res.currency'].sudo().search([])
        payment_term_ids = request.env['account.payment.term'].sudo().search([])
        qcontext = {
            "business_types": [
                ("manufacturer", "Manufacturer"),
                ("distributor", "Distributor"),
                ("service", "Service"),
                ("other", "Other"),
            ],
            'state_ids': state_ids,
            'country_ids': country_ids,
            'currency_ids': currency_ids,
            'payment_term_ids': payment_term_ids,
        }
        return request.render("bista_supplier_registration.vendor_apply", qcontext)

    @http.route("/vendor/submit", type="http", auth="public", methods=["POST"], csrf=True, website=True)
    def vendor_submit(self, **post):
        files = request.httprequest.files

        # Helper to read file -> b64
        def _bin(name):
            f = files.get(name)
            return base64.b64encode(f.read()) if f and getattr(f, "filename", "") else False

        # Helper to get only the file name
        def _filename(name):
            f = files.get(name)
            return f.filename if f and getattr(f, "filename", "") else False

        # 1) Create application record
        vals = {
            # Section 1
            "legal_name": post.get("legal_name"),
            "contact_name": post.get('primary_contact_finance', '') or post.get('primary_contact_ops', ''),
            "trading_name": post.get("trading_name"),
            "vat": post.get("company_reg_no"),
            "business_type": post.get("business_type") or False,
            "website": post.get("website_url"),
            # Section 2
            "street": post.get("street"),
            "city": post.get("city"),
            "state_id": post.get("state"),
            "zip": post.get("zip"),
            "country_id": post.get("country"),

            "finance_name": post.get("finance_name"),
            "finance_phone": post.get("finance_phone"),
            "finance_email": post.get("finance_email"),
            "finance_position": post.get("finance_position"),

            "operational_name": post.get("operational_name"),
            "operational_phone": post.get("operational_phone"),
            "operational_email": post.get("operational_email"),
            "operational_position": post.get("operational_position"),

            "email_from": post.get("applicant_email"),
            "phone": post.get("applicant_phone"),
            # Section 3
            "bank_name": post.get("bank_name"),
            "bic": post.get("swift_bic"),
            "acc_number": post.get("iban_account"),
            "acc_holder_name": post.get("account_name"),
            "currency_id": post.get("account_currency"),
            "bank_country": post.get("bank_country"),
            "standard_payment_term": post.get("payment_term"),
            "supplier_invoice_currency_id": post.get("supplier_invoice_currency"),
            # State
            # "state": "submitted",
            # Section 4 (binaries)
            "incorporation_certificate": _bin("doc_certificate_incorp"),
            "incorporation_certificate_filename": _filename("doc_certificate_incorp"),
            "bank_proof": _bin("doc_bank_proof"),
            "bank_proof_filename": _filename("doc_bank_proof"),
            "master_agreement": _bin("doc_master_agreement"),
            "master_agreement_filename": _filename("doc_master_agreement"),
            "kyc_form": _bin("doc_kyc_form"),
            "kyc_form_filename": _filename("doc_kyc_form"),
            "annual_report": _bin("doc_annual_report"),
            "annual_report_filename": _filename("doc_annual_report"),
            "insurance_certificates": _bin("doc_insurance"),
            "insurance_certificates_filename": _filename("doc_insurance"),
            "other_documents": _bin("doc_other"),
            "other_documents_filename": _filename("doc_other"),
        }

        # 3) Ensure we have a tag "Vendor Application"
        tag = request.env["crm.tag"].sudo().search([("name", "=", "Vendor Application")], limit=1)
        if not tag:
            tag = request.env["crm.tag"].sudo().create({"name": "Vendor Application"})

        # Optionally pick a team. If you want a specific one, set its ID here.
        # team_id = request.env["crm.team"].sudo().search([], limit=1).id or False
        team_id = False

        # 4) Create the Lead
        vals.update({
            # "partner_name": post.get('legal_name', '') or post.get('trading_name', ''),
            "team_id": team_id,
            "type": "opportunity",
            "tag_ids": [(4, tag.id)],
            "is_supplier_reg": True,
        })
        lead = request.env["crm.lead"].sudo().create(vals)

        return request.redirect(f'/supplier/thank-you?lead={lead.id}')

    @http.route('/supplier/thank-you', type='http', auth='public', website=True, sitemap=False)
    def supplier_thank_you(self, **kw):
        lead = request.env["crm.lead"].sudo().search([('id', '=', kw.get('lead', 0))])
        return request.render('bista_supplier_registration.supplier_thank_you_page', {'ref': lead.reference_no})

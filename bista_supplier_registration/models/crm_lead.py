# -*- encoding: utf-8 -*-

import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"
    _order = "create_date desc"

    is_supplier_reg = fields.Boolean('Is Supplier?', default=False)
    reference_no = fields.Char(string="Reference", copy=False,
                               readonly=True, default=lambda self: 'New', tracking=True)
    legal_name = fields.Char(
        string="Legal Name", help="Registered Legal Name", tracking=True, copy=False)
    vat = fields.Char(string='Tax ID', tracking=True, help="The Tax Identification Number.")
    trading_name = fields.Char(string="Trading Name", tracking=True, help="Trading Name (If different)")
    business_type = fields.Selection([
        ("manufacturer", "Manufacturer"),
        ("distributor", "Distributor"),
        ("service", "Service Provider"),
        ("other", "Other"),
    ], string="Type of Business", default='manufacturer', tracking=True, help="Specify the primary nature of the supplier business.")

    # documents related field
    incorporation_certificate = fields.Binary(
        string="Certificate of Incorporation / Business Registration",
        help="Upload the official Certificate of Incorporation or Business Registration document.",
        attachment=True
    )
    incorporation_certificate_filename = fields.Char(string="File Name")
    related_incorporation_certificate_id = fields.Many2one(
        "ir.attachment",
        string="Certificate of Incorporation / Business Registration Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    bank_proof = fields.Binary(
        string="Proof of Bank Account",
        help="Upload bank account verification documents (e.g., IBAN Consult).",
        attachment=True,
    )
    bank_proof_filename = fields.Char(string="File Name")
    related_bank_proof_id = fields.Many2one(
        "ir.attachment",
        string="Proof of Bank Account Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    master_agreement = fields.Binary(
        string="Signed Master Agreement / Framework",
        help="Upload the signed Master Agreement or Framework contract.",
        attachment=True
    )
    master_agreement_filename = fields.Char(string="File Name")
    related_master_agreement_id = fields.Many2one(
        "ir.attachment",
        string="Signed Master Agreement / Framework Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    kyc_form = fields.Binary(
        string="KYC Form / Company Financial Structure",
        help="Upload Know Your Customer (KYC) documents or company financial structure details.",
        attachment=True
    )
    kyc_form_filename = fields.Char(string="File Name")
    related_kyc_form_id = fields.Many2one(
        "ir.attachment",
        string="KYC Form / Company Financial Structure Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    annual_report = fields.Binary(
        string="Annual Report (Latest Available)",
        help="Upload the latest available Annual Report for the company.",
        attachment=True
    )
    annual_report_filename = fields.Char(string="File Name")
    related_annual_report_id = fields.Many2one(
        "ir.attachment",
        string="Annual Report (Latest Available) Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    insurance_certificates = fields.Binary(
        string="Insurance Certificates",
        help="Upload valid insurance certificates related to the business.",
        attachment=True
    )
    insurance_certificates_filename = fields.Char(string="File Name")
    related_insurance_certificates_id = fields.Many2one(
        "ir.attachment",
        string="Insurance Certificates Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    other_documents = fields.Binary(
        string="Other Documents",
        help="Upload any other relevant documents not covered in the fields above.",
        attachment=True
    )
    other_documents_filename = fields.Char(string="File Name")
    related_other_documents_id = fields.Many2one(
        "ir.attachment",
        string="Other Documents Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    extra_documents = fields.Binary(
        string="Extra Documents",
        help="Upload any additional supporting files or reference documents.",
        attachment=True
    )
    extra_documents_filename = fields.Char(string="File Name")
    related_extra_documents_id = fields.Many2one(
        "ir.attachment",
        string="Extra Documents Attachment",
        compute="_compute_related_authorization_attachment_ids",
        store=True,
        copy=False,
    )

    # bank related field: res.bank
    bank_name = fields.Char(string="Bank Name", tracking=True)
    bic = fields.Char(string='BIC Code', help="Bank BIC Code or SWIFT.", tracking=True)
    bank_country = fields.Many2one('res.country', string='Bank Country', tracking=True)
    bank_id = fields.Many2one('res.bank', string='Bank', tracking=True)

    # person wise bank field : res.partner.bank
    acc_number = fields.Char('Account Number', tracking=True)
    acc_holder_name = fields.Char(
        string='Account Holder Name', tracking=True,
        help="Account holder name, in case it is different than the name of the Account Holder"
    )
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    supplier_invoice_currency_id = fields.Many2one("res.currency", string="Supplier Invoice Currency", tracking=True)
    standard_payment_term = fields.Char(string="Standard Payment Terms", tracking=True)
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        tracking=True,
        help="Default payment terms to be applied (e.g., Net 30) when working with this bank account."
    )
    state = fields.Selection([
        ('operation', 'Operational Team'),
        ('finance', 'Finance Team'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('locked', 'Locked'),
    ], string="Status", default='operation', tracking=True)
    can_reject = fields.Boolean(
        string="Can Reject",
        compute="_compute_can_reject",
        store=False
    )

    # Finance/Admin Primary Contact
    finance_name = fields.Char(string="Finance/Admin Name", help="Finance/Admin Contact Name", tracking=True)
    finance_phone = fields.Char(string="Finance/Admin Phone", help="Finance/Admin Contact Phone", tracking=True)
    finance_email = fields.Char(string="Finance/Admin Email", help="Finance/Admin Contact Email", tracking=True)
    finance_position = fields.Char(string="Finance/Admin Position", help="Finance/Admin Contact Position", tracking=True)

    # Operational Primary Contact
    operational_name = fields.Char(string="Operational Name", help="Operational Contact Name", tracking=True)
    operational_phone = fields.Char(string="Operational Phone", help="Operational Contact Phone", tracking=True)
    operational_email = fields.Char(string="Operational Email", help="Operational Contact Email", tracking=True)
    operational_position = fields.Char(string="Operational Position", help="Operational Contact Position", tracking=True)

    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)
    extra_info = fields.Text(string="Extra Information", help="Provide any additional details.", tracking=True)

    has_state = fields.Boolean(string='Has State', compute='_compute_has_state')

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.depends('country_id')
    def _compute_has_state(self):
        """ Compute field to check if the lead has a state """
        for rec in self:
            rec.has_state = False
            if rec.country_id:
                state_id = self.env['res.country.state'].search([('country_id', '=', rec.country_id.id)], limit=1)
                if state_id:
                    rec.has_state = True

    @api.depends(
        "incorporation_certificate",
        "bank_proof",
        "master_agreement",
        "kyc_form",
        "annual_report",
        "insurance_certificates",
        "other_documents",
        "extra_documents",
    )
    def _compute_related_authorization_attachment_ids(self):
        Attachment = self.env["ir.attachment"].sudo()
        # mapping: binary_field -> related_many2one_field
        field_map = {
            "incorporation_certificate": "related_incorporation_certificate_id",
            "bank_proof": "related_bank_proof_id",
            "master_agreement": "related_master_agreement_id",
            "kyc_form": "related_kyc_form_id",
            "annual_report": "related_annual_report_id",
            "insurance_certificates": "related_insurance_certificates_id",
            "other_documents": "related_other_documents_id",
            "extra_documents": "related_extra_documents_id",
        }

        for rec in self:
            for bin_field, rel_field in field_map.items():
                bin_value = getattr(rec, bin_field)
                if bin_value:
                    attachment = Attachment.search(
                        [
                            ("res_model", "=", rec._name),
                            ("res_id", "=", rec.id),
                            ("res_field", "=", bin_field),
                        ],
                        limit=1,
                        order="create_date desc",
                    )
                    setattr(rec, rel_field, attachment or False)
                else:
                    setattr(rec, rel_field, False)

    def _notify_finance_team(self):
        """Notify Finance team when supplier registration is approved by Operations."""
        finance_group = self.env.ref('bista_supplier_registration.group_supplier_finance')
        template = self.env.ref('bista_supplier_registration.mail_template_supplier_approved')

        menu_id = self.env.ref('bista_supplier_registration.menu_supplier_register_main').id
        action_id = self.env.ref('bista_supplier_registration.action_supplier_register').id
        view_id = self.env.ref('bista_supplier_registration.view_supplier_register_form').id

        if finance_group and template:
            recipients = finance_group.users.mapped('partner_id')
            if recipients:
                for lead in self:
                    template.sudo().with_context(
                        menu_id=menu_id or 0,
                        action_id=action_id or 0,
                        view_id=view_id or 0
                    ).send_mail(
                        lead.id,
                        force_send=True,
                        raise_exception=False,
                        email_values={'recipient_ids': [(6, 0, recipients.ids)]}
                    )
                    _logger.info(
                        "Supplier registration approved by Operations Team: Lead %s (ID: %d). Email sent to Finance Team: %s",
                        lead.name, lead.id, recipients.mapped('email')
                    )

    def _notify_customer(self):
        """Send email notification to the supplier (customer) on approval."""
        template = self.env.ref('bista_supplier_registration.mail_template_supplier_customer')
        if template:
            for lead in self:
                if lead.partner_id and lead.partner_id.email:
                    template.sudo().with_context(
                        lang=lead.partner_id.lang or 'en_US'
                    ).send_mail(
                        lead.id,
                        force_send=True,
                        raise_exception=False,
                        email_values={'email_to': lead.partner_id.email}
                    )
                    _logger.info(
                        "Customer notification sent for Lead %s (ID: %d) to %s",
                        lead.name, lead.id, lead.partner_id.email
                    )

    def action_set_finance(self):
        """
        Approve the supplier reg request from ops team:
        - Change state to 'finance'
        - notify the finance team.
        """
        for lead in self:
            lead.write({'state': 'finance'})

            # Send email notification to finance team users
            lead._notify_finance_team()

    def action_approve(self):
        """
        Approve the supplier reg request:
        - Change the state to 'approved'
        - Activate the linked partner so portal access is granted
        - Notify customer via email
        """
        for lead in self:
            if not lead.partner_id:
                raise UserError("Cannot approve: Registration request has no linked partner.")
            if not lead.bank_id:
                raise UserError("Cannot approve: Registration request has no linked bank account.")

            lead.write({'state': 'approved'})
            lead.partner_id.write({'registration_status': True,})
            child = self.env['res.partner'].search([('parent_id', '=', lead.partner_id.id)])
            if child:
                child.sudo().write({'registration_status': True})
            lead.partner_id.grant_portal_access()
            lead._notify_customer()

            _logger.info(
                "Supplier Registration %s (ID: %d) approved and portal access granted to partner %s.",
                lead.name, lead.id, lead.partner_id.name)

    def action_reject(self):
        """
        Reject the supplier registration request:
        - Change the state to 'rejected'
        """
        for lead in self:
            lead.write({'state': 'rejected'})

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Supplier Application'),
            'res_model': 'supplier.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lead_id': self.id},
        }

    def action_reset_to_operation(self):
        """
        Reset the supplier registration request:
        - Change the state back to 'operation'
        - Allow the process to be reviewed again
        """
        for lead in self:
            lead.write({'state': 'operation'})

    def action_lock(self):
        """
        Lock the supplier registration request:
        - Change the state to 'locked'
        - Make the record read-only to prevent further edits
        """
        for lead in self:
            lead.write({'state': 'locked'})

    def _create_supplier(self):
        """Create supplier values from lead data"""
        self.ensure_one()
        supplier = {
            'name': self.partner_id.name or self.name,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': self.state_id.id,
            'zip': self.zip,
            'vat': self.vat,
            'country_id': self.country_id.id,
            'website': self.website,
            'email': self.email_from,
            'phone': self.phone,
            'mobile': self.mobile,
            'customer_rank': 0,
            'supplier_rank': 1,
            'business_type': self.business_type,
            'property_payment_term_id': False,
            'property_supplier_payment_term_id': self.payment_term_id.id,
            'trading_name': self.trading_name,
            'registration_status': False,
            'company_type': 'company',
            'is_registered_customer': False,
            'is_registered_supplier': True,
            'comment': self.description,
            'title': self.title.id,
            'function': self.function,
            'type': 'contact',
        }
        if self.lang_id.active:
            supplier['lang'] = self.lang_id.code
        return self.env['res.partner'].sudo().create(supplier)

    def _assign_and_deactivate_supplier(self):
        """Create a partner from contact registration data, link it to the lead"""
        for lead in self:
            partner = lead._create_supplier()
            lead.partner_id = partner.id

            lead._create_finance_child_contact(lead.partner_id, supplier_rank=1)
            lead._create_operational_child_contact(lead.partner_id, supplier_rank=1)

    def _notify_ops_team(self):
        """Send email to all users in Supplier Operations group."""
        ops_group = self.env.ref('bista_supplier_registration.group_supplier_ops')
        email_template = self.env.ref('bista_supplier_registration.mail_template_supplier_submitted')

        menu_id = self.env.ref('bista_supplier_registration.menu_supplier_register_main').id
        action_id = self.env.ref('bista_supplier_registration.action_supplier_register').id
        view_id = self.env.ref('bista_supplier_registration.view_supplier_register_form').id

        if ops_group and email_template:
            recipients = ops_group.users.mapped('partner_id')
            if recipients:
                for lead in self:
                    email_template.with_context(
                        menu_id=menu_id or 0,
                        action_id=action_id or 0,
                        view_id=view_id or 0
                    ).send_mail(
                        lead.id,
                        force_send=True,
                        raise_exception=False,
                        email_values={'recipient_ids': [(6, 0, recipients.ids)]}
                    )
                    _logger.info(
                        "Supplier registration submitted: Lead %s (ID: %d). Email sent to Operations Team. %s",
                        lead.name, lead.id, recipients.mapped('email')
                    )

    # NOTE: Supplier-Registation specific logic, skipped for normal lead creation.
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get('default_is_supplier_reg') or vals.get('is_supplier_reg'):
                if 'is_supplier_reg' not in vals:
                    vals['is_supplier_reg'] = True
                if 'contact_name' not in vals and not vals.get('contact_name', '') and vals.get('legal_name', ''):
                    vals.update({
                        'contact_name': vals.get('legal_name', ''),
                    })
                if vals.get('reference_no', 'New') == 'New' and vals['is_supplier_reg']:
                    vals['reference_no'] = self.env['ir.sequence'].sudo().next_by_code('crm.lead.distributor.reference') or 'New'
                if not vals.get('name'):
                    vals['name'] = vals.get('legal_name', '') or 'Unnamed'
        leads = super(CrmLead, self).create(vals_list)

        for lead in leads.filtered(lambda x: x.is_supplier_reg):
            # Partner assign to lead
            lead._create_partner_bank_account()
            lead._assign_and_deactivate_supplier()
            # Send email notification to operations team users
            lead._notify_ops_team()

        return leads

    def action_open_partner(self):
        self.ensure_one()
        if not self.partner_id:
            return
        return {
            'name': 'Supplier',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }

    @api.depends('state')
    def _compute_can_reject(self):
        for rec in self:
            user = self.env.user
            rec.can_reject = False

            if rec.state == 'operation' and user.has_group('bista_supplier_registration.group_supplier_ops'):
                rec.can_reject = True
            elif rec.state == 'finance' and user.has_group('bista_supplier_registration.group_supplier_finance'):
                rec.can_reject = True

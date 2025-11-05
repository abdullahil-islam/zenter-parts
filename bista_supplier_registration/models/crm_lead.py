import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"
    _order = "create_date desc"

    is_supplier_reg = fields.Boolean('Is Supplier?', default=False)
    reference_no = fields.Char(string="Reference", required=True, copy=False,
                               readonly=True, default=lambda self: 'New', tracking=True)
    legal_name = fields.Char(
        string="Legal Name", help="Registered Legal Name", required=True, tracking=True, copy=False)
    vat = fields.Char(string='Tax ID', tracking=True,
                      help="The Tax Identification Number.", required=True)
    # supplier_website = fields.Char('Website', tracking=True)
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
        attachment=True,
        required=True
    )
    incorporation_certificate_filename = fields.Char(string="File Name")

    bank_proof = fields.Binary(
        string="Proof of Bank Account",
        help="Upload bank account verification documents (e.g., IBAN Consult).",
        attachment=True,
        required=True
    )
    bank_proof_filename = fields.Char(string="File Name")

    master_agreement = fields.Binary(
        string="Signed Master Agreement / Framework",
        help="Upload the signed Master Agreement or Framework contract.",
        attachment=True
    )
    master_agreement_filename = fields.Char(string="File Name")

    kyc_form = fields.Binary(
        string="KYC Form / Company Financial Structure",
        help="Upload Know Your Customer (KYC) documents or company financial structure details.",
        attachment=True
    )
    kyc_form_filename = fields.Char(string="File Name")

    annual_report = fields.Binary(
        string="Annual Report (Latest Available)",
        help="Upload the latest available Annual Report for the company.",
        attachment=True
    )
    annual_report_filename = fields.Char(string="File Name")

    insurance_certificates = fields.Binary(
        string="Insurance Certificates",
        help="Upload valid insurance certificates related to the business.",
        attachment=True
    )
    insurance_certificates_filename = fields.Char(string="File Name")

    other_documents = fields.Binary(
        string="Other Documents",
        help="Upload any other relevant documents not covered in the fields above.",
        attachment=True
    )
    other_documents_filename = fields.Char(string="File Name")

    # bank related field: res.bank
    bank_name = fields.Char(string="Bank Name", tracking=True, required=True)
    bic = fields.Char(string='BIC Code', help="Bank BIC Code or SWIFT.", tracking=True, required=True)
    bank_country = fields.Many2one('res.country', string='Bank Country', tracking=True, required=True)

    # person wise bank field : res.partner.bank
    acc_number = fields.Char('Account Number', tracking=True, required=True)
    acc_holder_name = fields.Char(
        string='Account Holder Name', tracking=True, required=True,
        help="Account holder name, in case it is different than the name of the Account Holder"
    )
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    supplier_invoice_currency_id = fields.Many2one("res.currency", string="Supplier Invoice Currency", tracking=True)
    standard_payment_term = fields.Char(string="Standard Payment Terms", tracking=True)
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        tracking=True,
        required=True,
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
    extra_documents = fields.Binary(
        string="Extra Documents",
        help="Upload any additional supporting files or reference documents",
        attachment=True,
    )
    extra_documents_filename = fields.Char(string="File Name")

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

            lead.write({'state': 'approved'})

            lead.partner_id.registration_status = True
            lead.partner_id.grant_portal_access()

            # Send email notification to customer
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

    def _assign_and_deactivate_partner(self):
        """Create a partner from lead and mark as supplier if applicable."""
        res = super()._assign_and_deactivate_partner()
        for lead in self:
            if lead.is_supplier_reg and lead.partner_id:
                lead.partner_id.write({
                    'supplier_rank': 1,
                    'company_type': 'company',
                    'is_registered_supplier': True,
                })
            # partner.active = False
        return res

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
            if self.env.context.get('is_supplier_reg') or vals.get('is_supplier_reg'):
                if 'is_supplier_reg' not in vals:
                    vals['is_supplier_reg'] = True
                if 'contact_name' not in vals and not vals.get('contact_name', '') and vals.get('legal_name', ''):
                    vals.update({
                        'contact_name': vals.get('legal_name', ''),
                    })
                if vals.get('reference_no', 'New') == 'New':
                    vals['reference_no'] = self.env['ir.sequence'].next_by_code('crm.lead.reference') or 'New'
                if not vals.get('name'):
                    vals['name'] = vals.get('legal_name', '') or 'Unnamed'
        leads = super(CrmLead, self).create(vals_list)

        for lead in leads.filtered(lambda x: x.is_supplier_reg):
            # Partner assign to lead
            lead._assign_and_deactivate_partner()
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

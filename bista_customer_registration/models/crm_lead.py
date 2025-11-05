import logging
from odoo import fields, models, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"
    _order = "create_date desc"

    is_customer_reg = fields.Boolean('Is Customer?', default=False)
    # customer_name = fields.Char(
    #     string="Legal Name", help="Registered Legal Name", tracking=True)
    # customer_website = fields.Char('Website', tracking=True)
    customer_state = fields.Selection([
        ('finance', 'Financial'),
        ('commercial', 'Commercial'),
        ('accounts', 'Accounts'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Status", default='finance', tracking=True)
    can_reject_customer = fields.Boolean(
        string="Can Reject Customer",
        compute="_compute_can_reject_customer",
        store=False
    )
    # customer contact field
    # customer_contact_name = fields.Char(
    #     string="Contact Name", tracking=True, help="Primary contact person for the customer")
    # customer_contact_phone = fields.Char(
    #     string="Contact Phone", tracking=True, help="Phone number of the primary customer contact")
    # customer_contact_email = fields.Char(
    #     string="Contact Email", tracking=True, help="Email address of the primary customer contact")

    # documents related field
    # address_proof = fields.Binary(
    #     string="Address Proof",
    #     help="Upload Address Proof verification documents.",
    #     attachment=True
    # )
    # address_proof_filename = fields.Char(string="File Name")
    #
    # master_agreement = fields.Binary(
    #     string="Signed Master Agreement / Framework",
    #     help="Upload the signed Master Agreement or Framework contract.",
    #     attachment=True
    # )
    # master_agreement_filename = fields.Char(string="File Name")
    #
    # kyc_form = fields.Binary(
    #     string="KYC Form / Company Financial Structure",
    #     help="Upload  Customer (KYC) documents or financial structure details.",
    #     attachment=True
    # )
    # kyc_form_filename = fields.Char(string="File Name")
    #
    # other_documents = fields.Binary(
    #     string="Other Documents",
    #     help="Upload any other relevant documents not covered in the fields above.",
    #     attachment=True
    # )
    # other_documents_filename = fields.Char(string="File Name")
    # rejection_reason = fields.Text(string="Rejection Reason", tracking=True)
    # extra_info = fields.Text(string="Extra Information", help="Provide any additional details.", tracking=True)
    # extra_documents = fields.Binary(
    #     string="Extra Documents",
    #     help="Upload any additional supporting files or reference documents",
    #     attachment=True,
    # )
    # extra_documents_filename = fields.Char(string="File Name")
    payment_condition = fields.Char(string="Payment Condition")
    price_list_discount = fields.Char(string="Price List Discount")

    def action_set_commercial_customer(self):
        for lead in self:
            lead.write({'customer_state': 'commercial'})

    def action_set_accounts_customer(self):
        for lead in self:
            lead.write({'customer_state': 'accounts'})

    def action_approve_customer(self):
        """
        Approve the customer registration request:
        - Change the state to 'approved'
        - Create the main customer contact (res.partner)
        - Create child contact if customer-specific fields exist
        """
        for lead in self:
            if not lead.partner_id:
                raise UserError("Cannot approve: Registration request has no linked partner.")

            lead.write({'customer_state': 'approved'})

            # Create main customer partner
            lead.partner_id.registration_status = True
            lead.partner_id.grant_portal_access()

            lead._create_customer_child_contact(lead.partner_id)
            _logger.info(
                "Customer Registration %s (ID: %d) approved and portal access granted to partner %s.",
                lead.name, lead.id, lead.partner_id.name)

    def _create_customer_child_contact(self, partner):
        """
        Create a child contact under the given partner using customer contact fields
        """
        if not (self.finance_name or self.finance_phone or self.finance_email):
            return
        self.env['res.partner'].create({
            'parent_id': partner.id,
            'type': 'contact',
            'name': self.finance_name,
            'phone': self.finance_phone,
            'email': self.finance_email,
        })

    def action_reject_customer(self):
        """
        Reject the customer registration request:
        - Change the state to 'rejected'
        """
        for lead in self:
            lead.write({'customer_state': 'rejected'})

    def action_reset_to_finance_customer(self):
        """
        Reset the customer registration request:
        - Change the state back to 'operation'
        - Allow the process to be reviewed again
        """
        for lead in self:
            lead.write({'customer_state': 'finance'})

    def _assign_and_deactivate_partner(self):
        """Create a partner from lead and mark as customer if applicable."""
        res = super()._assign_and_deactivate_partner()
        for lead in self:
            if lead.is_customer_reg and lead.partner_id:
                lead.partner_id.write({
                    'customer_rank': 1,
                    'company_type': 'company',
                    'is_registered_customer': True,
                })
        return res

    # NOTE: Customer-Registation specific logic, skipped for normal lead creation.
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get('is_customer_reg') or vals.get('is_customer_reg'):
                if 'is_customer_reg' not in vals:
                    vals['is_customer_reg'] = True
                if 'contact_name' not in vals and not vals.get('contact_name', '') and vals.get('legal_name', ''):
                    vals.update({
                        'contact_name': vals.get('legal_name', ''),
                    })
                if vals.get('reference_no', 'New') == 'New':
                    vals['reference_no'] = self.env['ir.sequence'].next_by_code('crm.lead.customer.reference') or 'New'
                if not vals.get('name'):
                    vals['name'] = vals.get('legal_name', '') or 'Unnamed'
        leads = super(CrmLead, self).create(vals_list)
        for lead in leads.filtered(lambda x: x.is_customer_reg):
            # Partner assign to lead
            lead._assign_and_deactivate_partner()

        return leads

    def action_open_customer(self):
        self.ensure_one()
        if not self.partner_id:
            return
        return {
            'name': 'Customer',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
        }

    @api.depends('customer_state')
    def _compute_can_reject_customer(self):
        for rec in self:
            user = self.env.user
            rec.can_reject_customer = False

            if rec.customer_state == 'finance' and user.has_group('bista_customer_registration.group_customer_finance'):
                rec.can_reject_customer = True
            elif rec.customer_state == 'commercial' and user.has_group('bista_customer_registration.group_customer_commercial'):
                rec.can_reject_customer = True
            elif rec.customer_state == 'accounts' and user.has_group('bista_customer_registration.group_customer_accounts'):
                rec.can_reject_customer = True

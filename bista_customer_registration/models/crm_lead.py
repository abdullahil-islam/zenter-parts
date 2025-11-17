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
    payment_condition = fields.Char(string="Payment Condition")
    price_list_discount = fields.Char(string="Price List Discount")
    distributor_or_customer = fields.Selection(
        [('distributor', 'Distributor'), ('customer', 'Customer')],
        string='Registration Type',
        help='Type of registration: Distributor or Customer'
    )

    def _assign_and_deactivate_partner(self):
        """Create a partner from contact registration data, link it to the lead"""
        for lead in self:
            partner = lead._create_customer()
            lead.partner_id = partner.id
            lead.partner_id.sudo().write({
                'name': lead.partner_id.name or lead.name,
                'street': lead.street,
                'street2': lead.street2,
                'city': lead.city,
                'state_id': lead.state_id.id,
                'zip': lead.zip,
                'vat': lead.vat,
                'country_id': lead.country_id.id,
                'website': lead.website,
                'email': lead.email_from,
                'phone': lead.phone,
                'lead_id': lead.id,
                'customer_rank': 1,
                'supplier_rank': 0,
                'business_type': lead.business_type,
                'property_payment_term_id': lead.payment_term_id.id,
                'property_supplier_payment_term_id': False,
                'trading_name': lead.trading_name,
                'registration_status': False,
                'company_type': 'company',
                'is_registered_customer': True,
                'is_registered_supplier': False,
            })

            lead._create_finance_child_contact(lead.partner_id, customer_rank=1)
            lead._create_operational_child_contact(lead.partner_id, customer_rank=1)

    def _create_partner_bank_account(self):
        """Create partner bank account if it doesn't exist"""
        self.ensure_one()

        if self.bank_id and self.acc_number and self.currency_id and self.partner_id:
            # Check if bank account already exists
            existing_bank = self.env['res.partner.bank'].search([
                ('partner_id', '=', self.partner_id.id),
                ('bank_id', '=', self.bank_id.id),
                ('acc_number', '=', self.acc_number),
                ('currency_id', '=', self.currency_id.id),
            ], limit=1)

            # Only create if it doesn't exist
            if not existing_bank:
                self.partner_id.sudo().write({
                    'bank_ids': [(0, 0, {
                        'bank_id': self.bank_id.id,
                        'acc_number': self.acc_number,
                        'currency_id': self.currency_id.id,
                    })]
                })

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
                reg_type = vals.get('distributor_or_customer')
                if vals.get('reference_no', 'New') == 'New' and reg_type == 'customer':
                    vals['reference_no'] = self.env['ir.sequence'].sudo().next_by_code('crm.lead.customer.reference') or 'New'
                elif vals.get('reference_no', 'New') == 'New' and reg_type == 'distributor':
                    vals['reference_no'] = self.env['ir.sequence'].sudo().next_by_code('crm.lead.distributor.reference') or 'New'
                if not vals.get('name'):
                    vals['name'] = vals.get('legal_name', '') or 'Unnamed'
        leads = super(CrmLead, self).create(vals_list)
        for lead in leads.filtered(lambda x: x.is_customer_reg):
            # Partner assign to lead
            lead._create_partner_bank_account()
            lead._assign_and_deactivate_partner()

        return leads

    def write(self, vals):
        """Update related partner fields when certain contact fields are changed."""
        res = super().write(vals)
        bank_fields = ['bank_id', 'acc_number', 'currency_id', 'partner_id']
        if any(field in vals for field in bank_fields):
            for lead in self:
                lead._create_partner_bank_account()
        for lead in self:
            if lead.partner_id:
                partner_vals = {}
                if 'legal_name' in vals:
                    partner_vals['name'] = vals.get('legal_name')
                if 'email_from' in vals:
                    partner_vals['email'] = vals.get('email_from')
                if 'phone' in vals:
                    partner_vals['phone'] = vals.get('phone')
                if partner_vals:
                    lead.partner_id.write(partner_vals)
        return res

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
            if not lead.bank_id:
                raise UserError("Cannot approve: Registration request has no linked bank account.")

            lead.write({'customer_state': 'approved'})
            lead.partner_id.sudo().write({'registration_status': True})
            child = self.env['res.partner'].search([('parent_id', '=', lead.partner_id.id)])
            if child:
                child.sudo().write({'registration_status': True})
            lead.partner_id.grant_portal_access()

            _logger.info(
                "Customer Registration %s (ID: %d) approved and portal access granted to partner %s.",
                lead.name, lead.id, lead.partner_id.name)

    def _create_finance_child_contact(self, partner, customer_rank=0, supplier_rank=0):
        """
        Create a finance child contact under the given partner using customer contact fields
        """
        if not (self.finance_name or self.finance_phone or self.finance_email):
            return
        self.env['res.partner'].create({
            'parent_id': partner.id,
            'type': 'contact',
            'name': self.finance_name,
            'phone': self.finance_phone,
            'email': self.finance_email,
            'function': self.finance_position,
            'customer_rank': customer_rank,
            'supplier_rank': supplier_rank,
            'is_registered_customer': bool(customer_rank),
            'is_registered_supplier': bool(supplier_rank),
            'registration_status': False,
        })

    def _create_operational_child_contact(self, partner, customer_rank=0, supplier_rank=0):
        """
        Create a operational child contact under the given partner using customer contact fields
        """
        if not (self.operational_name or self.operational_phone or self.operational_email):
            return
        self.env['res.partner'].create({
            'parent_id': partner.id,
            'type': 'contact',
            'name': self.operational_name,
            'phone': self.operational_phone,
            'email': self.operational_email,
            'function': self.operational_position,
            'customer_rank': customer_rank,
            'supplier_rank': supplier_rank,
            'is_registered_customer': bool(customer_rank),
            'is_registered_supplier': bool(supplier_rank),
            'registration_status': False,
        })

    def _create_operational_child_contact(self, partner):
        """
        Create a operational child contact under the given partner using customer contact fields
        """
        if not (self.operational_name or self.operational_phone or self.operational_email):
            return
        self.env['res.partner'].create({
            'parent_id': partner.id,
            'type': 'contact',
            'name': self.operational_name,
            'phone': self.operational_phone,
            'email': self.operational_email,
            'function': self.operational_position,
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

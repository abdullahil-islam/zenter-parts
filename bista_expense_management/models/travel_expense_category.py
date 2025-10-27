from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TravelExpenseCategory(models.Model):
    _name = 'travel.expense.category'
    _description = 'Travel Expense Category'

    name = fields.Char(required=True)
    type = fields.Selection(
        [('po', 'PO'), ('per_diem', 'Per Diem'), ('other', 'Other')],
        string='Type', default='po', required=True
    )
    meal_type = fields.Selection(
        [('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner')],
        string='Meal Type', default=''
    )
    price_unit = fields.Monetary(string='Price', currency_field='currency_id')
    is_po_approve = fields.Boolean(string='Require PO Approval')
    state = fields.Selection([('draft','Draft'), ('confirmed','Confirmed')], default='draft')
    product_id = fields.Many2one('product.product', string='Created Product', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this journal")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', help='The currency used to enter statement', string="Currency")

    def action_confirm(self):
        """Confirm category and create a linked product automatically."""
        self.ensure_one()
        if self.product_id:
            return True
        Product = self.env['product.product'].sudo()
        vals = {
            'name': self.name,
            # create a simple consumable product; change type if you want 'service' or template instead
            'type': 'service',
            # custom fields on product (added by this module)
            'travel_exp_conf_id': self.id,
            'travel_exp_product': True,
            'can_be_expensed': True,
            'sale_ok': False,
            'purchase_ok': False,
            'taxes_id': False,
        }
        prod = Product.create(vals)
        self.product_id = prod.id
        self.state = 'confirmed'
        return True

    @api.onchange('meal_type')
    def onchange_meal_type(self):
        if self.type == 'per_diem':
            if self.meal_type == 'breakfast':
                self.price_unit = 15
            elif self.meal_type == 'lunch':
                self.price_unit = 25
            elif self.meal_type == 'dinner':
                self.price_unit = 20
            else:
                self.price_unit = 1

    @api.onchange('type')
    def onchange_type(self):
        self.price_unit = 0

    # @api.depends('name')
    # def compute_product_name(self):
    #     for rec in self:
    #         rec.product_id.name = rec.name


class ProductProduct(models.Model):
    _inherit = 'product.product'

    travel_exp_conf_id = fields.Many2one('travel.expense.category', string='Travel Expense Category')
    travel_exp_product = fields.Boolean(string='Is Travel Expense Product', default=False)
    travel_exp_type = fields.Selection(
        related='travel_exp_conf_id.type',
        string='Travel Expense Type',
        readonly=True,
        store=True
    )

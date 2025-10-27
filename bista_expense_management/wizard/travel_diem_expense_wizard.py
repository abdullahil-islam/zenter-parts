from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pytz import timezone, UTC


class TravelDiemExpenseWizardLine(models.TransientModel):
    _name = 'travel.diem.expense.wizard.line'
    _description = 'Travel Diem Expense Wizard Line'

    wizard_id = fields.Many2one('travel.diem.expense.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    price = fields.Monetary(string='Unit Price', currency_field='currency_id')
    qty = fields.Float(string='Quantity')
    total_price = fields.Monetary(string='Total Price', currency_field='currency_id')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, index=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this journal")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', help='The currency used to enter statement', string="Currency")
    meal_type = fields.Selection(
        [('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner')],
        string='Meal Type', default=''
    )


class TravelDiemExpenseWizard(models.TransientModel):
    _name = 'travel.diem.expense.wizard'
    _description = 'Travel Diem Expense Wizard'

    departure_datetime = fields.Datetime(string='Departure', required=True)
    return_datetime = fields.Datetime(string='Return', required=True)
    travel_id = fields.Many2one('corporate.travel', string='Travel Record', readonly=True)

    line_ids = fields.One2many('travel.diem.expense.wizard.line', 'wizard_id', string='Expense Lines')
    total_cost = fields.Monetary(
            string='Total Cost',
            currency_field='currency_id',
            compute='_compute_total_cost',
            store=False
        )
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True,
                                 default=lambda self: self.env.company,
                                 help="Company related to this journal")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', help='The currency used to enter statement', string="Currency")

    @api.depends('line_ids.total_price')
    def _compute_total_cost(self):
        for wizard in self:
            wizard.total_cost = sum(line.total_price for line in wizard.line_ids)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        travel_id = self.env.context.get('default_travel_id')
        if travel_id:
            res['travel_id'] = travel_id
        per_diem_categories = self.env['travel.expense.category'].search([
            ('type', '=', 'per_diem'),
            ('product_id', '!=', False)
        ])

        departure = self._get_user_dt(self.env.context.get('default_departure_datetime'))
        return_dt = self._get_user_dt(self.env.context.get('default_return_datetime'))

        breakfast_qty = 0
        lunch_qty = 0
        dinner_qty = 0
        lines = []

        if departure and return_dt:
            dep = fields.Datetime.to_datetime(departure)
            ret = fields.Datetime.to_datetime(return_dt)

            # ---- Deprature & Return same day
            if dep.date() == ret.date():
                if dep.hour < 10 and ret.hour >= 10:
                    breakfast_qty += 1
                if dep.hour < 14 and ret.hour >= 14:
                    lunch_qty += 1
                if dep.hour < 20 and ret.hour >= 20:
                    dinner_qty += 1

            # ---- Deprature & Return not same day
            else:
                # ----- First Day
                if dep.hour < 10:
                    breakfast_qty += 1
                if dep.hour < 14:
                    lunch_qty += 1
                if dep.hour < 20:
                    dinner_qty += 1

                # ----- Middle Days
                middle_days_count = max((ret.date() - dep.date()).days - 1, 0)
                breakfast_qty += middle_days_count
                lunch_qty += middle_days_count
                dinner_qty += middle_days_count

                # ----- Last Day
                if ret.hour >= 10:
                    breakfast_qty += 1
                if ret.hour >= 14:
                    lunch_qty += 1
                if ret.hour >= 20:
                    dinner_qty += 1

        for cat in per_diem_categories:
            meal_qty = 0
            if cat.meal_type == 'breakfast':
                meal_qty = breakfast_qty
            if cat.meal_type == 'lunch':
                meal_qty = lunch_qty
            if cat.meal_type == 'dinner':
                meal_qty = dinner_qty
            if meal_qty:
                lines.append((0, 0, {
                    'product_id': cat.product_id.id,
                    'price': cat.price_unit,
                    'currency_id': cat.currency_id.id,
                    'meal_type': cat.meal_type,
                    'qty': meal_qty,
                    'total_price': meal_qty * cat.price_unit,
                }))

        res['line_ids'] = lines
        return res

    def action_confirm(self):
        """Create corporate travel lines from wizard lines"""
        self.ensure_one()
        if not self.travel_id:
            raise UserError(_("Travel reference is not set on this wizard."))

        TravelLine = self.env['corporate.travel.line'].sudo()

        for line in self.line_ids:
            if line.total_price:
                TravelLine.create({
                    'is_meal_line': True,
                    'travel_id': self.travel_id.id,
                    'product_id': line.product_id.id,
                    'estimated_amount': line.total_price,
                })
        return {'type': 'ir.actions.act_window_close'}

    # def _get_user_dt(self, dt_str):
    #     """Convert server datetime string to user's local datetime"""
    #     if not dt_str:
    #         return None
    #     utc_dt = datetime.strptime(dt_str, DEFAULT_SERVER_DATETIME_FORMAT)
    #     user_tz = self.env.user.tz
    #     local_dt = utc_dt.astimezone(timezone(user_tz))
    #     dt = local_dt.replace(tzinfo=None)
    #     return dt

    def _get_user_dt(self, dt):
        """Convert stored UTC datetime to user's timezone (naive)."""
        if not dt:
            return None
        if isinstance(dt, str):
            dt = datetime.strptime(dt, DEFAULT_SERVER_DATETIME_FORMAT)
        if dt.tzinfo is None:
            dt = UTC.localize(dt)
        user_tz = timezone(self.env.user.tz or 'UTC')
        local_dt = dt.astimezone(user_tz)
        return local_dt.replace(tzinfo=None)

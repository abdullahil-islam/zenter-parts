from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CorporateTravelLine(models.Model):
    _name = 'corporate.travel.line'
    _description = 'Corporate Travel Line'

    travel_id = fields.Many2one('corporate.travel', string='Travel Reference', ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Category',
        domain="[('can_be_expensed', '=', True),  ('travel_exp_product', '=', True), ('travel_exp_conf_id.type', '!=', 'per_diem')]"
    )
    description = fields.Char()
    estimated_amount = fields.Monetary(required=True, default=0.0)
    currency_id = fields.Many2one('res.currency', related='travel_id.currency_id', store=True, readonly=True)
    payment_mode = fields.Selection([('own_account', 'Employee(to reimburse)'), ('company_account', 'Company')], string='Paid By', default='company_account')
    vendor_id = fields.Many2one('res.partner')
    is_meal_line = fields.Boolean(default=False)

    @api.onchange('product_id')
    def _compute_company_account(self):
        for rec in self:
            if rec.product_id.travel_exp_conf_id and rec.product_id.travel_exp_conf_id.type == 'other':
                rec.payment_mode = 'own_account'


class CorporateTravel(models.Model):
    _name = 'corporate.travel'
    _description = 'Corporate Travel Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self._default_employee(), tracking=True)
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', readonly=True)
    phone = fields.Char(related='employee_id.work_phone', string='Phone', readonly=True)
    email = fields.Char(related='employee_id.work_email', string='Email', readonly=True)
    destination = fields.Char(tracking=True)
    departure_datetime = fields.Datetime(tracking=True)
    return_datetime = fields.Datetime(tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    line_ids = fields.One2many('corporate.travel.line','travel_id', string='Estimated Costs', copy=True)
    total_estimated_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Draft'), ('md_approval', 'Managing Director'), ('fd_approval', 'Finance Director'),
        ('approved', 'Approved'), ('rejected', 'Rejected')
    ], default='draft', tracking=True)
    md_rejection_reason = fields.Text(string='MD Rejection Reason', tracking=True)
    fd_rejection_reason = fields.Text(string='FD Rejection Reason', tracking=True)
    expense_sheet_ids = fields.One2many('hr.expense.sheet', 'travel_id', string='Created Expense Sheets')
    
    # Purchase Order Fields
    purchase_order_ids = fields.One2many('purchase.order', 'travel_id', string='Purchase Orders', readonly=True)
    po_count = fields.Integer(string='PO Count', compute='_compute_po_count')

    # Advance Payment Fields
    advance_payment_id = fields.Many2one('account.payment', string='Advance Payment', readonly=True, copy=False)
    advance_move_id = fields.Many2one('account.move', string='Advance Payment Bill', readonly=True, copy=False)
    advance_account_id = fields.Many2one('account.account', string='Account', required=False, copy=False)
    advance_amount = fields.Monetary(string='Advance Amount', readonly=True, copy=False)
    advance_state = fields.Selection([
        ('none', 'No Advance'),
        ('paid', 'Paid'),
        ('partially_settled', 'Partially Settled'),
        ('fully_settled', 'Fully Settled'),
        ('reconciled', 'Reconciled'),
    ], string='Advance State', default='none', readonly=True, copy=False, tracking=True)

    # NEW FIELDS for Advance Settlement
    actual_other_expense = fields.Monetary(
        string='Actual Other Expenses',
        compute='_compute_actual_expenses',
        store=True,
        currency_field='currency_id',
        help="Total actual 'Other' expenses from approved expense sheets"
    )
    advance_balance = fields.Monetary(
        string='Advance Balance',
        compute='_compute_advance_balance',
        store=True,
        currency_field='currency_id',
        help="Positive = Employee owes company, Negative = Company owes employee"
    )
    settlement_payment_id = fields.Many2one(
        'account.payment',
        string='Settlement Payment',
        readonly=True,
        copy=False,
        help="Payment created to settle advance balance"
    )

    @api.depends('purchase_order_ids')
    def _compute_po_count(self):
        for rec in self:
            rec.po_count = len(rec.purchase_order_ids)

    @api.depends('expense_sheet_ids', 'expense_sheet_ids.state', 'expense_sheet_ids.expense_line_ids')
    def _compute_actual_expenses(self):
        """Calculate actual 'Other' expenses from approved/posted expense sheets"""
        for rec in self:
            total = 0.0
            # Get the "Other Expenses" sheet
            for sheet in rec.expense_sheet_ids:
                if 'Other Expenses' in sheet.name and sheet.state in ['approve', 'post', 'done']:
                    # Sum up all expense lines in this sheet
                    total += sum(sheet.expense_line_ids.mapped('total_amount_currency'))
            rec.actual_other_expense = total

    @api.depends('advance_amount', 'actual_other_expense')
    def _compute_advance_balance(self):
        """Calculate balance: Positive = Employee owes, Negative = Company owes"""
        for rec in self:
            rec.advance_balance = rec.advance_amount - rec.actual_other_expense

    def action_open_advance_wizard(self):
        """Return action to open advance payment wizard for this travel request."""
        self.ensure_one()
        ctx = dict(self.env.context or {})
        default_amount = sum(self.line_ids.filtered(lambda x: x.product_id.travel_exp_type == 'other' and x.payment_mode == 'own_account').mapped('estimated_amount'))
        ctx.update({
            'default_travel_id': self.id,
            'default_amount': default_amount or 0.0,
            'default_partner_id': self.employee_id.user_id.partner_id.id,
            'default_currency_id': self.currency_id.id or self.env.company.currency_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'travel.advance.payment.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_settle_advance(self):
        """Open wizard to settle advance balance"""
        self.ensure_one()
        
        if not self.advance_payment_id:
            raise UserError(_("No advance payment exists for this travel request."))
        
        if self.advance_state == 'fully_settled':
            raise UserError(_("Advance has already been fully settled."))
        
        if abs(self.advance_balance) < 0.01:  # Threshold for rounding
            raise UserError(_("Advance balance is already zero. No settlement needed."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Settle Advance'),
            'res_model': 'travel.advance.settlement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_travel_id': self.id,
                'default_balance_amount': abs(self.advance_balance),
                'default_balance_type': 'employee_owes' if self.advance_balance > 0 else 'company_owes',
            },
        }

    def action_view_purchase_orders(self):
        """Open purchase orders related to this travel request"""
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'create': False},
        }

    @api.model
    def _default_employee(self):
        user = self.env.user
        emp = self.env['hr.employee'].search([('user_id','=',user.id)], limit=1)
        return emp and emp.id or False

    @api.model
    def create(self, vals):
        if vals.get('name','New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('corporate.travel') or 'CT/NEW'
        return super().create(vals)

    @api.depends('line_ids.estimated_amount')
    def _compute_total(self):
        for rec in self:
            rec.total_estimated_amount = sum(rec.line_ids.mapped('estimated_amount'))

    @api.constrains('departure_datetime','return_datetime')
    def _check_dates(self):
        for rec in self:
            if rec.departure_datetime and rec.return_datetime and rec.return_datetime < rec.departure_datetime:
                raise ValidationError('Return datetime must be after departure datetime.')

    def action_submit(self):
        self.ensure_one()
        md_group = self.env.ref('bista_expense_management.group_md', raise_if_not_found=False)
        if md_group and self.employee_id.user_id and md_group.users and self.employee_id.user_id in md_group.users:
            # employee is MD -> skip to FD
            self.state = 'fd_approval'
            self._schedule_activity_for_group('bista_expense_management.group_fd', 'Please review travel request')
        else:
            self.state = 'md_approval'
            self._schedule_activity_for_group('bista_expense_management.group_md', 'Please review travel request')

        self.message_post(body='Travel request submitted for approval.')

    def _schedule_activity_for_group(self, group_xml_id, summary):
        group = self.env.ref(group_xml_id, raise_if_not_found=False)
        if not group:
            return
        users = group.users
        for user in users:
            self.activity_schedule('mail.mail_activity_data_todo', summary=summary, user_id=user.id)

    def action_approve_md(self):
        self.ensure_one()
        if not self.env.user.has_group('bista_expense_management.group_md') and not self.env.user.has_group('base.group_system'):
            raise ValidationError('Only Managing Director can approve here.')
        self.state = 'fd_approval'
        self._schedule_activity_for_group('bista_expense_management.group_fd', 'Please review travel request')
        self.message_post(body='Approved by Managing Director: %s' % (self.env.user.name,))

    def action_reject_md(self):
        self.ensure_one()
        self.state = 'rejected'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Travel'),
            'res_model': 'travel.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_travel_id': self.id,
                'user_role': 'MD',
            },
        }

    def action_approve_fd(self):
        self.ensure_one()
        if not self.env.user.has_group('bista_expense_management.group_fd') and not self.env.user.has_group('base.group_system'):
            raise ValidationError('Only Finance Director can approve here.')
        
        # Enhanced vendor validation - check both company_account and PO type lines
        for rec in self:
            # Check company_account lines
            missing_vendor_lines = rec.line_ids.filtered(
                lambda line: not line.vendor_id and line.payment_mode == 'company_account'
            )
            
            # Also check PO type lines specifically
            po_lines_no_vendor = rec.line_ids.filtered(
                lambda line: not line.vendor_id and 
                line.product_id and 
                line.product_id.travel_exp_conf_id and 
                line.product_id.travel_exp_conf_id.type == 'po'
            )

            if missing_vendor_lines or po_lines_no_vendor:
                all_missing = (missing_vendor_lines | po_lines_no_vendor)
                product_names = all_missing.mapped('product_id.name')
                error_message = _(
                    "The following lines are missing vendor information:\n\n%s\n\n"
                    "Please set the vendor for these lines before approving."
                ) % '\n'.join(['• ' + name for name in product_names])

                raise UserError(error_message)
        
        # Create Purchase Orders for PO type lines
        self._create_purchase_orders()
        
        # Create Expense Sheets
        sheets = self._create_expense_sheets()
        self.expense_sheet_ids = [(6, 0, sheets.ids)]
        
        self.state = 'approved'
        self.message_post(body='Approved by Finance Director: %s' % (self.env.user.name,))

    def action_reject_fd(self):
        self.ensure_one()
        self.state = 'rejected'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Travel'),
            'res_model': 'travel.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_travel_id': self.id,
                'user_role': 'FD',
            },
        }

    def _create_purchase_orders(self):
        """Create draft purchase orders for PO type travel lines, grouped by vendor"""
        self.ensure_one()
        
        # Get PO type lines
        po_lines = self.line_ids.filtered(
            lambda l: l.product_id and 
            l.product_id.travel_exp_conf_id and 
            l.product_id.travel_exp_conf_id.type == 'po' and
            l.vendor_id
        )
        
        if not po_lines:
            return self.env['purchase.order']
        
        # Group lines by vendor
        vendor_lines = {}
        for line in po_lines:
            vendor_id = line.vendor_id.id
            if vendor_id not in vendor_lines:
                vendor_lines[vendor_id] = []
            vendor_lines[vendor_id].append(line)
        
        # Create POs
        created_pos = self.env['purchase.order']
        PurchaseOrder = self.env['purchase.order'].sudo()
        
        for vendor_id, lines in vendor_lines.items():
            vendor = self.env['res.partner'].browse(vendor_id)
            
            # Prepare PO values
            po_vals = {
                'partner_id': vendor_id,
                'travel_id': self.id,
                'date_order': fields.Datetime.now(),
                'origin': self.name,
                'currency_id': self.currency_id.id or self.env.company.currency_id.id,
                'notes': _('Purchase Order for Travel Request: %s\nEmployee: %s\nDestination: %s') % (
                    self.name, self.employee_id.name, self.destination or ''
                ),
            }
            
            # Create PO
            po = PurchaseOrder.create(po_vals)
            
            # Create PO lines
            POLine = self.env['purchase.order.line'].sudo()
            for travel_line in lines:
                po_line_vals = {
                    'order_id': po.id,
                    'product_id': travel_line.product_id.id,
                    'name': travel_line.description or travel_line.product_id.name,
                    'product_qty': 1.0,
                    'price_unit': travel_line.estimated_amount,
                    'date_planned': self.departure_datetime or fields.Datetime.now(),
                    'travel_line_id': travel_line.id,  # Link to travel line
                }
                POLine.create(po_line_vals)
            
            created_pos |= po
            
            # Post message
            self.message_post(
                body=_('Purchase Order created: %s for vendor %s') % (po.name, vendor.name)
            )
        
        return created_pos

    def _create_expense_sheets(self):
        # Mapping: flights/car/hotel -> PO Expenses; food -> Per Diem; other -> Other Expenses
        po_lines = []
        per_diem_lines = []
        other_lines = []
        Expense = self.env['hr.expense']
        
        # iterate travel lines and map them to corresponding lists based on product -> travel config type
        for l in self.line_ids:
            # determine type from product's travel expense config
            t = False
            if l.product_id and l.product_id.travel_exp_conf_id:
                t = l.product_id.travel_exp_conf_id.type
            # prepare expense line values
            ln_vals = {
                'name': l.description or (l.product_id.name if l.product_id else False),
                'product_id': l.product_id.id if l.product_id else False,
                'total_amount_currency': l.estimated_amount or 0.0,
                'employee_id': self.employee_id.id,
                'payment_mode': l.payment_mode,
                'description': l.description,
                'vendor_id': l.vendor_id.id,
                'travel_line_id': l.id,  # Link back to travel line
            }
            if t == 'po':
                po_lines.append(ln_vals)
            elif t == 'per_diem':
                per_diem_lines.append(ln_vals)
            else:
                other_lines.append(ln_vals)

        Sheet = self.env['hr.expense.sheet']

        def make_sheet(name, lines, auto_approve=False):
            sheet_vals = {
                'name': name, 
                'employee_id': self.employee_id.id,
                'travel_id': self.id,
            }
            sheet = Sheet.create(sheet_vals)
            sheet.write({'journal_id': sheet.payment_method_line_id.journal_id.id})
            
            created_expenses = self.env['hr.expense']
            for ln in lines:
                ln_vals = dict(ln)
                ln_vals.update({'sheet_id': sheet.id})
                try:
                    expense = Expense.create(ln_vals)
                    created_expenses |= expense
                except Exception as e:
                    # Fallback with minimal fields
                    try:
                        expense = Expense.create({
                            'name': ln_vals.get('name'),
                            'sheet_id': sheet.id,
                            'total_amount_currency': ln_vals.get('total_amount_currency', 0.0),
                            'employee_id': ln_vals.get('employee_id'),
                            'payment_mode': ln_vals.get('payment_mode'),
                            'description': ln_vals.get('description'),
                            'vendor_id': ln_vals.get('vendor_id'),
                            'travel_line_id': ln_vals.get('travel_line_id'),
                        })
                        created_expenses |= expense
                    except Exception:
                        pass
            
            # Auto-approve PO expense sheets since they're tied to approved POs
            if auto_approve and created_expenses:
                try:
                    # Set state directly to approved/posted - skip normal approval flow
                    sheet.write({'state': 'approve'})
                    self.message_post(
                        body=_('PO Expense Sheet auto-approved: %s (linked to Purchase Orders)') % sheet.name
                    )
                except Exception:
                    pass
            
            return sheet

        # PO expenses - auto-approve since tied to POs
        s1 = make_sheet('PO Expenses - %s' % self.name, po_lines)
        s2 = make_sheet('Per Diem - %s' % self.name, per_diem_lines)
        s3 = make_sheet('Other Expenses - %s' % self.name, other_lines)
        
        return self.env['hr.expense.sheet'].browse([r.id for r in (s1|s2|s3) if r])

    def action_open_expense_sheets(self):
        self.ensure_one()
        return {
            'name': 'Expense Reports',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.sheet',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.expense_sheet_ids.ids)],
            'target': 'current',
        }

    def action_add_meals(self):
        """Open Travel Diem Expense Wizard and pass departure/return dates"""
        self.ensure_one()
        if not self.departure_datetime or not self.return_datetime:
            raise UserError(_("Please set both Departure and Return Date/Time before adding meals."))
        if self.return_datetime < self.departure_datetime:
            raise UserError(_("Return Date/Time cannot be before Departure Date/Time."))

        # Unlink any existing meal-related travel lines
        meal_lines = self.env['corporate.travel.line'].sudo().search([
            ('travel_id', '=', self.id),
            ('is_meal_line', '=', True)
        ])
        if meal_lines:
            meal_lines.unlink()

        return {
            'name': _('Travel Diem Expense Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'travel.diem.expense.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_departure_datetime': self.departure_datetime,
                'default_return_datetime': self.return_datetime,
                'default_travel_id': self.id,
            },
        }

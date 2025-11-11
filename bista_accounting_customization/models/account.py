# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    central_account_name = fields.Char(string="Central Account Name")
    central_acc_code = fields.Char(string="Central Account Code")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    user_id = fields.Many2one(string='User', related='move_id.invoice_user_id')

    @api.onchange('partner_id', 'product_id')
    def onchange_get_analytic_distribution(self):
        """
        Trigger analytic distribution computation on partner/product change.
        Raises validation errors in UI context.
        """
        for line in self:
            try:
                distributions = line.compute_analytic_distribution(
                    partner=line.partner_id,
                    product=line.product_id,
                    user=self.env.user,
                    raise_on_missing=True
                )
                line.analytic_distribution = distributions
            except ValidationError:
                # Re-raise so the UI still shows the validation error
                raise

    def compute_analytic_distribution(self, partner=None, product=None, user=None, raise_on_missing=False):
        """
        Return merged distribution dict from partner, product, user, and user's department.

        Order of precedence: partner -> product -> user -> department (later ones override earlier).
        Accepts record objects or falsy values.
        
        Args:
            partner: res.partner record or False
            product: product.template/product.product record or False
            user: res.users record or False
            raise_on_missing: bool - if True, raises ValidationError when user/department lack distribution
        
        Returns:
            dict: Merged analytic distribution
        """
        distributions = {}

        # 1. Partner distribution (includes country group distribution)
        if partner and getattr(partner, 'analytic_distribution', False):
            try:
                distributions.update(partner.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read partner.analytic_distribution for partner %s", partner.id)

        # 2. Product distribution (auto-computed from brand + category)
        if product and getattr(product, 'analytic_distribution', False):
            try:
                distributions.update(product.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read product.analytic_distribution for product %s", product.id)

        # 3. User + Department distribution
        user = user or self.env.user
        department = False
        try:
            department = user.employee_id.department_id if getattr(user, 'employee_id', False) else False
        except Exception:
            department = False

        # if caller cares about validation (UI), raise; otherwise log and continue
        if raise_on_missing:
            # Department validation
            if not department:
                raise ValidationError(
                    _('User "%s" is not linked to any employee or department. Please configure employee settings.') % user.name
                )
            
            if not getattr(department, 'analytic_distribution', False):
                raise ValidationError(
                    _('Analytic distribution is not set on department "%s". Please configure it.') % department.name
                )


        # 5. Department distribution (highest priority - overrides all)
        if department and getattr(department, 'analytic_distribution', False):
            try:
                distributions.update(department.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read department.analytic_distribution for department %s", department.id)

        return distributions

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-populate analytic distribution.
        Uses context flag to prevent recursion.
        """
        # First create records normally
        records = super().create(vals_list)

        # Skip if context flag is set (prevents infinite recursion)
        if self.env.context.get('skip_analytic_distribution_create'):
            return records

        # After creation, compute distribution for each created record
        for rec in records:
            try:
                # Compute using actual record values
                dist = rec.compute_analytic_distribution(
                    partner=(rec.partner_id.sudo() if rec.partner_id else False),
                    product=(rec.product_id.sudo() if rec.product_id else False),
                    user=self.env.user,
                    raise_on_missing=False  # shouldn't raise during imports/API calls
                )
                
                # Only write if computed distribution differs from current
                if dist and dist != (rec.analytic_distribution or {}):
                    # Use context flag to prevent recursion
                    rec.with_context(skip_analytic_distribution_write=True).write({
                        'analytic_distribution': dist
                    })
            except Exception:
                _logger.exception(
                    "Error computing analytic_distribution for newly created account.move.line id %s",
                    rec.id
                )

        return records

    def write(self, vals):
        """
        Override write to recompute analytic distribution when relevant fields change.
        Uses context flag to prevent recursion.
        """
        # Skip recomputation if context flag is set (prevents infinite recursion)
        if self.env.context.get('skip_analytic_distribution_write'):
            return super().write(vals)
        
        # Call super first to apply changes
        res = super().write(vals)

        # Determine whether we need to recompute analytic_distribution
        trigger_keys = {'partner_id', 'product_id'}
        
        # If the write explicitly sets analytic_distribution, assume caller handled it
        if 'analytic_distribution' in vals:
            return res

        # Only recompute when partner/product changed or when explicitly forced
        do_recompute = (
            bool(set(vals.keys()) & trigger_keys) or 
            bool(self.env.context.get('force_recompute_analytic_distribution'))
        )

        if not do_recompute:
            return res

        # Recompute for all records in this recordset
        for rec in self:
            try:
                dist = rec.compute_analytic_distribution(
                    partner=(rec.partner_id.sudo() if rec.partner_id else False),
                    product=(rec.product_id.sudo() if rec.product_id else False),
                    user=self.env.user,
                    raise_on_missing=False
                )
                
                if dist and dist != (rec.analytic_distribution or {}):
                    # Use context flag to prevent recursion
                    rec.with_context(skip_analytic_distribution_write=True).write({
                        'analytic_distribution': dist
                    })
            except Exception:
                _logger.exception(
                    "Error recomputing analytic_distribution for account.move.line id %s during write",
                    rec.id
                )

        return res

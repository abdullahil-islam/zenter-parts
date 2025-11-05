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

    # @api.onchange('partner_id', 'product_id')
    # def onchange_method(self):
    #     # distributions = self.analytic_distribution or {}
    #     distributions = {}
    #     if self.partner_id and self.partner_id.analytic_distribution:
    #         distributions.update(self.partner_id.analytic_distribution)
    #     if self.product_id and hasattr(self.product_id, 'analytic_distribution') and self.product_id.analytic_distribution:
    #         distributions.update(self.product_id.analytic_distribution)
    #
    #     user = self.env.user
    #     department = user.employee_id.department_id if user.employee_id and user.employee_id.department_id else False
    #     if not user.analytic_distribution:
    #         raise ValidationError('Analytic distribution plans is not set on user.')
    #     if not department.analytic_distribution:
    #         raise ValidationError(f'Analytic distribution plans is not set on employee\'s department ({department.name}).')
    #
    #     if user and hasattr(user, 'analytic_distribution') and user.analytic_distribution:
    #         distributions.update(user.analytic_distribution)
    #     if department.analytic_distribution:
    #         distributions.update(department.analytic_distribution)
    #
    #     self.analytic_distribution = distributions

    @api.onchange('partner_id', 'product_id')
    def onchange_get_analytic_distribution(self):
        for line in self:
            try:
                # Only raise validation if explicitly coming from UI
                # raise_on_missing = bool(self.env.context.get('raise_analytic_distribution_validation'))
                distributions = line.compute_analytic_distribution(
                    partner=line.partner_id,
                    product=line.product_id,
                    user=self.env.user,
                    raise_on_missing=True
                )
                line.analytic_distribution = distributions
            except ValidationError:
                # re-raise so the UI still shows the validation error
                raise

    # central helper used by onchange, create and write
    def compute_analytic_distribution(self, partner=None, product=None, user=None, raise_on_missing=False):
        """Return merged distribution dict from partner, product, user, and user's department.

        Order of precedence: partner -> product -> user -> department (later ones override earlier).
        Accepts record objects or falsy values.
        If raise_on_missing=True will raise if user/department don't have analytic_distribution
        (keeps original UI behavior). For imports/batch operations, pass False to avoid breaking imports.
        """
        distributions = {}

        # partner
        if partner and getattr(partner, 'analytic_distribution', False):
            try:
                distributions.update(partner.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read partner.analytic_distribution for partner %s", partner.id)

        # product
        if product and getattr(product, 'analytic_distribution', False):
            try:
                distributions.update(product.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read product.analytic_distribution for product %s", product.id)

        # user + department
        user = user or self.env.user
        department = False
        try:
            department = user.employee_id.department_id if getattr(user, 'employee_id', False) else False
        except Exception:
            department = False

        # if caller cares about validation (UI), raise; otherwise log and continue
        if raise_on_missing:
            # if not getattr(user, 'analytic_distribution', False):
            #     raise ValidationError(_('Analytic distribution plans is not set on user.'))
            if not (department and getattr(department, 'analytic_distribution', False)):
                dep_name = department.name if department else _('(no department)')
                raise ValidationError(
                    _('Analytic distribution plans is not set on employee\'s department (%s).') % dep_name)

        # user
        if getattr(user, 'analytic_distribution', False):
            try:
                distributions.update(user.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read user.analytic_distribution for user %s", user.id)

        # department
        if department and getattr(department, 'analytic_distribution', False):
            try:
                distributions.update(department.analytic_distribution or {})
            except Exception:
                _logger.exception("Failed to read department.analytic_distribution for department %s", department.id)

        return distributions

    # handle create (including multi-create)
    @api.model_create_multi
    def create(self, vals_list):
        # First create records normally
        records = super().create(vals_list)

        # After creation, compute distribution for each created record and write it
        # I am using sudo() for reading referenced records safely if needed
        for rec in records:
            try:
                # compute using factual record values
                dist = rec.compute_analytic_distribution(
                    partner=(rec.partner_id.sudo() if rec.partner_id else False),
                    product=(rec.product_id.sudo() if rec.product_id else False),
                    user=self.env.user,
                    raise_on_missing=False  # don't raise during imports
                )
                # Only write if computed distribution is non-empty or differs from current
                if dist != (rec.analytic_distribution or {}):
                    # Use write to update; skip triggers by passing context if needed
                    rec.write({'analytic_distribution': dist})
            except Exception:
                _logger.exception("Error computing analytic_distribution for newly created account.move.line id %s",
                                  rec.id)

        return records

    # handle write (updates)
    def write(self, vals):
        # We call super first to apply changes, then recompute for affected records
        res = super().write(vals)

        # Determine whether we need to recompute analytic_distribution:
        # Recompute when partner_id or product_id is changed in this write,
        # or when analytic_distribution not present but other relevant fields changed.
        trigger_keys = {'partner_id', 'product_id'}
        # If the write explicitly sets analytic_distribution, then assume caller handled it.
        if 'analytic_distribution' in vals:
            return res

        # If none of the trigger keys are in vals, we still might want to update if context demands it.
        # For safety, only recompute when partner/product changed or when explicitly forced via context.
        do_recompute = bool(set(vals.keys()) & trigger_keys) or bool(
            self.env.context.get('force_recompute_analytic_distribution'))

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
                if dist != (rec.analytic_distribution or {}):
                    # write without raising validation
                    rec.write({'analytic_distribution': dist})
            except Exception:
                _logger.exception("Error recomputing analytic_distribution for account.move.line id %s during write",
                                  rec.id)

        return res

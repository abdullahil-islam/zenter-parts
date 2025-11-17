# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """Validate partner registration status before sending any email"""
        for wizard in self:
            # Get the records being emailed
            if wizard.model and wizard.res_ids:
                # Ensure res_ids is a proper list of integers
                res_ids = wizard.res_ids
                if isinstance(res_ids, str):
                    import ast
                    res_ids = ast.literal_eval(res_ids)
                elif not isinstance(res_ids, list):
                    res_ids = [res_ids]

                records = self.env[wizard.model].browse(res_ids)

                if 'partner_id' in records[0]._fields:
                    for record in records:
                        # Check if record has partner_id field
                        if record.partner_id:
                            if not record.partner_id.registration_status and (record.partner_id.is_registered_customer or record.partner_id.is_registered_supplier):
                                raise ValidationError(_(
                                    'Cannot send email to %s. Partner registration is not completed.'
                                ) % record.partner_id.name)

                        # Check for partner_ids field (multiple partners)
                        partner_ids = record.partner_id
                        if 'partner_ids' in record._fields:
                            partner_ids = record.partner_ids
                        if partner_ids:
                            unregistered = partner_ids.filtered(
                                lambda p: not p.registration_status and (p.is_registered_customer or p.is_registered_supplier)
                            )
                            if unregistered:
                                raise ValidationError(_(
                                    'Cannot send email. The following partners are not registered: %s'
                                ) % ', '.join(unregistered.mapped('name')))

            # Check recipient partners directly in composer
            if wizard.partner_ids:
                unregistered = wizard.partner_ids.filtered(
                    lambda p: not p.registration_status and (p.is_registered_customer or p.is_registered_supplier)
                )
                if unregistered:
                    raise ValidationError(_(
                        'Cannot send email. The following partners are not registered: %s'
                    ) % ', '.join(unregistered.mapped('name')))

        return super(MailComposer, self)._action_send_mail(auto_commit=auto_commit)


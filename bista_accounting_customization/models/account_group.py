from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountGroup(models.Model):
    _inherit = 'account.group'

    explicit_account_codes = fields.Char(
        string="Explicit Account Codes",
        help="Comma-separated list of account codes that should be explicitly assigned to this group, "
             "bypassing prefix range matching. Example: 100100,100200,100300"
    )

    @api.constrains('explicit_account_codes', 'company_id')
    def _check_explicit_codes_uniqueness(self):
        for group in self:
            if not group.explicit_account_codes:
                continue

            # Parse and clean codes
            codes = [
                code.strip()
                for code in group.explicit_account_codes.split(',')
                if code.strip()
            ]

            if not codes:
                continue

            # Check for duplicates within the same field
            if len(codes) != len(set(codes)):
                duplicates = [code for code in codes if codes.count(code) > 1]
                raise ValidationError(_(
                    "Duplicate account codes found within the same group '%(group)s': %(codes)s",
                    group=group.name,
                    codes=', '.join(set(duplicates))
                ))

            # Check for duplicates across other groups in same company
            other_groups = self.search([
                ('id', '!=', group.id),
                ('company_id', '=', group.company_id.id),
                ('explicit_account_codes', '!=', False),
            ])

            for other_group in other_groups:
                other_codes = [
                    code.strip()
                    for code in other_group.explicit_account_codes.split(',')
                    if code.strip()
                ]
                conflicts = set(codes) & set(other_codes)
                if conflicts:
                    raise ValidationError(_(
                        "Account code(s) %(codes)s already exist in group '%(other_group)s'. "
                        "Each account code can only be explicitly assigned to one group.",
                        codes=', '.join(conflicts),
                        other_group=other_group.name
                    ))

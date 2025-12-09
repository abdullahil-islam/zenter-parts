# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class ResConfigSettings(models.TransientModel):
    """
    Add extra fields in the settings.
    """
    _inherit = 'res.config.settings'

    hide_price = fields.Boolean(
        string='Hide Price',
        config_parameter='website_hide_button.hide_price',
        help="If enabled, the price of product will not be visible to guest users in website"
    )
    hide_type = fields.Selection(
        [('all', 'All Websites'), ('selected', 'Selected Websites')],
        string='Apply To',
        config_parameter='website_hide_button.hide_type',
        default='all',
        help="Choose whether to apply the hide settings to all websites or only selected websites"
    )
    # Changed from Many2many to Char to store comma-separated website IDs
    website_ids = fields.Many2many(
        'website',
        string='Websites',
        help="Select the websites where price and cart should be hidden for guest users"
    )

    def set_values(self):
        """Method for setting the parameters"""
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        params.set_param('website_hide_button.hide_price', self.hide_price)
        params.set_param('website_hide_button.hide_type', self.hide_type)

        # Store website_ids as comma-separated string
        website_ids_str = ','.join(map(str, self.website_ids.ids)) if self.website_ids else ''
        params.set_param('website_hide_button.website_ids', website_ids_str)

    @api.model
    def get_values(self):
        """Method for getting the parameters"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        hide_price = params.get_param('website_hide_button.hide_price', default=False)
        hide_type = params.get_param('website_hide_button.hide_type', default='all')
        website_ids_str = params.get_param('website_hide_button.website_ids', default='')

        # Convert string to list of integers
        website_ids = []
        if website_ids_str:
            try:
                website_ids = [int(x) for x in website_ids_str.split(',') if x]
            except ValueError:
                website_ids = []

        res.update({
            'hide_price': hide_price,
            'hide_type': hide_type,
            'website_ids': [(6, 0, website_ids)],
        })
        return res

    @api.onchange('hide_type')
    def _onchange_hide_type(self):
        """Clear website_ids when changing to 'all' using Command format"""
        if self.hide_type == 'all':
            self.website_ids = [Command.clear()]

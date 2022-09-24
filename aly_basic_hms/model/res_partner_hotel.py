# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_partner(models.Model):
    _name = 'res.partner.hotel'

    hotel_id = fields.Many2one('res.partner', string='Hotel')
    occupancy_rate = fields.Integer('Occupancy Rate')
    occupancy_rate_date = fields.Date('Date', required=True, default=fields.Datetime.now)

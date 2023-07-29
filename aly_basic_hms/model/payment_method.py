# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class PaymentMethods(models.Model):
    _name = 'payment.method'
    _description = 'Payment Method'

    name = fields.Char("Payment Method", required=True)
    is_include_fees = fields.Boolean(string='With Fees?', default=False, required=False, tracking=False)
    fees_percentage = fields.Float(string='Fees %', default=0.0)

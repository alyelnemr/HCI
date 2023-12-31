# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BankFees(models.Model):
    _name = 'bank.fees'
    _description = 'Bank Fees'

    name = fields.Char('Payment Method Name')
    bank_fees_percentage = fields.Float(string="Bank Fees Percentage", default=.05)
    bank_fees_account = fields.Many2one(comodel_name='account.account', string='Bank Fees default Account')
    company_id = fields.Many2one(comodel_name='res.company', readonly=True, required=True)

    @api.constrains('bank_fees_percentage')
    def _bank_fees(self):
        for rec in self:
            if rec.bank_fees_percentage < 0:
                raise ValidationError(_("You are not allowed to select a negative value"))

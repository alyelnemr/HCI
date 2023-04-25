# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('amount', 'journal_id_type', 'journal_id_select', 'payment_date')
    def _compute_bank_fees(self):
        self.bank_fees_amount = 0
        self.is_bank_fees = False
        self.total_amount_with_fees = self.amount
        self.journal_id = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)
        if self.amount and self.journal_id_select == 'bank' and self.env.company.aly_enable_bank_fees:
            self.is_bank_fees = True
            self.bank_fees_amount = self.amount * self.env.company.aly_bank_fees_percentage
            self.total_amount_with_fees = self.amount + self.bank_fees_amount
            self.journal_id = self.env['account.journal'].search([
                ('type', '=', 'bank'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

    is_bank_fees = fields.Boolean(default=False)
    bank_fees_amount = fields.Monetary(string="Bank Fees", compute='_compute_bank_fees', store=False)
    total_amount_with_fees = fields.Monetary(string="Total Amount with Fees", compute='_compute_bank_fees', store=False)
    journal_id_select = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank'),
    ], string="Journal", default='cash')
    journal_id = fields.Many2one('account.journal', store=True, readonly=False)
    journal_id_type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], related="journal_id.type")

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        res['bank_fees_amount'] = self.bank_fees_amount
        res['is_bank_fees'] = self.is_bank_fees
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
        res['bank_fees_amount'] = self.bank_fees_amount
        res['is_bank_fees'] = self.is_bank_fees
        return res

    def action_create_payments(self):
        for rec in self:
            if rec.bank_fees_amount < 0:
                raise ValidationError(_("You are not allowed to select a negative value"))
            if rec.bank_fees_amount > 0 and not rec.env.company.aly_bank_fees_account:
                raise ValidationError(_("Please set bank charge account in company screen."))
        return super(AccountPaymentRegister, self).sudo().action_create_payments()

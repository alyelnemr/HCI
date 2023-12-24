# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    is_bank_fees = fields.Boolean(string='Is Bank Fees', default=False, required=False)
    bank_fees_amount = fields.Monetary(string="Bank Fees")
    total_amount_with_fees = fields.Monetary(string="Total Amount with Fees", compute='_compute_bank_fees', store=False)
    journal_id_select = fields.Char(string="Payment Method", required=False)
    pay_method_id = fields.Many2one(comodel_name='payment.method', String='Journal', required=True)
    bank_fees_id = fields.Many2one(comodel_name='bank.fees', string='Payment Method', domain="[('company_id', '=', company_id)]")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        # "function super for adding lines of bank charge payments"
        res = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.bank_fees_amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.bank_fees_amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        payment_display_name = self._prepare_payment_display_name()

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name[
                '%s-%s' % (self.payment_type, self.partner_type)],
            self.bank_fees_amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        currency_id = self.currency_id.id
        debit = {
            'name': default_line_name,
            'date_maturity': self.date,
            'amount_currency': liquidity_amount_currency,
            'currency_id': currency_id,
            'debit': liquidity_balance,
            'credit': 0,
            'partner_id': self.partner_id.id,
            # 'account_id':  self.outstanding_account_id.id,
            'account_id': self.bank_fees_id.bank_fees_account.id,
        },
        credit = {
            'name': default_line_name,
            'date_maturity': self.date,
            'amount_currency': -liquidity_amount_currency,
            'currency_id': currency_id,
            'debit': 0,
            'credit': liquidity_balance,
            'partner_id': self.partner_id.id,
            'account_id': self.bank_fees_id.bank_fees_account.id,
            # 'account_id': self.journal_id.default_account_id.id,

        },
        if self.is_bank_fees and self.bank_fees_amount:
            charge_list = []
            charge_list.extend(debit)
            charge_list.extend(credit)
            charge_list.extend(res)
            res = charge_list
        return res

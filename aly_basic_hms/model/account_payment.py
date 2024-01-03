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
            # 'account_id': self.destination_account_id.id,
            'account_id': self.journal_id.default_account_id.id,
            # 'account_id': self.bank_fees_id.bank_fees_account.id,
        },
        credit = {
            'name': default_line_name,
            'date_maturity': self.date,
            'amount_currency': -liquidity_amount_currency,
            'currency_id': currency_id,
            'debit': 0,
            'credit': liquidity_balance,
            'partner_id': self.partner_id.id,
            # 'account_id': self.destination_account_id.id,
            # 'account_id': self.journal_id.default_account_id.id,
            'account_id': self.bank_fees_id.bank_fees_account.id,
        },
        if self.is_bank_fees and self.bank_fees_amount:
            charge_list = []
            charge_list.extend(debit)
            charge_list.extend(credit)
            charge_list.extend(res)
            res = charge_list
        return res

    def _synchronize_from_moves(self, changed_fields):
        # "overriden original function to add some condition for bank charge payments"
        for rec in self:
            if self.env.company.aly_enable_bank_fees:
                if self._context.get('skip_account_move_synchronization'):
                    return

                for pay in self.with_context(skip_account_move_synchronization=True):
                    # After the migration to 14.0, the journal entry could be shared between the account.payment and the
                    # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
                    if pay.move_id.statement_line_id:
                        continue

                    move = pay.move_id
                    move_vals_to_write = {}
                    payment_vals_to_write = {}

                    if 'journal_id' in changed_fields:
                        if pay.journal_id.type not in ('bank', 'cash'):
                            raise UserError(_("A payment must always belongs to a bank or cash journal."))

                    if 'line_ids' in changed_fields:
                        all_lines = move.line_ids
                        liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                        if len(liquidity_lines) != 1 and not self.env.company.aly_enable_bank_fees:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must"
                                "include one and only one outstanding payments/receipts account.",
                                move.display_name,
                            ))

                        if len(counterpart_lines) != 1 and not self.env.company.aly_enable_bank_fees:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must"
                                "include one and only one receivable/payable account (with an exception of "
                                "internal transfers).",
                                move.display_name,
                            ))
                        if writeoff_lines and len(writeoff_lines.account_id) != 1 and not self.env.company.aly_enable_bank_fees:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, "
                                "all optional journal items must share the same account.",
                                move.display_name,
                            ))

                        if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must "
                                "share the same currency.",
                                move.display_name,
                            ))
                        """updated this warning message"""
                        if any(line.partner_id != all_lines[0].partner_id for line in
                               all_lines):
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must "
                                "share the same partner.",
                                move.display_name,
                            ))

                        counterpart = counterpart_lines.filtered(
                            lambda l: l.account_id.user_type_id.type in ('payable', 'receivable'))
                        for rec in counterpart:
                            counterpart = rec
                            break
                        if not pay.is_internal_transfer:
                            if counterpart.account_id.user_type_id.type == 'receivable':
                                payment_vals_to_write['partner_type'] = 'customer'
                            else:
                                payment_vals_to_write['partner_type'] = 'supplier'

                        for line in liquidity_lines:
                            liquidity_amount = line.amount_currency

                        move_vals_to_write.update({
                            'currency_id': liquidity_lines.currency_id.id,
                            'partner_id': liquidity_lines.partner_id.id,
                        })
                        payment_vals_to_write.update({
                            'amount': abs(liquidity_amount),
                            'currency_id': liquidity_lines.currency_id.id,
                            'destination_account_id': counterpart.account_id.id,
                            'partner_id': liquidity_lines.partner_id.id,
                        })
                        if liquidity_amount > 0.0:
                            payment_vals_to_write.update({'payment_type': 'inbound'})
                        elif liquidity_amount < 0.0:
                            payment_vals_to_write.update({'payment_type': 'outbound'})

                    move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
                    pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))
            else:
                return super(AccountPayment, self)._synchronize_from_moves(changed_fields)

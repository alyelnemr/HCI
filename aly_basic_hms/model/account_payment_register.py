# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('amount', 'journal_id_type', 'journal_id_select', 'payment_date')
    def _compute_bank_fees(self):
        self.bank_fees_amount = 0
        self.is_bank_fees = False
        self.total_amount_with_fees = self.amount
        if not self.journal_id:
            self.journal_id = self.env['account.journal'].search([
                        ('type', '=', 'cash'),
                        ('company_id', '=', self.company_id.id),
                    ], limit=1)
        if self.amount and self.journal_id_select in ('paypal', 'stripe'):
            self.is_bank_fees = True
            percentage = .03 if self.journal_id_select == 'stripe' else .05
            self.bank_fees_amount = self.amount * percentage
            self.total_amount_with_fees = self.amount + self.bank_fees_amount
            if not self.journal_id:
                self.journal_id = self.env['account.journal'].search([
                    ('type', '=', 'bank'),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)

    def _get_default_journal(self):
        current = self.env['payment.method'].search([], limit=1)
        return current

    is_bank_fees = fields.Boolean(default=False)
    bank_fees_amount = fields.Monetary(string="Bank Fees", compute='_compute_bank_fees', store=False)
    total_amount_with_fees = fields.Monetary(string="Total Amount with Fees", compute='_compute_bank_fees', store=False)
    journal_id_select = fields.Many2one(comodel_name='payment.method', String='Journal', required=True, default=lambda self: self._get_default_journal())
    # journal_id_select = fields.Selection([
    #     ('cash', 'Cash'),
    #     ('bank', 'Bank'),
    #     ('paypal', 'Paypal'),
    #     ('stripe', 'Stripe'),
    #     ('wise', 'Wise Bank'),
    #     ('pos', 'Hotel POS'),
    # ], string="Journal", default='cash')
    journal_id = fields.Many2one('account.journal', store=True, readonly=False)
    journal_id_type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], related="journal_id.type")
    is_insurance_patient = fields.Boolean(default=False)

    def _post_payments(self, to_process, edit_mode=False):
        """ Post the newly created payments.

        :param to_process:  A list of python dictionary, one for each payment to create, containing:
                            * create_vals:  The values used for the 'create' method.
                            * to_reconcile: The journal items to perform the reconciliation.
                            * batch:        A python dict containing everything you want about the source journal items
                                            to which a payment will be created (see '_get_batches').
        :param edit_mode:   Is the wizard in edition mode.
        """
        payments = self.env['account.payment']
        for vals in to_process:
            payments |= vals['payment']
        payments.sudo().action_post()

    def _reconcile_payments(self, to_process, edit_mode=False):
        """ Reconcile the payments.

        :param to_process:  A list of python dictionary, one for each payment to create, containing:
                            * create_vals:  The values used for the 'create' method.
                            * to_reconcile: The journal items to perform the reconciliation.
                            * batch:        A python dict containing everything you want about the source journal items
                                            to which a payment will be created (see '_get_batches').
        :param edit_mode:   Is the wizard in edition mode.
        """
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        for vals in to_process:
            payment_lines = vals['payment'].line_ids.filtered_domain(domain)
            lines = vals['to_reconcile']

            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .sudo().reconcile()

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments

    def _create_payment_vals_from_wizard(self):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        res['bank_fees_amount'] = self.bank_fees_amount
        res['total_amount_with_fees'] = self.total_amount_with_fees
        res['is_bank_fees'] = self.is_bank_fees
        res['journal_id_select'] = self.journal_id_select
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
        res['bank_fees_amount'] = self.bank_fees_amount
        res['total_amount_with_fees'] = self.total_amount_with_fees
        res['is_bank_fees'] = self.is_bank_fees
        return res

    def action_create_payments(self):
        for rec in self:
            if rec.bank_fees_amount < 0:
                raise ValidationError(_("You are not allowed to select a negative value"))
            # if rec.bank_fees_amount > 0 and not rec.env.company.aly_bank_fees_account:
            #     raise ValidationError(_("Please set bank charge account in company screen."))
        payments = self.with_user(SUPERUSER_ID)._create_payments()

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move_id = False

        if self._context.get('active_model') == 'account.move':
            move_id = self.env['account.move'].browse(self._context.get('active_ids', []))
        elif self._context.get('active_model') == 'account.move.line':
            lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
            if lines:
                move_id = lines[0].move_id

        res['journal_id_select'] = move_id.payment_method_fees
        res['is_insurance_patient'] = move_id.is_insurance_patient
        return res

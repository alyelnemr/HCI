from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    @api.onchange('patient_id', 'partner_id', 'amount_tax')
    def onchange_readonly(self):
        for rec in self:
            rec.is_readonly_lines = not self.env.user.has_group('aly_basic_hms.aly_group_medical_manager')

    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    is_readonly_lines = fields.Boolean(string='Is Readonly Lines', default=False, store=False,
                                       compute=onchange_readonly)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    treating_physician_ids = fields.Many2many('medical.physician', string='Treating Physicians',
                                              related='patient_id.treating_physician_ids', required=False)
    bank_fees_amount = fields.Monetary(string="Bank Fees")
    payment_method_fees = fields.Selection([('bank', 'Bank'), ('cash', 'Cash')],
                                           required=True, default='cash', string="Payment Method")

    def _move_autocomplete_invoice_lines_values(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        '''
        self.ensure_one()

        for line in self.line_ids.filtered(lambda l: not l.display_type):
            analytic_account = line._cache.get('analytic_account_id')

            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line._origin:
                line.account_id = self.journal_id.default_account_id
                # line.account_id = line._get_computed_account() or self.journal_id.default_account_id
            if line.product_id and not line._cache.get('name'):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            if line.partner_id != self.partner_id.commercial_partner_id:
                line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = self.currency_id
            if analytic_account:
                line.analytic_account_id = analytic_account

        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

        values = self._convert_to_write(self._cache)
        values.pop('invoice_line_ids', None)
        return values

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute(
            'select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal), sum(line.quantity) * max(line.price_unit) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.sorting_rank, categ.name order by categ.sorting_rank' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group

    def unlink_force(self):
        for move in self:
            if move.posted_before and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete an entry which has been posted once."))
        self.line_ids.unlink()
        return super(AccountMoveForDiscount, self).unlink()

    @api.model
    def _search_default_journal(self, journal_types):
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types)]

        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            if self._context.get('active_model') == 'sale.order':
                sale_order = self.env['sale.order'].browse(self._context.get('active_id'))
                if sale_order.patient_id and sale_order.patient_id.is_insurance:
                    domain_insurance = [('company_id', '=', company_id), ('type', 'in', journal_types),
                                        ('is_insurance_journal', '=', True)]
                    journal = self.env['account.journal'].search(domain_insurance, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal

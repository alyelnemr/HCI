
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    treating_physician_ids = fields.Many2many('medical.physician',string='Treating Physicians',related='patient_id.treating_physician_ids', required=False)

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute('select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal), sum(line.quantity) * max(line.price_unit) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.sorting_rank, categ.name order by categ.sorting_rank' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group

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
                    domain_insurance = [('company_id', '=', company_id), ('type', 'in', journal_types), ('is_insurance_journal', '=', True)]
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

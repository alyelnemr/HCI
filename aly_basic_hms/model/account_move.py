
from odoo import api, fields, models, _


class ProductCategorySorting(models.Model):
    _inherit = "product.category"

    sorting_rank = fields.Integer(string='Sorting Rank', default=100)


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    @api.depends('discount_total')
    def onchange_age(self):
        discount_amount = 0
        discount_amount_untaxed = 0
        amount_untaxed = 0
        amount_total = 0
        for rec in self:
            if rec.amount_total:
                # amount_total = (rec.amount_untaxed * rec.discount_total / 100)
                amount_total = 0 # rec.amount_total
                discount_amount = 0
                not_discount_amount = 0
                first_subtotal = 0
                for line in rec.line_ids:
                    amount_total += (line.price_unit * line.quantity) if line.debit <= 0 else 0
                    discount_amount += ((line.price_unit * line.quantity) * rec.discount_total / 100) if (line.price_unit * line.quantity) > 0 else 0
                    line.with_context({'check_move_validity': False}).discount = rec.discount_total
                for line in rec.line_ids:
                    if line.product_id.categ_id.name in ['Prosthetics', 'Disposables', 'Discounts)']:
                        first_subtotal = (line.price_unit * line.quantity)
                        not_discount_amount += line.price_subtotal - first_subtotal if (line.price_subtotal - first_subtotal) > 0 else (first_subtotal - line.price_subtotal)
                        line.with_context({'check_move_validity': False}).discount = 0
                for line in rec.line_ids:
                    if line.debit > 0 and rec.discount_total > 0:
                        discount_diff = round((discount_amount - not_discount_amount), 2)
                        line.discount = ((discount_amount - not_discount_amount) / amount_total) * 100 if discount_diff >= 1 else 0
                        x= line.discount
                rec._compute_amount()
                rec._compute_invoice_taxes_by_group()

    discount_total = fields.Float(string='Total Discount %')
    discount_amount = fields.Monetary(compute=onchange_age,string="Discount", store=True)
    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute('select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.name' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group

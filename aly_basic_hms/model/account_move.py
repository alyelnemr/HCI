
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductCategorySorting(models.Model):
    _inherit = "product.category"

    sorting_rank = fields.Integer(string='Sorting Rank', default=100)


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute('select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.sorting_rank, categ.name order by categ.sorting_rank' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        super(SaleOrderLine, self)._onchange_discount()
        for record in self:
            allow_discount = self.env['ir.model.access'].check_groups("product.group_discount_per_so_line")
            if record.product_id and record.order_partner_id.id and allow_discount:
                user_lines = self.env['user.partner.discount'].sudo().search([('partner_id', '=', record.order_partner_id.id),('user_id', '=', self.env.user.id)])
                if user_lines:
                    partner_discount_obj = user_lines[0]
                    discount = partner_discount_obj.discount
                    record.discount = discount


class SaleOrderForDiscount(models.Model):
    _inherit = 'sale.order'

    @api.depends('discount_total', 'order_line')
    def onchange_age(self):
        current_user = self.env['res.users'].sudo().browse(self.env.user.id)
        for rec in self:
            if rec.discount_total > current_user.max_allowed_discount:
                raise UserError(_('Your Maximum Allowed Discount is %s', str(current_user.max_allowed_discount)))
            if rec.amount_total > 0 and rec.discount_total > 0:
                # amount_total = (rec.amount_untaxed * rec.discount_total / 100)
                amount_total = 0
                discount_amount = 0
                for line in rec.order_line:
                    amount_total += (line.price_unit * line.product_uom_qty)
                    discount_amount += ((line.price_unit * line.product_uom_qty) * rec.discount_total / 100) if (line.price_unit * line.product_uom_qty) > 0 else 0
                    line.discount = rec.discount_total if line.product_id.categ_id.name not in ['Prosthetics', 'Medicines', 'Disposables', 'Discounts)'] else 0

    discount_total = fields.Float(string='Total Discount %', default=0.0)
    discount_amount = fields.Monetary(compute=onchange_age, string="Discount", store=True)
    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)

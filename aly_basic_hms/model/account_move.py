
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductCategorySorting(models.Model):
    _inherit = "product.category"

    sorting_rank = fields.Integer(string='Sorting Rank', default=100)


class SaleAdvancePaymentInvMedical(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection([
        ('delivered', 'Regular invoice')], string='Create Invoice', default='delivered', required=True, readonly=True,
        help="A standard invoice is issued with all the order lines ready for invoicing, \
        according to their invoicing policy (based on ordered or delivered quantity).")

    def create_invoices(self):
        result = super(SaleAdvancePaymentInvMedical, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            patient = self.env['medical.patient'].browse(order.patient_id.id)
            for inv in order.invoice_ids:
                if inv.state != 'cancel':
                    invoice = self.env['account.move'].browse(inv.id)
                    patient.invoice_id = inv.id
                    invoice.patient_id = patient.id
                    break
        return result


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.move'

    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)

    def get_quantity_subtotal(self):
        sql = self.env.cr.execute('select line.product_id, pt.name, categ.name, sum(line.quantity), max(line.price_unit), sum(line.price_subtotal), sum(line.quantity) * max(line.price_unit) from account_move move inner join account_move_line line on move.id = line.move_id inner join product_product p on line.product_id = p.id inner join product_template pt on pt.id = p.product_tmpl_id inner join product_category categ on pt.categ_id = categ.id where move.id = %s group by line.product_id, pt.name, categ.sorting_rank, categ.name order by categ.sorting_rank' % self.id)
        read_group = self.env.cr.fetchall()
        return read_group


class SaleOrderForDiscount(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total', 'amount_total', 'amount_untaxed', 'discount_total', 'order_line')
    def compute_amount_all(self):
        aly_enable_service_charge = self.env['ir.config_parameter'].sudo().get_param('aly_enable_service_charge')
        aly_service_product_id = int(self.env['ir.config_parameter'].sudo().get_param('aly_service_product_id'))
        for rec in self:
            if aly_enable_service_charge and rec.amount_total > 0:
                amount_untaxed = 0.0
                for line in rec.order_line:
                    if line.product_id.id == aly_service_product_id:
                        line.price_unit = 0
                    amount_untaxed += line.price_subtotal
                aly_service_charge_percentage = float(self.env['ir.config_parameter'].sudo().get_param('aly_service_charge_percentage'))
                rec.service_charge_amount = aly_service_charge_percentage * amount_untaxed / 100
                rec.service_untaxed_amount = amount_untaxed
                for line in rec.order_line:
                    if line.product_id.id == aly_service_product_id:
                        line.price_unit = rec.service_charge_amount

    @api.depends('discount_total', 'order_line')
    def onchange_discount(self):
        current_user = self.env['res.users'].sudo().browse(self.env.user.id)
        for rec in self:
            if rec.discount_total < 0:
                raise UserError(_('Discount % cannot be negative'))
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
    discount_amount = fields.Monetary(compute=onchange_discount, string="Discount", store=True)
    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    service_charge_amount = fields.Monetary(compute=compute_amount_all, string="Service Charge %", store=False)
    service_untaxed_amount = fields.Monetary(compute=compute_amount_all, string="Untaxed Amount", store=False)

    def update_prices(self):
        self.ensure_one()
        aly_service_product_id = int(self.env['ir.config_parameter'].sudo().get_param('aly_service_product_id'))
        for line in self.order_line:
            if line.product_id.id == aly_service_product_id:
                line.price_unit = 0
        res = super().update_prices()
        aly_service_charge_percentage = float(self.env['ir.config_parameter'].sudo().get_param('aly_service_charge_percentage'))
        for line in self.order_line:
            if line.product_id.id == aly_service_product_id:
                line.price_unit = aly_service_charge_percentage * self.amount_untaxed / 100
        return res

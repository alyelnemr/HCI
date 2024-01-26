from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class SaleOrderForDiscount(models.Model):
    _inherit = 'sale.order'

    @api.model
    def default_get(self, vals):
        defaults = super(SaleOrderForDiscount, self).default_get(vals)
        for rec in self:
            if rec.patient_id and rec.patient_id.is_insurance and not self.env.user.has_group(
                    'aly_basic_hms.aly_group_insurance'):
                raise UserError(_("You don't have permission to access insurance invoice from patient"))
            if rec.patient_id and not self.env.user.has_group('aly_basic_hms.aly_group_outpatient'):
                raise UserError(_("You don't have permission to access this invoice"))
        return defaults

    @api.depends('order_line.price_total', 'amount_total', 'amount_untaxed', 'discount_total', 'order_line')
    def compute_amount_all(self):
        for rec in self:
            if rec.patient_id and rec.patient_id.is_insurance and not self.env.user.has_group(
                    'aly_basic_hms.aly_group_insurance'):
                raise UserError(_("You don't have permission to access insurance invoice from patient"))
            aly_enable_service_charge = rec.company_id.aly_enable_service_charge
            if aly_enable_service_charge and rec.amount_total > 0 and rec.patient_id.clinic_id.is_hospital:
                aly_service_product_id = int(rec.company_id.aly_service_product_id.id)
                amount_untaxed = 0.0
                for line in rec.order_line:
                    if line.product_id.id == aly_service_product_id:
                        line.price_unit = 0
                    amount_untaxed += (line.price_unit * line.product_uom_qty) if line.product_id.categ_id.name not in [
                        'Prosthetics', 'Medicines', 'Disposables', 'Discounts', 'Service Charge Services'] else 0
                aly_service_charge_percentage = float(rec.company_id.aly_service_charge_percentage)
                rec.service_charge_amount = aly_service_charge_percentage * amount_untaxed / 100
                rec.service_untaxed_amount = amount_untaxed
                for line in rec.order_line:
                    if line.product_id.id == aly_service_product_id:
                        line.price_unit = rec.service_charge_amount
            else:
                rec.service_charge_amount = 0
                rec.service_untaxed_amount = rec.amount_untaxed - rec.service_charge_amount

    @api.depends('service_charge_amount')
    def compute_service_untaxed_amount(self):
        for rec in self:
            rec.service_untaxed_amount = rec.amount_untaxed - rec.service_charge_amount

    @api.depends('discount_total', 'order_line')
    def onchange_discount(self):
        current_user = self.env['res.users'].sudo().browse(self.env.user.id)
        for rec in self:
            if rec.discount_total < 0:
                raise UserError(_('Discount % cannot be negative'))
            if rec.discount_total > current_user.max_allowed_discount:
                raise UserError(_('Your Maximum Allowed Discount is %s', str(current_user.max_allowed_discount)))
            if rec.amount_total > 0 and rec.discount_total > 0:
                amount_total = 0
                discount_amount = 0
                for line in rec.order_line:
                    amount_total += (line.price_unit * line.product_uom_qty)
                    discount_amount += ((line.price_unit * line.product_uom_qty) * rec.discount_total / 100) if (
                                                                                                                        line.price_unit * line.product_uom_qty) > 0 else 0
                    line.discount = rec.discount_total if line.product_id.categ_id.name not in ['Prosthetics',
                                                                                                'Medicines',
                                                                                                'Disposables',
                                                                                                'Discounts',
                                                                                                'Service Charge Services'] else 0

    @api.onchange('patient_id', 'partner_id', 'amount_tax')
    def onchange_readonly(self):
        for rec in self:
            rec.is_readonly_lines = not self.env.user.has_group('aly_basic_hms.aly_group_medical_manager')

    is_readonly_lines = fields.Boolean(string='Is Readonly Lines', default=False, store=False,
                                       compute=onchange_readonly)
    discount_total = fields.Float(string='Total Discount %', default=0.0)
    discount_amount = fields.Monetary(compute=onchange_discount, string="Discount", store=True)
    is_insurance = fields.Boolean(string='Is Insurance', default=False, required=False)
    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    service_charge_amount = fields.Monetary(compute=compute_amount_all, string="Service Charge %", store=False)
    service_untaxed_amount = fields.Monetary(compute=compute_service_untaxed_amount, string="Untaxed Amount",
                                             store=False)
    treating_physician_ids = fields.Many2many('medical.physician', string='Treating Physicians',
                                              related='patient_id.treating_physician_ids', required=False)

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderForDiscount, self)._prepare_invoice()
        invoice_vals['patient_id'] = self.patient_id.id
        return invoice_vals

    def get_service_charge_service(self):
        service_id = False
        if self.company_id.aly_enable_service_charge and self.patient_id.clinic_id.is_hospital:
            service_id = self.order_line.filtered_domain(
                [('product_id', '=', self.company_id.aly_service_product_id.id)])
        return service_id

    def update_prices(self):
        self.ensure_one()
        line_service_charge = self.get_service_charge_service()
        if line_service_charge:
            line_service_charge.price_unit = 0
        res = super().update_prices()
        medicine_prod_cat = self.env['ir.config_parameter'].sudo().get_param('medicine.product_category')
        domain = [
            ('product_id.categ_id.name', '=', medicine_prod_cat)
        ]
        medicines_lines = self.order_line.filtered_domain(domain)
        if medicines_lines:
            medicines_lines.write({
                'price_unit': 0
            })
        if self.company_id.aly_enable_service_charge and line_service_charge and self.patient_id.clinic_id.is_hospital:
            line_service_charge.price_unit = self.company_id.aly_service_charge_percentage * self.amount_untaxed / 100
        return res

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

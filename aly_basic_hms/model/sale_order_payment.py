
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


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
                    patient.invoice_id = inv.id
                    inv.patient_id = patient.id
                    inv.action_post()
                    break
        return result

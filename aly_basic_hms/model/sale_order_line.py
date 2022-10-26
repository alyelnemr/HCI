
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            lang = get_lang(self.env, line.order_id.partner_id.lang).code
            product = self.product_id.with_context(
                lang=lang,
                partner=line.order_id.partner_id,
                quantity=line.product_uom_qty,
                date=line.order_id.date_order,
                pricelist=line.order_id.pricelist_id.id,
                uom=line.product_uom.id
            )
            price_unit = product._get_tax_included_unit_price(
                line.order_id.company_id,
                line.order_id.currency_id,
                line.order_id.date_order,
                'sale',
                fiscal_position=line.order_id.fiscal_position_id,
                product_price_unit=line._get_display_price(product),
                product_currency=line.order_id.currency_id
            )
            price = price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'price_unit': price_unit
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

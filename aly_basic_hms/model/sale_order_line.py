from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def unlink(self):
        for rec in self:
            if rec.product_id == self.company_id.aly_service_product_id:
                raise UserError('You cannot remove the service charge.')
        return super(SaleOrderLine, self).unlink()
    #
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the SO line.
    #     """
    #     for line in self:
    #         lang = get_lang(self.env, line.order_id.partner_id.lang).code
    #         product = line.product_id.with_context(
    #             lang=lang,
    #             partner=line.order_id.partner_id,
    #             quantity=line.product_uom_qty,
    #             date=line.order_id.date_order,
    #             pricelist=line.order_id.pricelist_id.id,
    #             uom=line.product_uom.id
    #         )
    #         price_unit = product._get_tax_included_unit_price(
    #             line.order_id.company_id,
    #             line.order_id.currency_id,
    #             line.order_id.date_order,
    #             'sale',
    #             fiscal_position=line.order_id.fiscal_position_id,
    #             product_price_unit=line._get_display_price(product),
    #             product_currency=line.order_id.currency_id
    #         )
    #         price = price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
    #                                         product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #             'price_unit': price_unit
    #         })
    #         if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
    #                 'account.group_account_manager'):
    #             line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
    #
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    # def _compute_amount(self):
    #     """
    #     Compute the amounts of the SO line.
    #     """
    #     for line in self:
    #         price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
    #         taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
    #                                         product=line.product_id, partner=line.order_id.partner_shipping_id)
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #             'price_unit': price,
    #         })
    #         if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
    #                 'account.group_account_manager'):
    #             line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
    #
    # @api.onchange('product_id')
    # def product_id_change(self):
    #     if not self.product_id:
    #         return
    #     valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
    #     # remove the is_custom values that don't belong to this template
    #     for pacv in self.product_custom_attribute_value_ids:
    #         if pacv.custom_product_template_attribute_value_id not in valid_values:
    #             self.product_custom_attribute_value_ids -= pacv
    #
    #     # remove the no_variant attributes that don't belong to this template
    #     for ptav in self.product_no_variant_attribute_value_ids:
    #         if ptav._origin not in valid_values:
    #             self.product_no_variant_attribute_value_ids -= ptav
    #
    #     vals = {}
    #     if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
    #         vals['product_uom'] = self.product_id.uom_id
    #         vals['product_uom_qty'] = self.product_uom_qty or 1.0
    #
    #     lang = get_lang(self.env, self.order_id.partner_id.lang).code
    #     product = self.product_id.with_context(
    #         lang=lang,
    #         partner=self.order_id.partner_id,
    #         quantity=vals.get('product_uom_qty') or self.product_uom_qty,
    #         date=self.order_id.date_order,
    #         pricelist=self.order_id.pricelist_id.id,
    #         uom=self.product_uom.id
    #     )
    #
    #     vals.update(name=self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product))
    #
    #     self._compute_tax_id()
    #
    #     if self.order_id.pricelist_id and self.order_id.partner_id:
    #         vals['price_unit'] = product._get_tax_included_unit_price(
    #             self.company_id,
    #             self.order_id.currency_id,
    #             self.order_id.date_order,
    #             'sale',
    #             fiscal_position=self.order_id.fiscal_position_id,
    #             product_price_unit=self._get_display_price(product),
    #             product_currency=self.order_id.currency_id
    #         )
    #     self.write(vals)
    #
    #     title = False
    #     message = False
    #     result = {}
    #     warning = {}
    #     if product.sale_line_warn != 'no-message':
    #         title = _("Warning for %s", product.name)
    #         message = product.sale_line_warn_msg
    #         warning['title'] = title
    #         warning['message'] = message
    #         result = {'warning': warning}
    #         if product.sale_line_warn == 'block':
    #             self.product_id = False
    #
    #     return result

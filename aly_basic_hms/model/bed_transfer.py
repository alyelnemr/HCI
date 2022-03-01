# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BedTransfer(models.Model):
    _name = 'bed.transfer'

    def _get_accommodation_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('accommodation.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        return [('categ_id', '=', prod_cat_obj.id)]

    @api.constrains('accommodation_qty')
    def date_constrains(self):
        for rec in self:
            if rec.accommodation_qty <= 0:
                raise ValidationError(_('Accommodation Qty must be greater than or equal Admission Date...'))

    name = fields.Char("Name")
    accommodation_service = fields.Many2one('product.product',
                                            string='Accommodation',
                                            domain=lambda self: self._get_accommodation_product_category_domain(), required=True)
    accommodation_qty = fields.Integer(string="Extra Accommodation Qty", default=1)
    reason = fields.Text(string='Reason')
    inpatient_id = fields.Many2one('medical.inpatient.registration', string='Inpatient Id')

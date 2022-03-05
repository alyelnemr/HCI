# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedicalInpatientAccommodation(models.Model):
    _name = 'medical.inpatient.accommodation'

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
    admission_type = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU'), ('care', 'Intermediate Care Unit')],
                                      required=True, default='standard', string="Admission Type")
    accommodation_service = fields.Many2one('product.product',
                                            string='Accommodation Service',
                                            domain=lambda self: self._get_accommodation_product_category_domain(), required=True)
    accommodation_qty = fields.Integer(string="Qty", default=1)
    reason = fields.Text(string='Reason')
    inpatient_id = fields.Many2one('medical.inpatient.registration', string='Inpatient Id')

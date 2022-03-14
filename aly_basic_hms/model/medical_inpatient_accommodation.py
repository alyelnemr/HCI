# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedicalInpatientAccommodation(models.Model):
    _name = 'medical.inpatient.accommodation'
    _description = 'description'

    def _get_accommodation_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('accommodation.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    name = fields.Char("Name")
    # , ('care', 'Intermediate Care Unit')
    admission_type = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU')],
                                      required=True, default='standard', string="Admission Type")
    accommodation_service = fields.Many2one('product.product',
                                            string='Accommodation Service',
                                            domain=lambda self: self._get_accommodation_product_category_domain(), required=True)
    accommodation_qty = fields.Integer(string="Qty", default=1)
    reason = fields.Text(string='Reason')
    acc_id = fields.Many2one('medical.inpatient.acc', string='Master Accommodation ID')

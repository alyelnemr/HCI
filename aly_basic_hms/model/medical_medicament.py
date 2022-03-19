# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class medical_medicament(models.Model):
    _name = 'medical.medicament'
    _rec_name = 'product_id'
    _description = 'description'

    @api.depends('product_id')
    def onchange_product(self):
        for each in self:
            if each:
                self.qty_available = self.product_id.qty_available
                self.price = self.product_id.lst_price
            else:
                self.qty_available = 0
                self.price = 0.0

    def _get_medicine_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('medicine.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', 1), ('type', '=', 'product')]

    product_id = fields.Many2one('product.product', string='Name',
                                 domain=lambda self: self._get_medicine_product_category_domain(), required=True)
    therapeutic_action = fields.Char('Therapeutic effect', help = 'Therapeutic action')
    price = fields.Float(compute=onchange_product,string='Price',store=True)
    qty_available = fields.Integer(compute=onchange_product,string='Quantity Available',store=True)
    indications = fields.Text('Indications')
    active_component = fields.Char(string="Active Component")
    presentation = fields.Text('Presentation')
    composition = fields.Text('Composition')

    adverse_reaction = fields.Text('Adverse Reactions')
    storage = fields.Text('Storage Condition')
    notes = fields.Text('Extra Info')


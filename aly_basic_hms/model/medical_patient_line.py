from odoo import api, fields, models, _


class MedicalPatientLine(models.Model):
    _name = 'medical.patient.line'
    _description = 'Medical Patient Line'

    def _get_disposable_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('disposable.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        for obj in prod_cat_obj:
            prod_cat_obj_id = obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    name = fields.Many2one('medical.patient', 'Patient Line ID')
    patient_id = fields.Many2one('medical.patient', 'Patient ID')
    product_id = fields.Many2one('product.product', 'Disposable',
                                 domain=lambda self: self._get_disposable_product_category_domain(), required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

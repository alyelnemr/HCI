from odoo import api, fields, models, _


class MedicalAppointmentProcedure(models.Model):
    _name = 'medical.appointment.procedure'
    _description = 'Medical Appointment Procedures'

    def _get_procedure_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('procedure.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) >= 2:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', 1), ('type', '=', 'service')]

    name = fields.Many2one('medical.appointment', 'Appointment Procedure ID')
    appointment_id = fields.Many2one('medical.appointment', 'Appointment ID')
    product_id = fields.Many2one('product.product', 'Service',
                                 domain=lambda self: self._get_procedure_product_category_domain(), required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)


from odoo import fields, models


class MedicalAppointmentConsultationLine(models.Model):
    _name = 'medical.appointment.consultation.line'
    _description = ''

    def _get_examination_product_category_domain(self):
        exam_prod_cat = self.env['ir.config_parameter'].sudo().get_param('examination.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', exam_prod_cat)])
        return [('sale_ok', '=', 1), ('type', '=', 'service'), ('categ_id', '=', prod_cat_obj.id)]

    name = fields.Many2one('medical.appointment', 'Appointment ID')
    appointment_id = fields.Many2one('medical.appointment', 'Appointment ID')
    product_id = fields.Many2one('product.product', 'Service',
                                 domain=lambda self: self._get_examination_product_category_domain(), required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.user.company_id)

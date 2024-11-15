from odoo import api, fields, models, _


class MedicalAppointmentLine(models.Model):
    _name = 'medical.appointment.line'
    _description = 'Medical Appointment Medications'

    name = fields.Many2one('medical.appointment', 'Appointment Line ID')
    appointment_id = fields.Many2one('medical.appointment', 'Appointment ID')
    product_id = fields.Many2one('product.product', 'Service', domain=[('sale_ok', '=', 1), ('type', '=', 'service')],
                                 required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

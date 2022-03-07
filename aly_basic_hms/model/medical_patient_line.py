from odoo import api, fields, models, _


class MedicalPatientLine(models.Model):
    _name = 'medical.patient.line'

    name = fields.Many2one('medical.patient', 'Patient ID')
    patient_id = fields.Many2one('medical.patient', 'Patient ID')
    product_id = fields.Many2one('product.product', 'Disposable', domain=[('sale_ok', '=', 1), ('type', '=', 'consu')],
                                 required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.user.company_id)

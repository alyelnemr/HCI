from odoo import api, fields, models, _


class MedicalInpatientProcedure(models.Model):
    _name = 'medical.inpatient.procedure'
    _description = 'description'

    name = fields.Many2one('medical.inp.update.note', 'Appointment ID')
    inp_update_note_id = fields.Many2one('medical.inp.update.note', 'Update Note ID')
    product_id = fields.Many2one('product.product', 'Service', domain=[('sale_ok', '=', 1), ('type', '=', 'service')],
                                 required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.user.company_id)

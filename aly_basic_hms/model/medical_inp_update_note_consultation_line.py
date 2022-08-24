from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalInpUpdateNoteConsultationLine(models.Model):
    _name = 'medical.inp.update.note.consultation.line'
    _description = 'Medical Inpatient Update Notes Another Consultations'

    @api.constrains('quantity')
    def date_constrains(self):
        for rec in self:
            if rec.quantity < 1:
                raise ValidationError(_('Another Consultation Qty Must be greater than 1'))

    def _get_examination_product_category_domain(self):
        exam_prod_cat = self.env['ir.config_parameter'].sudo().get_param('examination.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', exam_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    name = fields.Many2one('medical.inp.update.note', 'Consultations')
    inp_update_note_id = fields.Many2one('medical.inp.update.note', 'Inpatient Update Note ID')
    product_id = fields.Many2one('product.product', 'Service',
                                 domain=lambda self: self._get_examination_product_category_domain(), required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

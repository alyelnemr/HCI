from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalInpatientMedication(models.Model):
    _name = 'medical.inpatient.medication'
    _rec_name = 'product_id'
    _description = 'Medical Inpatient Medication'

    @api.constrains('medicine_quantity')
    def date_constrains(self):
        for rec in self:
            if rec.medicine_quantity < 1:
                raise ValidationError(_('Medicine Qty Must be greater than 1'))

    def _get_medicine_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('medicine.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    @api.depends('product_id')
    def get_medicine_product_categ_id(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('medicine.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        self.categ_id_medicine = prod_cat_obj_id

    product_id = fields.Many2one('product.product', string='Medicine',
                                 domain=lambda self: self._get_medicine_product_category_domain(), required=True)
    medical_medicament_id = fields.Many2one('medical.medicament', string="Medicine (Old Don't use)", readonly=True, required=False)
    medicine_quantity = fields.Integer(string='Quantity', default=1)
    dose = fields.Integer(string='Dose')
    admin_method = fields.Selection([('iv', 'IV'), ('im', 'IM'), ('sc', 'SC'), ('oral', 'Oral'), ('local', 'Local')],
                                    string='Administration Method')
    medical_dose_unit_id = fields.Many2one('medical.dose.unit', string='Dose Unit')
    frequency = fields.Integer(string='Frequency')
    frequency_unit = fields.Selection([('hours', 'hours')], readonly=True, default='hours', string='Frequency Unit')
    notes = fields.Text(string='Notes')
    medical_inp_update_note_id = fields.Many2one('medical.inp.update.note', string='Inpatient Medications')
    medical_inpatient_registration_id = fields.Many2one('medical.inpatient.registration', string='Medication')
    medical_appointment_id = fields.Many2one('medical.appointment', string='Medications')
    medical_discharge_id = fields.Many2one('medical.appointment', string='Discharge Medication')
    categ_id_medicine = fields.Integer('Medicine Product Category ID',store=False, compute=get_medicine_product_categ_id)


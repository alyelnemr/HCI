from odoo import models, fields, api, _


class MedicalInpatientMedicationTransient(models.TransientModel):
    _name = 'medical.inpatient.medication.transient'
    _rec_name = 'medical_medicament_id'
    _description = 'Medical Inpatient Medication Transient'

    def _get_medicine_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('medicine.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    product_id = fields.Many2one('product.product', string='Medicine',
                                 domain=lambda self: self._get_medicine_product_category_domain(), required=True)
    medical_medicament_id = fields.Many2one('medical.medicament', string="Medicine (Old Don't use)", readonly=True, required=False)
    medicine_quantity = fields.Integer(string='Medicine Quantity',default=1)
    dose = fields.Float(string='Dose')
    admin_method = fields.Selection([('iv','IV'),
                                        ('im','IM'),
                                        ('sc','SC'),
                                        ('oral','Oral'),
                                        ('local','Local')],string='Administration Method')
    medical_dose_unit_id = fields.Many2one('medical.dose.unit',string='Dose Unit')
    frequency = fields.Integer(string='Frequency')
    frequency_unit = fields.Selection([('hours','hours')], readonly=True, default='hours', string='Frequency Unit')
    notes = fields.Text(string='Notes')
    medical_discharge_id = fields.Many2one('medical.inpatient.discharge.wizard',string='Discharge Medication')

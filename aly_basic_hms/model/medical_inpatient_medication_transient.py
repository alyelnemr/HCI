from odoo import models, fields, api, _


class MedicalInpatientMedicationTransient(models.TransientModel):
    _name = 'medical.inpatient.medication.transient'
    _rec_name = 'medical_medicament_id'
    _description = ''

    medical_medicament_id = fields.Many2one('medical.medicament',string='Medicine',required=True)
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

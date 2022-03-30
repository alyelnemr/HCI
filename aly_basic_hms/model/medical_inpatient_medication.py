from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalInpatientMedication(models.Model):
    _name = 'medical.inpatient.medication'
    _rec_name = 'medical_medicament_id'
    _description = 'Medical Inpatient Medication'

    @api.constrains('medicine_quantity')
    def date_constrains(self):
        for rec in self:
            if rec.medicine_quantity < 1:
                raise ValidationError(_('Medicine Qty Must be greater than 1'))

    medical_medicament_id = fields.Many2one('medical.medicament', string='Medicine', required=True)
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

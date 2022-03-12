# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class MedicalInpatientMedication(models.Model):
    _name = 'medical.inpatient.medication'
    _rec_name = 'medical_medicament_id'
    _description = 'description'

    medical_medicament_id = fields.Many2one('medical.medicament', string='Medicine', required=True)
    medicine_quantity = fields.Integer(string='Medicine Quantity', default=1)
    dose = fields.Float(string='Dose')
    admin_method = fields.Selection([('iv', 'IV'), ('im', 'IM'), ('sc', 'SC'), ('oral', 'Oral'), ('local', 'Local')],
                                    string='Administration Method')
    medical_dose_unit_id = fields.Many2one('medical.dose.unit', string='Dose Unit')
    frequency = fields.Integer(string='Frequency')
    frequency_unit = fields.Selection([('hours', 'hours')], readonly=True, default='hours', string='Frequency Unit')
    notes = fields.Text(string='Notes')
    medical_inp_update_note_id = fields.Many2one('medical.inp.update.note', string='Medication')
    medical_inpatient_update_note_id = fields.Many2one('medical.inpatient.update.note', string='Medication')
    medical_inpatient_registration_id = fields.Many2one('medical.inpatient.registration', string='Medication')
    medical_appointment_id = fields.Many2one('medical.appointment', string='Medication')
    medical_discharge_id = fields.Many2one('medical.appointment', string='Discharge Medication')

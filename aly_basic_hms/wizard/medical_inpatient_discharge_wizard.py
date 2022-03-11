# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MedicalInpatientInvoiceWizard(models.TransientModel):
    _name = 'medical.inpatient.discharge.wizard'
    _description = 'description'

    @api.depends('discharge_datetime')
    def _compute_admission_days(self):
        active_ids = self._context.get('active_ids')
        lab_req_obj = self.env['medical.inpatient.registration']
        for active_id in active_ids:
            rec = lab_req_obj.browse(active_id)
            if self.discharge_datetime:
                d2 = self.discharge_datetime.date()
                d1 = rec.admission_date
                if d1 and d2:
                    rd = d2 - d1
                    self.actual_admission_days = rd.days + 1
                    if self.discharge_datetime.date() < rec.admission_date or rd.days < 0:
                        raise UserError(_('Discharge Date Must be greater than or equal Admission Date...'))

    name = fields.Char(string="Discharge Code", readonly=True)
    discharge_datetime = fields.Datetime(string='Discharge Date Time', required=True)
    actual_admission_days = fields.Integer(compute=_compute_admission_days,string="Admission Days",store=False, default=0)
    discharge_basis = fields.Selection([('improve', 'Improvement Basis'), ('against', 'Against Medical Advice'),
                                        ('repatriation', 'Repatriation Basis')],
                                       required=True, string="Discharge Basis")
    refer_to = fields.Char(string="Refer To")
    transportation = fields.Selection([('car', 'Standard Car'), ('ambulance', 'Ambulance')],
                                      required=True, default='car', string="Transportation")
    recommendation = fields.Text(string="Recommendations")
    discharge_medication_ids = fields.One2many('medical.inpatient.medication.transient', 'medical_discharge_id',
                                               string='Discharge Medications')

    def discharge_patient(self):
        active_ids = self._context.get('active_ids')
        medical_appointment_obj = self.env['medical.inpatient.registration']
        for active_id in active_ids: 
            appointment_obj = medical_appointment_obj.browse(active_id)
            appointment_obj.is_discharged = True
            appointment_obj.discharge_datetime = self.discharge_datetime
            appointment_obj.discharge_basis = self.discharge_basis
            appointment_obj.refer_to = self.refer_to
            appointment_obj.transportation = self.transportation
            appointment_obj.recommendation = self.recommendation
            appointment_obj.state = 'discharged'
            appointment_obj.admission_days = self.actual_admission_days
            # appointment_obj.discharge_medication_ids = self.discharge_medication_ids
            discharge_medication_ids = []
            for line in self.discharge_medication_ids:
                discharge_medication_ids.append((0, 0, {
                    'medical_medicament_id': line.medical_medicament_id.id,
                    'dose': line.dose,
                    'admin_method': line.admin_method,
                    'medical_dose_unit_id': line.medical_dose_unit_id.id,
                    'frequency': line.frequency,
                    'frequency_unit': line.frequency_unit,
                    'notes': line.notes,
                }))
            appointment_obj.discharge_medication_ids = discharge_medication_ids

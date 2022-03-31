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
                    self.actual_admission_days = rd.days
                    if self.discharge_datetime.date() < rec.admission_date or rd.days < 0:
                        raise UserError(_('Discharge Date Must be greater than or equal Admission Date (%s)...', rec.admission_date))

    name = fields.Char(string="Discharge Code", readonly=True)
    discharge_datetime = fields.Datetime(string='Discharge Date Time', required=True)
    actual_admission_days = fields.Integer(compute=_compute_admission_days, string="Admission Days",store=False, default=0)
    discharge_basis = fields.Selection([('improve', 'Improvement Basis'), ('against', 'Against Medical Advice'),
                                        ('repatriation', 'Repatriation Basis'),
                                        ('referral', 'Referral Basis')], default="improve",
                                       required=True, string="Discharge Basis")
    refer_to = fields.Char(string="Refer To")
    doctor_id = fields.Many2one('medical.physician', string='Treating Physician',required=False)
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
            appointment_obj.patient_id.current_discharge_date = self.discharge_datetime
            appointment_obj.discharge_basis = self.discharge_basis
            appointment_obj.refer_to = self.refer_to
            appointment_obj.transportation = self.transportation
            appointment_obj.doctor_id = self.doctor_id
            appointment_obj.recommendation = self.recommendation
            appointment_obj.state = 'discharged'
            appointment_obj.admission_days = self.actual_admission_days
            # appointment_obj.discharge_medication_ids = self.discharge_medication_ids
            discharge_medication_ids = []
            for line in self.discharge_medication_ids:
                discharge_medication_ids.append((0, 0, {
                    'medical_medicament_id': line.medical_medicament_id.id,
                    'medicine_quantity': line.medicine_quantity,
                    'dose': line.dose,
                    'admin_method': line.admin_method,
                    'medical_dose_unit_id': line.medical_dose_unit_id.id,
                    'frequency': line.frequency,
                    'frequency_unit': line.frequency_unit,
                    'notes': line.notes,
                }))
            appointment_obj.discharge_medication_ids = discharge_medication_ids
            param_name = ''
            param_name2 = ''
            if self.transportation == 'car':
                param_name = 'car.product_template'
            elif self.transportation == 'ambulance':
                param_name = 'ambulance1.product_template'
                param_name2 = 'ambulance2.product_template'

            service_record_id = self.env['ir.config_parameter'].sudo().get_param(param_name)

            product_record = self.env['product.product'].search([('product_tmpl_id', '=', service_record_id)])
            appointment_obj.transportation_service = product_record.id
            if self.transportation == 'ambulance':
                service_record_id = self.env['ir.config_parameter'].sudo().get_param(param_name2)
                product_record = self.env['product.product'].search([('product_tmpl_id', '=', service_record_id)])
                appointment_obj.transportation_service2 = product_record.id

            admission_days_current = 0
            for inp in appointment_obj.bed_transfers_ids:
                admission_days_current += inp.accommodation_qty

            # (record.id, '%s %s' % (record.name, record.patient_id.patient_id.name))

            if admission_days_current > 0 and admission_days_current != self.actual_admission_days:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _(
                            "Note that Patient [%s] Admission Days [%s] are not equal to Accommodation days [%s]"
                            % (appointment_obj.name, self.actual_admission_days, admission_days_current)
                        ),
                        'type': 'warning',
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    },
                }

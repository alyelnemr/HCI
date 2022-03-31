# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date


class MedicalInpatientUpdateNote(models.Model):
    _name = 'medical.inpatient.update.note'
    _description = 'Medical Inpatient Update Note old-model'

    def print_invoice_report(self):
        return self.env.ref('aly_basic_hms.report_print_inpatient_invoice_report').report_action(self)

    def _get_current_inpatient_domain(self):
        current_inpatient = self.env['medical.inpatient.registration'].search([('state', '!=', 'discharged')])
        return [('inpatient_id', 'in', current_inpatient)]

    name = fields.Char(string="Update Note Code", readonly=True)
    is_invoiced = fields.Boolean(copy=False, default=False)
    inpatient_id = fields.Many2one('medical.inpatient.registration',
                                 domain=lambda self: self._get_current_inpatient_domain(),
                                 string="Patient", required=True)
    update_note_date = fields.Datetime(string="Update Note date", required=True, default=date.today())
    attending_physician_id = fields.Many2one('medical.physician', string="Attending Physician")
    info = fields.Text(string="Notes")
    admission_type_management = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU')], string="Admission Type")
    nursing_plan = fields.Text(string="Nursing Plan")
    discharge_plan = fields.Text(string="Discharge Plan")
    invoice_id = fields.Many2one('account.move', 'Invoice')
    is_discharged = fields.Boolean(copy=False, default=False)
    refer_to = fields.Char(string="Refer To")
    transportation = fields.Selection([('car', 'Standard Car'), ('ambulance', 'Ambulance')], string="Transportation")
    recommendation = fields.Text(string="Recommendations")

    @api.model
    def create(self,val):
        patient_id = self.env['ir.sequence'].next_by_code('medical.inpatient.update.note')
        if patient_id:
            val.update({
                        'name': patient_id
                       })
        result = super(MedicalInpatientUpdateNote, self).create(val)
        return result


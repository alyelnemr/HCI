# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class MedicalInpatientRegistration(models.Model):
    _name = 'medical.inpatient.registration'
    _inherit = 'mail.thread'
    _description = 'Medical Inpatient Registration'
    _rec_name = 'patient_id'

    def print_invoice_report(self):
        return self.env.ref('aly_basic_hms.report_print_inpatient_invoice_report').report_action(self)

    @api.depends('discharge_date', 'admission_date')
    def _compute_admission_days(self):
        for rec in self:
            d2 = rec.discharge_date
            d1 = rec.admission_date
            if d1 and d2:
                rd = d2 - d1
                rec.admission_days = rd.days
                if rec.discharge_date < rec.admission_date or rd.days < 0:
                    raise UserError(_('Discharge Date Must be greater than or equal Admission Date...'))

    def _get_inpatient_domain(self):
        patients = []
        current_inpatient = self.env['medical.inpatient.registration'].search([('state', '!=', 'discharged')])
        for rec in current_inpatient:
            patients.append(rec.patient_id.id)
        current_inpatient = self.env['medical.patient'].search([('id', 'not in', patients)])
        for rec in current_inpatient:
            patients.append(rec.id)
        return [('id', 'in', patients)]

    name = fields.Char(string="Registration Code", readonly=True)
    patient_id = fields.Many2one('medical.patient', domain=lambda self: self._get_inpatient_domain(),
                                 string="Patient", required=True)
    admission_date = fields.Date(string="Admission date", required=True, default=date.today())
    discharge_date = fields.Date(string="Expected Discharge date", required=True, default=date.today())
    # admission_days = fields.Integer(compute=_compute_admission_days, string="Admission Duration", store=True)
    admission_days = fields.Integer(string="Admission Duration", default=1)
    attending_physician_id = fields.Many2one('medical.physician',string="Attending Physician")
    admission_type = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU'), ('care', 'Intermediate Care Unit')],
                                      required=False, string="Admission Type")
    info = fields.Text(string="Notes")
    bed_transfers_ids = fields.One2many('medical.inpatient.acc', 'inpatient_id', string='Accommodations')
    state = fields.Selection([('requested', 'Requested'), ('admitted', 'Admitted'), ('discharged', 'Discharged')],
                             string="State", default="requested")
    nursing_plan = fields.Text(string="Nursing Plan")
    discharge_plan = fields.Text(string="Discharge Plan")
    discharge_medication_ids = fields.One2many('medical.inpatient.medication', 'medical_inpatient_registration_id',
                                               string='Medication')
    is_discharged = fields.Boolean(copy=False, default=False)
    discharge_datetime = fields.Datetime(string='Discharge Date Time')
    discharge_basis = fields.Selection([('improve', 'Improvement Basis'), ('against', 'Against Medical Advice'),
                                        ('repatriation', 'Repatriation Basis'),
                                        ('referral', 'Referral Basis')], string="Discharge Basis")
    refer_to = fields.Char(string="Refer To")
    transportation = fields.Selection([('car', 'Standard Car'), ('ambulance', 'Ambulance')], string="Transportation")
    transportation_service = fields.Many2one('product.product',
                                            string='Transportation Service', required=False)
    transportation_service2 = fields.Many2one('product.product',
                                            string='Transportation Service2', required=False)
    recommendation = fields.Text(string="Recommendations")
    doctor_id = fields.Many2one('medical.physician','Discharge Physician', required=False)
    inpatient_update_note_ids = fields.One2many('medical.inp.update.note', 'inpatient_id', string='Inpatient Update Notes')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

    @api.constrains('discharge_date', 'admission_date')
    def date_constrains(self):
        for rec in self:
            if rec.discharge_date < rec.admission_date or rec.admission_days < 0:
                raise ValidationError(_('Discharge Date Must be greater than or equal Admission Date...'))
            if rec.admission_date > date.today():
                raise ValidationError(_('Admission Date Must be lower than or equal Today...'))

    @api.constrains('admission_days', 'bed_transfers_ids', 'discharge_date', 'admission_date')
    def admission_constrains(self):
        for rec in self:
            if len(rec.bed_transfers_ids) <= 0:
                raise ValidationError(_('Accommodation Services must have at least one record...'))

    @api.model
    def create(self,val):
        patient_id = self.env['ir.sequence'].next_by_code('medical.inpatient.registration')
        val.update({
                    'state': 'admitted'
                   })
        if patient_id:
            val.update({
                        'name': patient_id
                       })
        result = super(MedicalInpatientRegistration, self).create(val)
        return result

    def registration_confirm(self):
        self.write({'state': 'confirmed'})

    def registration_admission(self):
        self.write({'state': 'admitted'})

    def registration_cancel(self):
        self.write({'state': 'cancel'})

    def patient_discharge(self):
        self.write({'state': 'invoice'})

# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date, datetime, timezone
import pytz
from tzlocal import get_localzone
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class MedicalPatient(models.Model):
    _name = 'medical.patient'
    _inherits = {'res.partner': 'partner_id'}
    _rec_name = 'partner_id'
    _description = 'Medical Patient'

    def print_report(self):
        return self.env.ref('aly_basic_hms.report_print_medical_record').report_action(self)

    @api.constrains('is_opened_visit')
    def onchange_is_opened_visit(self):
        con = self._context.get('come_from_invoice', False)
        for rec in self:
            if not rec.order_id and not rec.is_opened_visit and not con:
                raise UserError(_('Cannot close Visit which is not invoiced...'))
            if rec.order_id.state == 'sale' or rec.order_id.state == 'done' or rec.invoice_id == 'posted' and not con:
                raise UserError(_('Cannot close Visit which has a confirmed invoice...'))

    @api.constrains('is_insurance', 'insurance_company_id')
    def onchange_is_insurance(self):
        for rec in self:
            if rec.is_insurance and not rec.insurance_company_id:
                raise UserError(_('Please enter Insurance Company or convert to Cash...'))

    @api.depends('date_of_birth')
    def onchange_age(self):
        for rec in self:
            if rec.date_of_birth:
                if rec.date_of_birth > date.today():
                    raise ValidationError(_('Birth date Must be lower than or equal Today...'))
                d1 = rec.date_of_birth
                d2 = datetime.today().date()
                rd = relativedelta(d2, d1)
                rec.age = str(rd.years) + 'y' + ' ' + str(rd.months) + 'm' + ' ' + str(rd.days) + 'd'
            else:
                rec.age = "No Date Of Birth!!"

    @api.constrains('diagnosis_final', 'diagnosis_provisional')
    def diagnosis_constrains(self):
        for rec in self:
            if not rec.diagnosis_final and not rec.diagnosis_provisional:
                raise ValidationError(_('Diagnosis must have at least one (final or provisional)'))

    def _get_patient_domain(self):
        patients = []
        current_inpatient = self.env['medical.patient'].search([])
        for rec in current_inpatient:
            patients.append(rec.patient_id.id)
        return ['&', ('id', 'not in', patients), ('is_patient', '=', True)]

    def _get_clinic_domain(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return [('id', 'in', current_clinics.allowed_clinic_ids)]

    def _get_default_clinic(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return current_clinics.default_clinic_id

    partner_id = fields.Many2one('res.partner', string="Related Partner")
    patient_code = fields.Char(string='Patient Code', readonly=True)
    date_of_birth = fields.Date(string="Date of Birth", required=True)
    sex = fields.Selection([('m', 'Male'), ('f', 'Female')], default='m', string="Sex", required=True)
    age = fields.Char(compute=onchange_age, string="Patient Age", store=True)
    referred_by = fields.Many2one('res.partner', domain=[('is_referred_by', '=', True)], required=False, string='Referred By')
    referred_to = fields.Many2one('res.partner', domain=[('is_referred_to', '=', True)], required=False, string='Referred To')
    is_opened_visit = fields.Boolean(string='Open Visit', default=True, required=False)
    is_invoiced = fields.Boolean(string='Is Invoiced', default=False, required=False)
    invoice_id = fields.Many2one('account.move', string='Accounting Invoice')
    order_id = fields.Many2one('sale.order', string='Draft Invoice')
    is_insurance = fields.Boolean(string='Insurance', default=False, required=False)
    our_reference = fields.Char(string='Our Reference', required=False)
    insurance_reference = fields.Char(string='Insurance Reference')
    insurance_company_id = fields.Many2one('res.partner', domain=[('is_insurance_company', '=', True)],
                                           required=False, string='Insurance Company')
    assistance_company = fields.Char(string="Assistance Company")
    policy_number = fields.Char(string='Policy Number', required=False)
    location_of_examination = fields.Char(string="Location of Examination")
    blood_type = fields.Selection([('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], string="Blood Type")
    marital_status = fields.Selection([('s', 'Single'), ('m', 'Married'),
                                       ('w', 'Widowed'), ('d', 'Divorced')], string='Marital Status')
    nationality_id = fields.Many2one("res.country", "Nationality", required=True)
    travel_agency = fields.Many2one('res.partner', domain=[('is_travel_agency', '=', True)], string='Travel Agency')
    tour_operator = fields.Many2one('res.partner', domain=[('is_tour_operator', '=', True)], string='Tour Operator')
    date_of_arrival = fields.Date(string="Date of Arrival", required=True)
    date_of_departure = fields.Date(string="Date of Departure", required=True)
    hotel = fields.Many2one('res.partner',domain=[('is_hotel', '=', True)], string='Hotel', required=True)
    room_number = fields.Integer(string='Room Number', required=True)
    social_history_info = fields.Text(string="Patient Social History")
    emergency_contact_name = fields.Char(string='Contact Name')
    emergency_contact_phone = fields.Char(string='Contact Phone')
    emergency_contact_relation = fields.Char(string='Contact Relation')
    emergency_contact_address = fields.Char(string='Contact Address')
    diagnosis_final = fields.Char(string='Final Diagnosis')
    diagnosis_provisional = fields.Char(string='Provisional Diagnosis')
    primary_care_physician_id = fields.Many2one('medical.physician', string="Primary Care Doctor")
    patient_complaint = fields.Char(string='Patient Complaint', required=True)
    food_drug_allergy = fields.Char(string='Food and Drug Allergy', required=True)
    history_present_illness = fields.Char(string='History of Present Illness (HPI)', required=True)
    past_medical_history = fields.Char(string='Past Medical History (PMH)', required=True)
    past_surgical_history = fields.Char(string='Past Surgical History (PSH)', required=True)
    family_history = fields.Char(string='Family History (FH)', required=True)
    social_history = fields.Char(string='Social History (SH)', required=True)
    company_id = fields.Many2one('res.company', required=True, string='Branch', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    clinic_id = fields.Many2one('medical.clinic', required=True, string='Facility', readonly=True,
                                default=lambda self: self._get_default_clinic(),
                                domain=lambda self: self._get_clinic_domain())
    bill_to = fields.Char(string='Bill To', required=False)
    update_note_ids = fields.One2many('medical.appointment', 'patient_id')
    inpatient_ids = fields.One2many('medical.inpatient.registration', 'patient_id')
    operation_ids = fields.One2many('medical.operation', 'patient_id')
    attachment_ids = fields.One2many('medical.patient.attachment', 'patient_id', string="Attachments")
    disposable_ids = fields.One2many('medical.patient.line', 'patient_id', string='Disposables', required=True)
    doctor_id = fields.Many2one('medical.physician','Treating Physician',required=False)
    treating_physician_ids = fields.Many2many('medical.physician',string='Treating Physicians',required=False)

    @api.model
    def create(self, val):
        if val.get('date_of_birth'):
            dt = val.get('date_of_birth')
            d1 = datetime.strptime(str(dt), "%Y-%m-%d").date()
            d2 = datetime.today().date()
            rd = relativedelta(d2, d1)
            age = str(rd.years) + "y" + " " + str(rd.months) + "m" + " " + str(rd.days) + "d"
            val.update({'age': age})

        patient_id = self.env['ir.sequence'].next_by_code('medical.patient.code')
        if patient_id:
            val.update({
                        'patient_code': patient_id,
                       })
        if val.get('is_insurance'):
            insurance = self.env.user.company_id.default_account_rec_insurance_id
            val.update({
                        'property_account_receivable_id': insurance,
                       })
        if val.get('is_insurance'):
            insurance = self.env.user.company_id.default_account_rec_insurance_id
            if insurance:
                val['property_account_receivable_id'] = insurance
        else:
            cash = self.env.user.company_id.default_account_rec_cash_id
            if cash:
                val['property_account_receivable_id'] = cash
        result = super(MedicalPatient, self).create(val)
        return result

    def write(self, vals):
        for record in self:
            if not record.name:
                patient_id = self.env['ir.sequence'].next_by_code('medical.patient.code')
                if patient_id:
                    vals.update({
                        'patient_code': patient_id,
                    })
            if record.is_insurance or vals.get('is_insurance'):
                has_insurance_group = self.env.user.has_group('aly_basic_hms.aly_group_insurance')
                if record.is_insurance and not vals.get('is_insurance') and not has_insurance_group:
                    raise UserError(_('You don''t have permission to remove insurance from patient!'))
                if record.is_insurance and record.order_id and not vals.get('order_id') and not has_insurance_group:
                    raise UserError(_('You don''t have permission to remove insurance invoice from patient'))
                if record.is_insurance and record.order_id and record.order_id != vals.get('order_id') and not has_insurance_group:
                    raise UserError(_('You don''t have permission to change insurance invoice from patient'))
                if record.is_insurance and record.invoice_id and not vals.get('invoice_id') and not has_insurance_group:
                    raise UserError(_('You don''t have permission to remove insurance invoice from patient'))
                if record.is_insurance and record.invoice_id and record.invoice_id != vals.get('invoice_id') and not has_insurance_group:
                    raise UserError(_('You don''t have permission to change insurance invoice from patient'))
            if vals.get('is_insurance'):
                insurance = self.env.user.company_id.default_account_rec_insurance_id
                if insurance:
                    vals['property_account_receivable_id'] = insurance
            else:
                cash = self.env.user.company_id.default_account_rec_cash_id
                if cash:
                    vals['property_account_receivable_id'] = cash
        res = super(MedicalPatient, self).write(vals)
        return res

    def my_format_date(self, var_datetime_str):
        user_tz = self.env.user.tz or get_localzone() or pytz.utc
        local = pytz.timezone(user_tz)
        return pytz.utc.localize(var_datetime_str).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if isinstance(var_datetime_str, datetime) else var_datetime_str#.strftime("%d/%m/%Y %H:%M:%S")


    def my_format_date2(self):
        user_tz = self.env.user.tz or get_localzone() or pytz.utc
        local = pytz.timezone(user_tz)
        return str(user_tz) + ' -- ' + str(local)

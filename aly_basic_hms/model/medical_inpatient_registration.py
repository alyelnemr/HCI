# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class MedicalInpatientRegistration(models.Model):
    _name = 'medical.inpatient.registration'
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

    @api.depends('invoice_id')
    def _compute_validity_status(self):
        for rec in self:
            if rec.invoice_id:
                rec.validity_status = 'invoice'
                rec.is_invoiced = True
            else:
                rec.validity_status = 'tobe'
                rec.is_invoiced = False

    def _get_accommodation_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('accommodation.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    name = fields.Char(string="Registration Code", readonly=True)
    is_invoiced = fields.Boolean(copy=False, default=False)
    patient_id = fields.Many2one('medical.patient', domain=[('current_discharge_date', '=', False)],
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
    ip_update_note_ids = fields.One2many('medical.inpatient.update.note', 'inpatient_id', string='Inpatient Update Notes')
    state = fields.Selection([('requested', 'Requested'), ('admitted', 'Admitted'), ('discharged', 'Discharged')],
                             string="State", default="requested")
    nursing_plan = fields.Text(string="Nursing Plan")
    discharge_plan = fields.Text(string="Discharge Plan")
    no_invoice = fields.Boolean(string='Invoice exempt', default=False)
    validity_status = fields.Selection([
        ('invoice', 'Invoice Created'),
        ('tobe', 'To be Invoiced'),
    ], 'Status', compute=_compute_validity_status, store=False, readonly=True, default='tobe')
    invoice_id = fields.Many2one('account.move', 'Invoice')
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
    doctor_id = fields.Many2one('medical.physician','Physician',required=False)
    inpatient_update_note_ids = fields.One2many('medical.inp.update.note', 'inpatient_id')

    @api.constrains('discharge_date', 'admission_date')
    def date_constrains(self):
        for rec in self:
            if rec.discharge_date < rec.admission_date or rec.admission_days < 0:
                raise ValidationError(_('Discharge Date Must be greater than or equal Admission Date...'))
            if rec.admission_date > date.today():
                raise ValidationError(_('Admission Date Must be lower than or equal Today...'))

    @api.constrains('admission_days', 'bed_transfers_ids', 'discharge_date', 'admission_date', 'accommodation_id')
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

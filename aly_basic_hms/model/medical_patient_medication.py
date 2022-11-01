# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class medical_patient_medication(models.Model):
    _name = 'medical.patient.medication'
    _description = 'Medical Patient Medication'

    @api.depends('start_treatment', 'end_treatment')
    def _compute_treatment_days(self):
        for rec in self:
            d2 = rec.end_treatment
            d1 = rec.start_treatment
            if d1 and d2:
                rd = d2 - d1
                rec.treatment_days = rd.days
                if rec.end_treatment < rec.start_treatment or rd.days < 0:
                    raise UserError(_('Treatment End Date Must be greater than or equal Start Date...'))

    medicament = fields.Many2one('medical.medicament',string='Medicine',required=True)
    medicine_quantity = fields.Integer(string='Medicine Quantity',default=1)
    is_active = fields.Boolean(string='Active', default = True)
    start_treatment = fields.Datetime(string='Start Of Treatment',required=True)
    course_completed = fields.Boolean(string="Course Completed")
    doctor_physician_id = fields.Many2one('medical.physician',string='Physician')
    end_treatment = fields.Datetime(string='End Of Treatment',required=True)
    treatment_days = fields.Integer(compute=_compute_treatment_days,string="Treatment Days Count",store=True)
    discontinued = fields.Boolean(string='Discontinued')
    route = fields.Many2one('medical.drug.route',string=" Administration Route ")
    dose = fields.Float(string='Dose')
    qty = fields.Integer(string='X')
    dose_unit = fields.Many2one('medical.dose.unit',string='Dose Unit')
    duration = fields.Integer(string="Treatment Duration")
    duration_period = fields.Selection([('minutes','Minutes'),
                                        ('hours','hours'),
                                        ('days','Days'),
                                        ('months','Months'),
                                        ('years','Years')],string='Treatment Period')
    common_dosage = fields.Many2one('medical.medication.dosage',string='Dosage Frequency')
    admin_times = fields.Char(string='Admin Hours')
    frequency = fields.Integer(string='Frequency')
    frequency_unit = fields.Selection([('seconds','Seconds'),
                                       ('minutes','Minutes'),
                                       ('hours','hours'),
                                       ('days','Days'),
                                       ('weeks','Weeks'),
                                       ('wr','When Required')],string='Unit')
    notes = fields.Text(string='Notes')

# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date, datetime


class medical_prescription_order(models.Model):
    _name = "medical.prescription.order"

    name = fields.Char('Prescription ID', readonly=True)
    patient_id = fields.Many2one('medical.patient', 'Patient ID', required=True)
    prescription_date = fields.Datetime('Prescription Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'Login User', readonly=True, default=lambda self: self.env.user)
    no_invoice = fields.Boolean('Invoice exempt')
    inv_id = fields.Many2one('account.invoice', 'Invoice', readonly=True)
    invoice_to_insurer = fields.Boolean('Invoice to Insurance')
    doctor_id = fields.Many2one('medical.physician', 'Prescribing Doctor')
    appointment_id = fields.Many2one('medical.appointment', 'Appointment ID')
    state = fields.Selection([('invoiced', 'To Invoiced'), ('tobe', 'To Be Invoiced')], 'Invoice Status')
    pharmacy_partner_id = fields.Many2one('res.partner', domain=[('is_pharmacy', '=', True)], string='Pharmacy')
    prescription_line_ids = fields.One2many('medical.prescription.line', 'name', 'Prescription Line')
    notes = fields.Text('Prescription Note')
    is_invoiced = fields.Boolean(copy=False, default=False)
    insurer_id = fields.Many2one('medical.insurance', 'Insurer')
    is_shipped = fields.Boolean(default=False, copy=False)
    company_id = fields.Many2one('res.company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medical.prescription.order') or '/'
        return super(medical_prescription_order, self).create(vals)

    def prescription_report(self):
        return self.env.ref('report_print_prescription').report_action(self)

    @api.onchange('name')
    def onchange_name(self):
        ins_obj = self.env['medical.insurance']
        ins_record = ins_obj.search([('patient_id', '=', self.patient_id.patient_id.id)])
        self.insurer_id = ins_record.id or False

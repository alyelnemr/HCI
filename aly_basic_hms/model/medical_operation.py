# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class MedicalOperation(models.Model):
    _name = 'medical.operation'
    _description = 'description'

    @api.depends('invoice_id')
    def _compute_validity_status(self):
        for rec in self:
            if rec.invoice_id:
                rec.validity_status = 'invoice'
                rec.is_invoiced = True
            else:
                rec.validity_status = 'tobe'
                rec.is_invoiced = False

    name = fields.Char(string="Operation Code", readonly=True)
    patient_id = fields.Many2one('medical.patient', string='Patient', required=True)
    type_of_anesthesia = fields.Char(string='Type of Anesthesia', required=True)
    monitoring = fields.Char(string='Monitoring')
    induction = fields.Char(string='Induction')
    maintenance = fields.Char(string='Maintenance')
    hemodynamic_status = fields.Char(string='Hemodynamic Status')
    blood_loss = fields.Char(string='Blood Loss')
    recovery = fields.Char(string='Recovery')
    further_note = fields.Char(string='Further Note')
    time_in = fields.Datetime(string='Time In', required=True)
    time_out = fields.Datetime(string='Time Out', required=True)
    operation_line_ids = fields.One2many('medical.operation.line','operation_id', string='Post Operative Investigations',required=True)
    notes = fields.Text(string='Operative Report')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    validity_status = fields.Selection([
        ('invoice', 'Invoice Created'),
        ('tobe', 'To be Invoiced'),
    ], 'Status', compute=_compute_validity_status, store=False, sort=False, readonly=True, default='tobe')
    is_invoiced = fields.Boolean(copy=False,default=False)
    no_invoice = fields.Boolean(string='Invoice exempt', default=False)

    @api.model
    def create(self, val):
        medical_operation_id = self.env['ir.sequence'].next_by_code('medical_operation_seq')
        if medical_operation_id:
            val.update({
                        'name':medical_operation_id,
                       })
        result = super(MedicalOperation, self).create(val)
        return result

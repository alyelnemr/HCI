
from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError


class MedicalOperation(models.Model):
    _name = 'medical.operation'
    _description = 'Medical Operation'

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
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, val):
        medical_operation_id = self.env['ir.sequence'].next_by_code('medical_operation_seq')
        if medical_operation_id:
            val.update({
                        'name':medical_operation_id,
                       })
        result = super(MedicalOperation, self).create(val)
        return result

from odoo import api, fields, models, _


class MedicalPatientAttachment(models.Model):
    _name = 'medical.patient.attachment'

    name = fields.Many2one('medical.patient', 'Patient ID')
    patient_id = fields.Many2one('medical.patient', 'Patient ID')
    att_document = fields.Binary(string='Attachment')
    att_document_name = fields.Char(string='File Name')
    short_comment = fields.Char('Comment', size=128)

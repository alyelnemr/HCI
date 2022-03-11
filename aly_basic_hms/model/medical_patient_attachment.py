from odoo import api, fields, models, _


class MedicalPatientAttachment(models.Model):
    _name = 'medical.patient.attachment'
    _description = ''

    name = fields.Char(string='File Name', required=True)
    patient_id = fields.Many2one('medical.patient')
    att_document = fields.Binary(string='Attachment', required=True)
    short_comment = fields.Char('Comment', size=128)

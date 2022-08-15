# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date,datetime


class medical_lab(models.Model):
    _name = 'medical.lab'
    _description = 'Medical Lab'

    name = fields.Char('Medical Lab Name')
    date_analysis =  fields.Datetime('Date of the Analysis', default=datetime.now())
    patient_id = fields.Many2one('medical.patient', 'Patient', required=True)
    date_requested = fields.Datetime('Date requested',  default=datetime.now())
    medical_lab_physician_id = fields.Many2one('medical.physician', 'Pathologist')
    requestor_physician_id = fields.Many2one('medical.physician', 'Physician', required=True)
    results= fields.Text('Results')
    diagnosis = fields.Text('Diagnosis')
    
    @api.model
    def create(self,val):
        val['name'] = self.env['ir.sequence'].next_by_code('medical.test_seq')
        result = super(medical_lab, self).create(val)

        return result


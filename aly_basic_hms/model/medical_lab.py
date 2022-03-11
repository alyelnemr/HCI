# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date,datetime


class medical_lab(models.Model):
    _name = 'medical.lab'
    _description = 'description'

    name = fields.Char('ID')
    test_id = fields.Many2one('medical.test_type', 'Test Type', required = True)
    date_analysis =  fields.Datetime('Date of the Analysis' , default = datetime.now())
    patient_id = fields.Many2one('medical.patient','Patient', required = True) 
    date_requested = fields.Datetime('Date requested',  default = datetime.now())
    medical_lab_physician_id = fields.Many2one('medical.physician','Pathologist')
    requestor_physician_id = fields.Many2one('medical.physician','Physician', required = True)
    criteria_ids = fields.One2many('medical_test.criteria','medical_lab_id', 'criteria')
    results= fields.Text('Results')
    diagnosis = fields.Text('Diagnosis')
    is_invoiced = fields.Boolean(copy=False,default = False)
   
    
    @api.model
    def create(self,val):
        val['name'] = self.env['ir.sequence'].next_by_code('medical.test_seq')
        result = super(medical_lab, self).create(val)
        if val.get('test_id'):
            criteria_obj= self.env['medical_test.criteria']
            criterea_ids = criteria_obj.search([('test_id', '=',val['test_id'] )])
            for id in   criterea_ids:
                criteria_obj.write({'medical_lab_id':result})

        return result

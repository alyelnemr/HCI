# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# classes under cofigration menu of laboratry 

class medical_test_type(models.Model):

    _name  = 'medical.test_type'
    _description = 'description'

    name = fields.Char('Name', required = True)
    code  =  fields.Char('Code' , required = True)
    criteria_ids = fields.One2many('medical_test.criteria', 'test_id','criteria')
    service_product_id = fields.Many2one('product.product','Service' , required = True)
    info  = fields.Text('Extra Information')

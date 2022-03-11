# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class psc_code(models.Model):
    _name  = 'psc.code'
    _description = 'description'
    
    name = fields.Char('Code', required =True) 
    description = fields.Text('Long Text', required =True)

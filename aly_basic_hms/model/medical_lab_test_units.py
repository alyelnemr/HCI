# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class medical_lab_test_units(models.Model):
    _name = 'medical.lab.test.units'
    _description = 'description'
    
    name = fields.Char('Name', required = True)
    code = fields.Char('Code')

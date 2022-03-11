# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class medical_family_disease(models.Model):
    _name = 'medical.family.disease'
    _rec_name = 'patient_id'
    _description = 'description'

    medical_pathology_id = fields.Many2one('medical.pathology', 'Disease',required=True)
    relative_name = fields.Char('Relative', required=True)
    relative_select = fields.Selection([('m','Mother'), ('f','Father'), ('b', 'Brother'), ('s', 'Sister'), ('a', 'aunt'), ('u', 'Uncle'), ('ne', 'Nephew'), ('ni', 'Niece'), ('gf', 'GrandFather'), ('gm', 'GrandMother')],string="Relative Select")
    patient_id = fields.Many2one('medical.patient',string="Patient")

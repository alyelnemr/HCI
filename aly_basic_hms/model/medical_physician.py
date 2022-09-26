# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class medical_physician(models.Model):
    _name = "medical.physician"
    _rec_name = 'partner_id'
    _description = 'Medical Physician'

    partner_id = fields.Many2one('res.partner', 'Physician', required=True)
    institution_partner_id = fields.Many2one('res.partner', domain=[('is_institution', '=', True)], string='Institution')
    mobile = fields.Char('Mobile Phone')
    email = fields.Char('Email')
    qualification = fields.Char('Qualification')
    graduation_year = fields.Integer('Graduation Year')
    languages = fields.Many2many('medical.physician.languages', string='Languages')
    certificates = fields.Text('Scientific certificates')


class MedicalPhyicianLanguages(models.Model):
    _name = "medical.physician.languages"
    _description = 'Medical Physician Languages'
    _rec_name = 'language'

    language = fields.Char('Languages')

# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class BedTransfer(models.Model):
    _name = 'medical.clinic'
    _description = 'Medical Clinics'

    name = fields.Char("Clinic Name", required=True)
    info = fields.Text('Extra Info')
    is_clinic = fields.Boolean(string='Is Clinic', default=True)
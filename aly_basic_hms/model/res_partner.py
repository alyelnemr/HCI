# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_partner(models.Model):
    _inherit = 'res.partner'

    relationship = fields.Char(string='Relationship')
    relative_partner_id = fields.Many2one('res.partner',string="Relative_id")
    is_patient = fields.Boolean(string='Patient')
    is_person = fields.Boolean(string="Person")
    is_doctor = fields.Boolean(string="Doctor")
    is_referred_to = fields.Boolean(string="Referred To")
    is_referred_by = fields.Boolean(string="Referred By")
    is_insurance_company = fields.Boolean(string='Insurance Company')
    is_travel_agency = fields.Boolean(string='Travel Agency')
    is_tour_operator = fields.Boolean(string='Tour Operator')
    is_our_reference = fields.Boolean(string='Our Reference')
    is_hotel = fields.Boolean(string='Hotel')
    is_insurance_reference = fields.Boolean(string='Insurance Reference')
    is_pharmacy = fields.Boolean(string="Pharmacy")
    # patient_insurance_ids = fields.One2many('medical.insurance','patient_id')
    is_institution = fields.Boolean('Institution')
    company_insurance_ids = fields.One2many('medical.insurance','insurance_company_id','Insurance')
    reference = fields.Char('ID Number')
    occupancy_rate = fields.Char('Occupancy Rate')

    @api.model
    def create(self,val):
        appointment = self._context.get('is_insurance_company')
        result = super(res_partner, self).create(val)
        return result

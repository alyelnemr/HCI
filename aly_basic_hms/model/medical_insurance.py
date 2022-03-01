# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MedicalInsurance(models.Model):
    _name = 'medical.insurance'

    @api.depends('number', 'insurance_company_id', 'member_exp')
    def _compute_record_name(self):
        for rec in self:
            if rec.number:
                rec_name = rec.number
            if rec.insurance_company_id:
                rec_name += ' - ' + rec.insurance_company_id.name
            if rec.member_exp:
                rec_name += ' - ' + str(rec.member_exp)
            if rec_name:
                rec.name = rec_name

    name = fields.Char(string='Card Name', compute='_compute_record_name', store=True)
    number = fields.Char('Policy Number', required=True)
    patient_id = fields.Many2one('medical.patient', 'Card Owner - Patient')
    type = fields.Selection([('state','State'),('private','Private'),('labour_union','Labour Union/ Syndical')],'Insurance Type')
    insurance_company_id = fields.Many2one('res.partner',domain=[('is_insurance_company', '=', True)], required=True, string='Insurance Company')
    category = fields.Char('Category')
    notes = fields.Text('Extra Info')
    member_exp = fields.Date(string='Card Expiration Date', required=True)
    medical_insurance_plan_id = fields.Many2one('medical.insurance.plan','Plan')
    price_list_id = fields.Many2one('product.pricelist', string="Insurance Price List", required=False)

# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import date,datetime


class MedicalExternalServiceWizard(models.TransientModel):
    _name = "medical.external.service"
    _inherits = {'res.partner': 'partner_id'}
    _rec_name = 'partner_id'
    _description = 'Medical External Service'


    def _get_clinic_domain(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return [('id', 'in', current_clinics.allowed_clinic_ids)]

    def _get_default_clinic(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return current_clinics.default_clinic_id

    partner_id = fields.Many2one('res.partner', string="Related Partner")
    patient_name = fields.Char(string='Patient Name', related='partner_id.name')
    date_of_birth = fields.Date(string="Date of Birth", required=True)
    invoice_id = fields.Many2one('account.move', string='Accounting Invoice')
    nationality_id = fields.Many2one("res.country", "Nationality", required=True)
    clinic_id = fields.Many2one('medical.clinic', required=True, string='Facility', readonly=True,
                                default=lambda self: self._get_default_clinic(),
                                domain=lambda self: self._get_clinic_domain())
    treating_physician_id = fields.Many2one('medical.physician',string='Treating Physician',required=True)
    service_date = fields.Datetime('Service Date',required=True,default=fields.Datetime.now)
    product_id = fields.Many2one('product.product', 'Service',
                                 domain=lambda self: self._get_investigation_product_category_domain(), required=True)
    quantity = fields.Integer('Quantity', default=1, required=True)
    service_amount = fields.Monetary(string="Service Price")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', required=True, string='Branch', readonly=True,
                                 default=lambda self: self.env.user.company_id)

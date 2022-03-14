# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalInpatientAcc(models.Model):
    _name = 'medical.inpatient.acc'
    _description = 'description'

    @api.constrains('accommodation_qty')
    def date_constrains(self):
        for rec in self:
            if rec.accommodation_qty < 1:
                raise ValidationError(_('Accommodation Days Must be greater than 1'))

    name = fields.Char("Name")
    admission_type = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU')],
                                      required=True, default='standard', string="Admission Type")
    accommodation_qty = fields.Integer(string="Qty (days)", default=1)
    acc_service_ids = fields.One2many('medical.inpatient.accommodation', 'acc_id', string='Accommodations')
    inpatient_id = fields.Many2one('medical.inpatient.registration', string='Inpatient Id')

    @api.model
    def create(self,val):
        param_name = ''
        if val['admission_type'] == 'standard':
            param_name = 'standard_accommodation.auto_services'
        elif val['admission_type'] == 'icu':
            param_name = 'icu_accommodation.auto_services'

        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param(param_name)
        services = accom_prod_cat.split(',')
        acc_services = []
        for ser in services:
            record_name = 'aly_basic_hms.' + ser
            service_record = self.env.ref(record_name)
            product_record = self.env['product.product'].search([('product_tmpl_id', '=', service_record.id)])
            acc_services.append((0, 0, {
                    'name': val['admission_type'],
                    'admission_type': val['admission_type'],
                    'accommodation_service': product_record.id,
                    'accommodation_qty': val['accommodation_qty']
                }))
        val.update({
            'acc_service_ids': acc_services
        })
        result = super(MedicalInpatientAcc, self).create(val)
        return result

    @api.model
    def write(self,val):
        param_name = ''
        for record in self:
            admission_type = val['admission_type'] if 'admission_type' in val.keys() else record.admission_type
            accommodation_qty = val['accommodation_qty'] if 'accommodation_qty' in val.keys() else record.accommodation_qty
            if admission_type == 'standard':
                param_name = 'standard_accommodation.auto_services'
            elif admission_type == 'icu':
                param_name = 'icu_accommodation.auto_services'

            accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param(param_name)
            services = accom_prod_cat.split(',')
            for acc in record.acc_service_ids:
                acc.unlink()
            acc_services = []
            for ser in services:
                record_name = 'aly_basic_hms.' + ser
                service_record = self.env.ref(record_name)
                product_record = self.env['product.product'].search([('product_tmpl_id', '=', service_record.id)])
                acc_services.append((0, 0, {
                    'name': admission_type,
                    'admission_type': admission_type,
                    'accommodation_service': product_record.id,
                    'accommodation_qty': accommodation_qty
                }))
            val.update({
                'acc_service_ids': acc_services
            })
        result = super(MedicalInpatientAcc, self).write(val)
        return result

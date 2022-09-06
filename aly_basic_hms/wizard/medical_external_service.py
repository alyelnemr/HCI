# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import date,datetime


class MedicalExternalServiceWizard(models.TransientModel):
    _name = "medical.external.service.wizard"
    _description = 'Medical External Service Wizard'


    def _get_clinic_domain(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return [('id', 'in', current_clinics.allowed_clinic_ids)]

    def _get_default_clinic(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return current_clinics.default_clinic_id

    patient_name = fields.Char(string='Patient Name')
    date_of_birth = fields.Date(string="Date of Birth", required=True)
    nationality_id = fields.Many2one("res.country", "Nationality", required=True)
    clinic_id = fields.Many2one('medical.clinic', required=True, string='Facility', readonly=True,
                                default=lambda self: self._get_default_clinic(),
                                domain=lambda self: self._get_clinic_domain())
    treating_physician_id = fields.Many2one('medical.physician',string='Treating Physician',required=True)
    service_date = fields.Datetime('Service Date',required=True,default=fields.Datetime.now)
    product_id = fields.Many2one('product.product', 'Service', required=True)
    quantity = fields.Integer('Quantity', default=1, required=True)
    service_amount = fields.Monetary(string="Service Price")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', required=True, string='Branch', readonly=True,
                                 default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        res_return = super(MedicalExternalServiceWizard, self).create(vals)
        account_invoice_obj = self.env['account.move']
        medical_external_service_obj = self.env['medical.external.service']
        product_product_obj = self.env['product.product'].browse(vals['product_id'])
        ir_property_obj = self.env['ir.property']
        partner_id = self.env['res.partner'].create({'name': vals['patient_name']})
        invoice_vals = {
            'name': self.env['ir.sequence'].next_by_code('medical_patient_inv_seq'),
            'invoice_origin': partner_id.name or '',
            'move_type': 'out_invoice',
            'partner_id': partner_id or False,
            'partner_shipping_id': partner_id or False,
            'currency_id': vals['currency_id'],
            'invoice_payment_term_id': False,
            'fiscal_position_id': partner_id.property_account_position_id.id,
            'team_id': False,
            'invoice_date': vals['service_date'],
            'company_id': self.env.user.company_id,
            'ref': partner_id.id,
        }
        res = account_invoice_obj.create(invoice_vals)
        list_of_vals = []
        invoice_line_account_id = False
        if product_product_obj:
            invoice_line_account_id = product_product_obj.property_account_income_id.id \
                                      or product_product_obj.categ_id.property_account_income_categ_id.id \
                                      or False
        if not invoice_line_account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
        if not invoice_line_account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (product_product_obj.name,))
        invoice_line_vals = {
            # 'name': appointment.consultations_id.name or '',
            'name': product_product_obj.name or '',
            'account_id': invoice_line_account_id,
            'price_unit': vals['service_amount'],
            'product_uom_id': product_product_obj.uom_id.id,
            'quantity': 1,
            'product_id': product_product_obj.id,
        }
        list_of_vals.append((0, 0, invoice_line_vals))
        print(partner_id)
        res1 = res.write({'invoice_line_ids': list_of_vals})
        res.action_post()
        print("it's OK")
        journal_id = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.env.user.company_id.id),
        ], limit=1)
        payment_vals = {
            'date': vals['service_date'],
            'amount': vals['service_amount'],
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'ref': partner_id.name,
            'journal_id': journal_id.id,
            'currency_id': vals['currency_id'],
            'partner_id': partner_id.id,
            'partner_bank_id': False,
            'payment_method_id': journal_id.inbound_payment_method_ids._origin.id,
            'destination_account_id': partner_id.property_account_receivable_id.id
        }
        payments = self.env['account.payment'].create(payment_vals)
        payments.action_post()
        res_patient = self.env['medical.external.service'].create({
            'partner_id': partner_id.id,
            'patient_name': res_return.patient_name,
            'date_of_birth': res_return.date_of_birth,
            'nationality_id': res_return.nationality_id.id,
            'clinic_id': res_return.clinic_id.id,
            'treating_physician_id': res_return.treating_physician_id.id,
            'service_date': res_return.service_date,
            'product_id': res_return.product_id.id,
            'quantity': res_return.quantity,
            'service_amount': res_return.service_amount,
            'currency_id': res_return.currency_id.id,
            'company_id': res_return.company_id.id,
        })
        return res_return

    def action_confirm(self):
        return True

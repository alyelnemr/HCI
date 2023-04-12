# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import date,datetime


class PharmacyInvoice(models.Model):
    _name = 'pharmacy.invoice'
    _inherits = {'res.partner': 'partner_id'}
    _rec_name = 'partner_id'
    _description = 'Pharmacy Invoice'

    @api.depends('company_id')
    def _compute_journal_id(self):
        for wizard in self:
            wizard.journal_id = self.sudo().env['account.journal'].search([
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', wizard.company_id.id),
            ], limit=1)

    @api.depends('journal_id')
    def _compute_payment_method_id(self):
        for wizard in self:
            wizard.payment_method_id = wizard.journal_id.inbound_payment_method_ids._origin[:1]

    @api.depends('journal_id')
    def _compute_payment_method_fields(self):
        for wizard in self:
            wizard.available_payment_method_ids = None
            wizard.hide_payment_method = False

    def _get_pharmacy_services(self):
        prod_cat_obj = self.env['product.product'].search([('name', '=', 'Pharmacy Item')], limit=1)
        return prod_cat_obj.id

    @api.depends('product_id')
    def get_pharmacy_product_categ_id(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('pharmacy_service.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)], limit=1)
        prod_cat_obj_id = prod_cat_obj.id
        self.categ_id_pharmacy = prod_cat_obj_id

    @api.depends('product_id', 'service_amount')
    def compute_bank_fees(self):
        self.bank_fees_amount = 0
        if self.service_amount and self.product_id:
            self.bank_fees_amount = self.service_amount * .05

    def _get_clinic_domain(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return [('id', 'in', current_clinics.allowed_clinic_ids)]

    def _get_default_clinic(self):
        current_clinics = self.env['res.users'].browse(self.env.user.id)
        return current_clinics.default_clinic_id

    partner_id = fields.Many2one('res.partner', string="Related Partner")
    patient_name = fields.Char(string='Patient Name', required=True)
    nationality_id = fields.Many2one("res.country", "Nationality", required=True)
    clinic_id = fields.Many2one('medical.clinic', required=False, string='Facility', readonly=True,
                                default=lambda self: self._get_default_clinic(),
                                domain=lambda self: self._get_clinic_domain())
    service_date = fields.Datetime('Service Date',required=True,default=fields.Datetime.now)
    item_category = fields.Selection([('medication', 'Medication'), ('cosmetic', 'Cosmetics'), ('accessory', 'Accessories')]
                                     , required=True, default='medication', string="Item Category")
    product_id = fields.Many2one('product.product', 'Service',
                                 default=lambda self: self._get_pharmacy_services(), required=False)
    categ_id_pharmacy = fields.Integer('Medicine Product Category ID', store=False, compute=get_pharmacy_product_categ_id)
    item_name = fields.Char(string='Service', required=False)
    quantity = fields.Integer('Quantity', default=1, required=True)
    service_amount = fields.Monetary(string="Service Price")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', required=True, string='Branch', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    invoice_id = fields.Many2one('account.move', string='Accounting Invoice')
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,
                                 domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    journal_id_type = fields.Selection([
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ],related='journal_id.type', string='Journal Type')

    # == Payment methods fields ==
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', readonly=False, store=True,
                                        compute='_compute_payment_method_id',
                                        domain="[('id', 'in', available_payment_method_ids)]")
    available_payment_method_ids = fields.Many2many('account.payment.method', compute='_compute_payment_method_fields')
    hide_payment_method = fields.Boolean(compute='_compute_payment_method_fields')

    @api.model
    def create(self, vals):
        account_invoice_obj = self.env['account.move']
        medical_external_service_obj = self.env['pharmacy.invoice']
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('pharmacy_service.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)], limit=1)
        cat = prod_cat_obj.id

        product_product_obj = self.env['product.product'].sudo().create({
            'name': vals['item_name'],
            'type': 'service',
            'categ_id': cat
        })
        ir_property_obj = self.env['ir.property']
        partner_id = self.env['res.partner'].sudo().create({'name': vals['patient_name'], 'is_pharmacy': True})
        invoice_vals = {
            'name': '/',
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
        service_amount = 0
        if 'service_amount' in vals:
            service_amount = vals['service_amount']
        invoice_line_vals = {
            # 'name': appointment.consultations_id.name or '',
            'name': product_product_obj.name or '',
            'account_id': invoice_line_account_id,
            'price_unit': service_amount,
            'product_uom_id': product_product_obj.uom_id.id,
            'quantity': 1,
            'product_id': product_product_obj.id,
        }
        list_of_vals.append((0, 0, invoice_line_vals))

        res1 = res.write({'invoice_line_ids': list_of_vals})
        res.sudo().action_post()
        vals['invoice_id'] = res.id
        vals['partner_id'] = partner_id.id
        res_return = super(MedicalExternalServiceWizard, self).create(vals)
        journal_id = self.env['account.journal'].sudo().browse(vals['journal_id'])
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
        payments.sudo().action_post()
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('reconciled', '=', False),
        ]
        payment_lines = payments.line_ids.filtered_domain(domain)
        lines = res.line_ids

        for account in payment_lines.account_id:
            (payment_lines + lines) \
                .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                .reconcile()

        return res_return

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_service_charge_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('service_charge.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)], limit=1)
        prod_cat_obj_id = prod_cat_obj.id
        if not self.aly_service_product_id:
            domain = [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', True), ('type', '=', 'service')]
        return domain

    header = fields.Binary(string='Medical Report Header - Clinic')
    footer = fields.Binary(string='Medical Report Footer - Clinic')
    header_hospital = fields.Binary(string='Medical Report Header - Hospital')
    footer_hospital = fields.Binary(string='Medical Report Footer - Hospital')
    bank_details = fields.Text(string='Banks Accounts Details')
    aly_enable_service_charge = fields.Boolean(string='Enable Service Charges', default=True)
    aly_service_charge_percentage = fields.Float(string="Service Charge Percentage", default=12.5)
    aly_service_product_id = fields.Many2one('product.product', string='Service Charge Product',
                                             domain=lambda self: self._get_service_charge_domain())
    aly_enable_bank_fees = fields.Boolean(string='Enable Bank Fees', default=True)
    aly_bank_fees_percentage = fields.Float(string="Bank Fees Percentage", default=.05)
    aly_bank_fees_journal_id = fields.Many2one(comodel_name='account.journal', string='Journal')
    aly_bank_fees_account = fields.Many2one('account.account', string='Bank Fees default Account', domain="[('company_id', '=', current_company_id)]")
    default_account_rec_cash_id = fields.Many2one('account.account',
                                                  domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                  string="Account Receivable (Cash)")
    default_account_rec_insurance_id = fields.Many2one('account.account',
                                                       domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
                                                       string="Account Receivable (Insurance)")
    bank_fees_ids = fields.One2many(comodel_name='bank.fees', inverse_name='company_id', string='Bank Fees')

    @api.onchange('aly_enable_service_charge')
    def set_config_service_charge(self):
        if self.aly_enable_service_charge:
            accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('service_charge.product_category')
            prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
            prod_cat_obj_id = 0
            if len(prod_cat_obj) >= 2:
                prod_cat_obj_id = prod_cat_obj[0].id
            else:
                prod_cat_obj_id = prod_cat_obj.id
            if not self.aly_service_product_id:
                domain = [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', True), ('type', '=', 'service')]
                self.aly_service_product_id = self.env['product.product'].search(domain, limit=1)
        else:
            self.aly_service_product_id = False

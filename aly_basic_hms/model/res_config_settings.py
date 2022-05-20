from odoo import api, fields, models, _


class AlyResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_service_charge_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('service_charge.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) >= 2:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        if not self.aly_service_product_id:
            domain = [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', True), ('type', '=', 'service')]
        return domain

    aly_enable_service_charge = fields.Boolean(string='Enable Service Charges', default=True)
    aly_service_charge_percentage = fields.Float(string="Service Charge Percentage", default = 12.5)
    aly_service_product_id = fields.Many2one('product.product', string='Service Product',
                                 domain=lambda self: self._get_service_charge_domain())

    def get_values(self):
        aly_res = super(AlyResConfigSettings, self).get_values()
        aly_res.update(
            aly_service_charge_percentage = self.env['ir.config_parameter'].sudo().get_param('aly_service_charge_percentage'),
            aly_enable_service_charge = self.env['ir.config_parameter'].sudo().get_param('aly_enable_service_charge'),
            # aly_service_product_id = self.env['ir.config_parameter'].sudo().get_param('aly_service_product_id'),
        )
        return aly_res

    def set_values(self):
        super(AlyResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('aly_service_charge_percentage', self.aly_service_charge_percentage)
        self.env['ir.config_parameter'].set_param('aly_enable_service_charge', self.aly_enable_service_charge)
        self.env['ir.config_parameter'].set_param('aly_service_product_id', self.aly_service_product_id.id)

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
                domain = [('categ_id', '=', prod_cat_obj_id), ('sale_ok', '=', True),  ('type', '=', 'service')]
                self.aly_service_product_id = self.env['product.product'].search(domain, limit=1)
        else:
            self.aly_service_product_id = False

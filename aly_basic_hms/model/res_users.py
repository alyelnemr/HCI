from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2one('stock.warehouse', string="Allowed Warehouses")
    max_allowed_discount = fields.Float(string='Max Allowed Discount %', default=0.0)
    default_clinic_id = fields.Many2one(comodel_name='medical.clinic', string="Default Clinic")
    allowed_clinic_ids = fields.Many2many(comodel_name='medical.clinic', string="Allowed Clinics")
    allowed_bank_fees_ids = fields.Many2many(comodel_name='account.journal', string="Allowed Payment Methods", domain=[('is_bank_fees', '=', True)])
    effective_date = fields.Date(string="Effective Date")
    pricelist_id = fields.Many2one(comodel_name='product.pricelist', string='Pricelist')

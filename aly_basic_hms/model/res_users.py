from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2one('stock.warehouse', string="Allowed Warehouses")
    max_allowed_discount = fields.Float(string='Max Allowed Discount %', default=0.0)
    default_clinic_id = fields.Many2one('medical.clinic', string="Default Clinic")
    allowed_clinic_ids = fields.Many2many('medical.clinic', string="Allowed Clinics")

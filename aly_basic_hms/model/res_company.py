
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    header = fields.Binary(string='Report Header')
    footer = fields.Binary(string='Report Footer')


class ResUsers(models.Model):
    _inherit = 'res.users'

    warehouse_ids = fields.Many2one('stock.warehouse', string="Allowed Warehouses")

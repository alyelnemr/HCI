
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = ''

    header = fields.Binary(string='Report Header')
    footer = fields.Binary(string='Report Footer')


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class ProductCategorySorting(models.Model):
    _inherit = "product.category"

    sorting_rank = fields.Integer(string='Sorting Rank', default=100)

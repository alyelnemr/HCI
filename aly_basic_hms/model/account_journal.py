
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools import float_compare, date_utils, email_split, email_re, float_is_zero
from collections import defaultdict


class AccountMoveForDiscount(models.Model):
    _inherit = 'account.journal'

    is_insurance_journal = fields.Boolean(string='Is Insurance Journal', default=False, required=False)
    is_bank_fees = fields.Boolean(string='Is Bank Fees', default=False, required=False)
    bank_fees_percentage = fields.Float(string="Bank Fees Percentage", default=.05)
    bank_fees_account = fields.Many2one(comodel_name='account.account', string='Bank Fees Account')

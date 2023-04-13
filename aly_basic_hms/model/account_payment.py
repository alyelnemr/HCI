# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.Model):
    _inherit = 'account.payment'

    patient_id = fields.Many2one('medical.patient', 'Patient', default=False, required=False)
    is_bank_fees = fields.Boolean(string='Is Bank Fees', default=False, required=False)

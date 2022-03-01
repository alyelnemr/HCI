# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MedicalInpatientLine(models.Model):
    _name = 'medical.inpatient.line'

    medical_inpatient_update_note_id = fields.Many2one('medical.inpatient.update.note','Inpatient ID')
    product_id = fields.Many2one('product.product','Service',domain=[('sale_ok', '=', 1), ('type', '=', 'service')],
                                 required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)

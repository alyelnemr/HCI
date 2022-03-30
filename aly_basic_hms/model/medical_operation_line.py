# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MedicalOperationLine(models.Model):
    _name = 'medical.operation.line'
    _description = 'Medical Operation Line'

    operation_id = fields.Many2one('medical.operation','Operation')
    product_id = fields.Many2one('product.product','Service',domain=[('sale_ok', '=', 1), ('type', '=', 'service')],
                                 required=True)
    quantity = fields.Integer('Quantity', default=1)
    short_comment = fields.Char('Comment', size=128)

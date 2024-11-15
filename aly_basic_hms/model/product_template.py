# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class ProductInherit(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        has_my_group = self.env.user.has_group('aly_basic_hms.aly_group_medical_manager')
        if not has_my_group and not self.env.su:
            raise exceptions.ValidationError("Sorry you can't create products!")
        return super(ProductInherit, self).create(vals)

    def write(self, vals):
        has_my_group = self.env.user.has_group('aly_basic_hms.aly_group_medical_manager')
        if not has_my_group and not self.env.su:
            raise exceptions.ValidationError("Sorry you can't edit products!")
        return super(ProductInherit, self).write(vals)

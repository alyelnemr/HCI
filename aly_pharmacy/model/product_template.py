# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.template'

    def unlink(self):
        for item in self:
            if item.name == 'Pharmacy Item':
                raise ValidationError("You can not delete 'Pharmacy Item', as it has been used in Pharmacy Module.")
        return super(ProductProduct, self).unlink()

    def write(self, vals):
        if 'name' in vals and self.name == 'Pharmacy Item':
            raise ValidationError("You can not edit 'Pharmacy Item', as it has been used in Pharmacy Module.")
        res = super(ProductProduct, self).write(vals)
        return res

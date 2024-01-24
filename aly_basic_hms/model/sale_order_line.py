from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def unlink(self):
        for rec in self:
            if rec.product_id == self.company_id.aly_service_product_id:
                raise UserError('You cannot remove the service charge.')
        return super(SaleOrderLine, self).unlink()
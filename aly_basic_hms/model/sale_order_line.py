from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def unlink(self):
        for rec in self:
            has_my_group = self.env.user.has_group('aly_basic_hms.aly_group_medical_manager')
            if not has_my_group and not self.env.su:
                if rec.product_id == self.company_id.aly_service_product_id:
                    raise UserError('You cannot remove the service charge.')
        return super(SaleOrderLine, self).unlink()

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import sql

from odoo import tools
from odoo import api, fields, models


class FleetReport(models.Model):
    _name = "medical.patient.dashboard.report"
    _description = "Medical Patient Dashboard Report"
    _auto = False
    _order = 'hotel_name'
    _rec_name = 'hotel_name'

    hotel_name = fields.Char('Hotel Name', readonly=True)
    invoice_amount = fields.Float('Invoice Amount', readonly=True)
    patient_count = fields.Float('Patients Count', readonly=True)
    invoice_date = fields.Date(string="Invoice Date", readonly=True)
    patient_id = fields.Many2one('medical.patient', 'Patient ID')

    def init(self):
        query = """
select p.id, rph.name as hotel_name, sum(p.invoice_amount_measure)  as invoice_amount, count(p.id) as patient_count,
cast(p.create_date as date) as invoice_date, p.id as patient_id
from medical_patient p inner join res_partner rp 
on p.partner_id = rp.id 
inner join res_partner rph on p.hotel = rph.id
group by rph.id, rph.name, p.create_date, p.id
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))

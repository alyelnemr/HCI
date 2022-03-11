from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError


class MedicalAppointment(models.Model):
    _name = "medical.appointment"
    _inherit = 'mail.thread'
    _order = "name, appointment_date desc"
    _description = ''

    @api.depends('invoice_id')
    def _compute_validity_status(self):
        for rec in self:
            if rec.invoice_id:
                rec.validity_status = 'invoice'
                rec.is_invoiced = True
            else:
                rec.validity_status = 'tobe'
                rec.is_invoiced = False

    def _get_examination_product_category_domain(self):
        exam_prod_cat = self.env['ir.config_parameter'].sudo().get_param('examination.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', exam_prod_cat)])
        return [('categ_id', '=', prod_cat_obj.id)]

    def _get_insurance_cards_domain(self):
        if self.patient_id.id:
            insurance_ids = self.patient_id.current_insurance_id
            return [('id', 'in', insurance_ids)]

    def _get_accommodation_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('accommodation.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        return [('categ_id', '=', prod_cat_obj.id)]

    name = fields.Char(string="Appointment ID", readonly=True, copy=True)
    is_invoiced = fields.Boolean(copy=False, default=False)
    institution_partner_id = fields.Many2one('res.partner',domain=[('is_institution','=',True)],string="Health Center")
    patient_id = fields.Many2one('medical.patient','Patient',required=True)
    appointment_date = fields.Datetime('Appointment Date',required=True,default=fields.Datetime.now)
    doctor_id = fields.Many2one('medical.physician','Physician',required=False)
    no_invoice = fields.Boolean(string='Invoice exempt',default=False)
    validity_status = fields.Selection([('invoice', 'Invoice Created'), ('tobe', 'To be Invoiced')], string='Status',
                                       compute=_compute_validity_status,
                                       store=False, sort=False,readonly=True,default='tobe')
    consultations_id = fields.Many2one('product.product','Consultation Service',
                                       domain=lambda self: self._get_examination_product_category_domain(), required=True)
    appointment_procedure_ids = fields.One2many('medical.appointment.procedure', 'appointment_id', string='Procedures', required=True)
    appointment_consultation_ids = fields.One2many('medical.appointment.consultation.line', 'appointment_id',
                                                   string='Another Consultations', required=True)
    appointment_investigations_ids = fields.One2many('medical.appointment.investigation', 'appointment_id',
                                                     string='Investigations', required=True)
    prescription_line_id = fields.One2many('medical.prescription.order', 'appointment_id',
                                           string='Services and Lab Investigations', required=True)
    invoice_id = fields.Many2one('account.move', 'Invoice')
    admission_duration = fields.Integer(string="Observation Duration (per hour)")
    accommodation_id = fields.Many2one('product.product', 'Accommodation Service',
                                       domain=lambda self: self._get_accommodation_product_category_domain(), required=False)
    admission_type = fields.Selection([('observation', 'Observation Room')],
                                      required=False, default='observation', readonly=True, string="Admission Type")
    is_discharged = fields.Boolean(copy=False, default=False)
    discharge_datetime = fields.Datetime(string='Discharge Date Time')
    discharge_basis = fields.Selection([('improve', 'Improvement Basis'), ('against', 'Against Medical Advice'),
                                        ('repatriation', 'Repatriation Basis')], string="Discharge Basis")
    refer_to = fields.Char(string="Refer To")
    transportation = fields.Selection([('car', 'Standard Car'), ('ambulance', 'Ambulance')], string="Transportation")
    recommendation = fields.Text(string="Recommendations")
    medication_ids = fields.One2many('medical.inpatient.medication', 'medical_appointment_id', string='Medication')
    discharge_medication_ids = fields.One2many('medical.inpatient.medication', 'medical_discharge_id', string='Medication')
    state = fields.Selection([('requested', 'Requested'), ('admitted', 'Admitted'),
                              ('discharged', 'Discharged')], string="State", default="requested")
    vital_bp = fields.Char(string='Blood Pressure')
    vital_pulse = fields.Char(string='Pulse')
    vital_temp = fields.Char(string='Temperature')
    vital_rr = fields.Char(string='RR')
    vital_oxygen = fields.Char(string='Oxygen Sat.')
    general_appearance = fields.Char('General Appearance',required=True)
    head_neck = fields.Char('Head & Neck',required=True)
    chest = fields.Char('Chest', required=True)
    heart = fields.Char('Abdomen', required=True)
    extremities = fields.Char('Extremities',required=True)
    neurological_examination = fields.Char('Neurological Examination',required=True)
    further_examination = fields.Char('Further examination',required=False)
    invoice_to_insurer = fields.Boolean('Invoice to Insurance')
    medical_prescription_order_ids = fields.One2many('medical.prescription.order','appointment_id',string='Prescription')
    insurer_id = fields.Many2one('medical.insurance', string='Insurance Card', domain=lambda self: self._get_insurance_cards_domain())
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.user.company_id)
    is_company_id_readonly = fields.Boolean(compute='_compute_company_id_readonly')

    @api.depends('company_id')
    def _compute_company_id_readonly(self):
        group_id = self.env['res.groups'].search([('name', '=', 'Can Change Company')])
        is_exists = self.env.user.id in group_id.users.ids
        self.is_company_id_readonly = not is_exists

    @api.onchange('patient_id')
    def onchange_name(self):
        ins_obj = self.env['medical.insurance']
        ins_record = ins_obj.search([('patient_id', '=', self.patient_id.patient_id.id)])
        if len(ins_record) >= 1:
            self.insurer_id = ins_record[0].id
        else:
            self.insurer_id = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medical.appointment.code') or 'APT'
        msg_body = 'Appointment created'
        for msg in self:
            msg.message_post(body=msg_body)
        result = super(MedicalAppointment, self).create(vals)
        return result

    def confirm(self):
        self.write({'state': 'confirmed'})

    def done(self):
        self.write({'state': 'done'})

    def cancel(self):
        self.write({'state': 'cancel'})

    def print_prescription(self):
        return self.env.ref('report_print_prescription').report_action(self)

    def view_patient_invoice(self):
        self.write({'state': 'cancel'})

    def create_invoice(self):
        lab_req_obj = self.env['medical.appointment']
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']

        lab_req = lab_req_obj
        if lab_req.is_invoiced:
            raise UserError(_(' Invoice is Already Exist'))
        if lab_req.no_invoice:
            res = account_invoice_obj.create({'partner_id': lab_req.patient_id.patient_id.id, 'date_invoice': date.today(),
                                              'account_id':lab_req.patient_id.patient_id.property_account_receivable_id.id,
                                              })

            res1 = account_invoice_line_obj.create({'product_id':lab_req.consultations_id.id ,
                                                    'product_uom': lab_req.consultations_id.uom_id.id,
                                                    'name': lab_req.consultations_id.name,
                                                    'product_uom_qty':1,
                                                    'price_unit':lab_req.consultations_id.lst_price,
                                                    'account_id': lab_req.patient_id.patient_id.property_account_receivable_id.id,
                                                    'invoice_id': res.id})

            if res:
                lab_req.write({'is_invoiced': True})
                imd = self.env['ir.model.data']
                action = imd.xmlid_to_object('account.action_invoice_tree1')
                list_view_id = imd.xmlid_to_res_id('account.view_order_form')
                result = {
                    'name': action.name,
                    'help': action.help,
                    'type': action.type,
                    'views': [[list_view_id, 'form']],
                    'target': action.target,
                    'context': action.context,
                    'res_model': action.res_model,
                    'res_id': res.id,
                }
                if res:
                    result['domain'] = "[('id','=',%s)]" % res.id
        else:
            raise UserError(_(' The Appointment is invoice exempt'))
        return result

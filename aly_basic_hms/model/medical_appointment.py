from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError


class MedicalAppointment(models.Model):
    _name = "medical.appointment"
    _inherit = 'mail.thread'
    _order = "name, appointment_date desc"
    _description = 'Medical Appointment Update Notes'

    @api.constrains('appointment_date')
    def date_constrains(self):
        for rec in self:
            if rec.appointment_date.date() > date.today():
                raise ValidationError(_('Update Note Date Must be lower than or equal Today...'))

    def _get_examination_product_category_domain(self):
        exam_prod_cat = self.env['ir.config_parameter'].sudo().get_param('examination.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', exam_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) > 1:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('sale_ok', '=', 1), ('type', '=', 'service'), ('categ_id', '=', prod_cat_obj_id)]

    def _get_insurance_cards_domain(self):
        if self.patient_id.id:
            insurance_ids = self.patient_id.current_insurance_id
            return [('id', 'in', insurance_ids)]

    def _get_accommodation_product_category_domain(self):
        accom_prod_cat = self.env['ir.config_parameter'].sudo().get_param('observation.product_category')
        prod_cat_obj = self.env['product.category'].search([('name', '=', accom_prod_cat)])
        prod_cat_obj_id = 0
        if len(prod_cat_obj) >= 2:
            prod_cat_obj_id = prod_cat_obj[0].id
        else:
            prod_cat_obj_id = prod_cat_obj.id
        return [('categ_id', '=', prod_cat_obj_id)]

    name = fields.Char(string="Appointment ID", readonly=True, copy=True)
    patient_id = fields.Many2one('medical.patient','Patient',required=True)
    appointment_date = fields.Datetime('Appointment Date',required=True,default=fields.Datetime.now)
    doctor_id = fields.Many2one('medical.physician','Physician',required=False)
    consultations_id = fields.Many2one('product.product','Consultation Service',
                                       domain=lambda self: self._get_examination_product_category_domain(), required=True)
    appointment_procedure_ids = fields.One2many('medical.appointment.procedure', 'appointment_id', string='Procedures', required=True)
    appointment_consultation_ids = fields.One2many('medical.appointment.consultation.line', 'appointment_id',
                                                   string='Another Consultations', required=True)
    appointment_investigations_ids = fields.One2many('medical.appointment.investigation', 'appointment_id',
                                                     string='Investigations', required=True)
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
    medication_ids = fields.One2many('medical.inpatient.medication', 'medical_appointment_id', string='Medications')
    discharge_medication_ids = fields.One2many('medical.inpatient.medication', 'medical_discharge_id', string='Home Medications')
    state = fields.Selection([('requested', 'Requested'), ('admitted', 'Admitted'),
                              ('discharged', 'Discharged')], string="State", default="requested")
    vital_bp = fields.Char(string='Blood Pressure',required=True)
    vital_pulse = fields.Char(string='Pulse',required=True)
    vital_temp = fields.Char(string='Temperature',required=True)
    vital_rr = fields.Char(string='RR',required=True)
    vital_oxygen = fields.Char(string='Oxygen Sat.',required=True)
    general_appearance = fields.Char('General Appearance',required=True)
    head_neck = fields.Char('Head & Neck',required=True)
    chest = fields.Char('Chest', required=True)
    heart = fields.Char('Abdomen', required=True)
    extremities = fields.Char('Extremities',required=True)
    neurological_examination = fields.Char('Neurological Examination',required=True)
    further_examination = fields.Char('Further examination',required=False)
    company_id = fields.Many2one('res.company', required=True, readonly=False, default=lambda self: self.env.user.company_id)
    is_company_id_readonly = fields.Boolean(compute='_compute_company_id_readonly')

    @api.depends('company_id')
    def _compute_company_id_readonly(self):
        group_id = self.env['res.groups'].search([('name', '=', 'Can Change Company')])
        is_exists = self.env.user.id in group_id.users.ids
        self.is_company_id_readonly = not is_exists

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

    def view_patient_invoice(self):
        self.write({'state': 'cancel'})


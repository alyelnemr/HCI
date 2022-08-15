from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import UserError


class MedicalInpUpdateNote(models.Model):
    _name = "medical.inp.update.note"
    _description = 'Medical Inpatient Update Notes'

    name = fields.Char(string="Inpatient Update Note ID", readonly=True, copy=True)
    inpatient_id = fields.Many2one('medical.inpatient.registration', domain=[('state', '!=', 'discharged')],
                                   string="Patient", required=True)
    update_note_date = fields.Datetime('Update Note Date',required=True,default=fields.Datetime.now)
    doctor_id = fields.Many2one('medical.physician','Physician',required=False)
    inp_update_note_procedure_ids = fields.One2many('medical.inpatient.procedure', 'inp_update_note_id', string='Procedures',
                                                    required=True)
    inp_update_note_consultation_ids = fields.One2many('medical.inp.update.note.consultation.line', 'inp_update_note_id',
                                                       string='Another Consultations', required=True)
    inp_update_note_investigations_ids = fields.One2many('medical.inpatient.investigation', 'inp_update_note_id',
                                                     string='Investigations', required=True)
    admission_type = fields.Selection([('standard', 'Standard Room'), ('icu', 'ICU')],
                                      required=True, default='standard', string="Admission Type")
    admission_status = fields.Selection([('still', 'is still admitted in'), ('has', 'has been transferred to')],
                                      required=True, default='still', string="Admission Status")
    is_discharged = fields.Boolean(copy=False, default=False)
    discharge_datetime = fields.Datetime(string='Discharge Date Time')
    discharge_basis = fields.Selection([('improve', 'Improvement Basis'), ('against', 'Against Medical Advice'),
                                        ('repatriation', 'Repatriation Basis')], string="Discharge Basis")
    refer_to = fields.Char(string="Refer To")
    transportation = fields.Selection([('car', 'Standard Car'), ('ambulance', 'Ambulance')], string="Transportation")
    recommendation = fields.Text(string="Recommendations")
    medication_ids = fields.One2many('medical.inpatient.medication', 'medical_inp_update_note_id', string='Medication')
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
    abdomen = fields.Char('Abdomen', required=True)
    heart = fields.Char('Heart', required=True)
    extremities = fields.Char('Extremities',required=True)
    neurological_examination = fields.Char('Neurological Examination',required=True)
    further_examination = fields.Char('Further examination',required=False)
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medical.inpatient.update.note')
        result = super(MedicalInpUpdateNote, self).create(vals)
        return result

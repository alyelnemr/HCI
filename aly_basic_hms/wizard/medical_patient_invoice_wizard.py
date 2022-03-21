# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import date,datetime


class MedicalPatientInvoiceWizard(models.TransientModel):
    _name = 'medical.patient.invoice.wizard'
    _description = 'description'

    def create_invoice(self):
        active_ids = self._context.get('active_ids')
        list_of_ids = []
        medical_patient_env = self.env['medical.patient']
        medical_appointment_env = self.env['medical.appointment']
        medical_inpatient_env = self.env['medical.inpatient.registration']
        medical_operation_env = self.env['medical.operation']
        medical_inpatient_update_note_env = self.env['medical.inpatient.update.note']
        account_invoice_obj = self.env['account.move']
        account_invoice_line_obj = self.env['account.move.line']
        ir_property_obj = self.env['ir.property']
        for active_id in active_ids:
            medical_patient_obj = medical_patient_env.browse(active_id)
            list_of_update_notes = medical_appointment_env.search([('patient_id', '=', medical_patient_obj.id)])
            list_of_inpatient = medical_inpatient_env.search([('patient_id', '=', medical_patient_obj.id)])
            list_of_operation = medical_operation_env.search([('patient_id', '=', medical_patient_obj.id)])
            if medical_patient_obj.invoice_id.state == 'posted':
                raise UserError(_('This patient is already invoiced'))
            for inpatient in list_of_inpatient:
                if not inpatient.is_discharged:
                    raise UserError(_('This patient is not discharged, Discharge the patient and then Create Invoice.'))

            partner_id = medical_patient_obj.insurance_company_id.id if medical_patient_obj.is_insurance else medical_patient_obj.patient_id.id or False
            customer_ref = medical_patient_obj.patient_id.id
            partner_shipping_id = medical_patient_obj.patient_id.id

            if medical_patient_obj.is_insurance:
                partner_id = medical_patient_obj.insurance_company_id.id
                partner_shipping_id = medical_patient_obj.insurance_company_id.id

            if not medical_patient_obj.invoice_id.state == 'posted':
                # delete all invoices related to this patient
                all_old_inv = account_invoice_obj.search([('partner_id', '=', partner_id)])
                for inv in all_old_inv:
                        inv.state = 'cancel'
                sale_journals = self.env['account.journal'].search([('type','=','sale')])
                invoice_vals = {
                    'name': self.env['ir.sequence'].next_by_code('medical_patient_inv_seq'),
                    'invoice_origin': medical_patient_obj.name or '',
                    'move_type': 'out_invoice',
                    'partner_id': partner_id or False,
                    'partner_shipping_id': partner_shipping_id or False,
                    'currency_id':medical_patient_obj.patient_id.currency_id.id ,
                    'invoice_payment_term_id': False,
                    'fiscal_position_id': medical_patient_obj.patient_id.property_account_position_id.id,
                    'team_id': False,
                    'invoice_date': date.today(),
                    'company_id': medical_patient_obj.patient_id.company_id.id or False,
                    'ref': customer_ref,
                    'is_insurance': medical_patient_obj.is_insurance,
                    'patient_id': customer_ref
                }
                res = account_invoice_obj.create(invoice_vals)

                list_of_vals = []

                for appointment in list_of_update_notes:
                    if appointment.consultations_id.id:
                        invoice_line_account_id = appointment.consultations_id.property_account_income_id.id \
                                                  or appointment.consultations_id.categ_id.property_account_income_categ_id.id \
                                                  or False
                    if not invoice_line_account_id:
                        inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                    if not invoice_line_account_id:
                        raise UserError(
                            _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                            (appointment.consultations_id.name,))

                    tax_ids = []
                    taxes = appointment.consultations_id.taxes_id.filtered(lambda r: not appointment.consultations_id.company_id or r.company_id == appointment.consultations_id.company_id)
                    tax_ids = taxes.ids
                    invoice_line_vals = {
                        # 'name': appointment.consultations_id.name or '',
                        'name': 'Update Note - Consultation' or '',
                        'account_id': invoice_line_account_id,
                        'price_unit': appointment.consultations_id.lst_price,
                        'product_uom_id': appointment.consultations_id.uom_id.id,
                        'quantity': 1,
                        'tax_ids': tax_ids,
                        'product_id': appointment.consultations_id.id,
                    }
                    list_of_vals.append((0, 0, invoice_line_vals))

                    # accommodation of update note (management tab)
                    if appointment.accommodation_id:
                        invoice_line_account_id = appointment.accommodation_id.property_account_income_id.id \
                                                  or appointment.accommodation_id.categ_id.property_account_income_categ_id.id \
                                                  or False
                        if not invoice_line_account_id:
                            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (appointment.accommodation_id.name,))

                        tax_ids = []
                        taxes = appointment.accommodation_id.taxes_id.filtered(lambda r: not appointment.accommodation_id.company_id or r.company_id == appointment.accommodation_id.company_id)
                        tax_ids = taxes.ids
                        invoice_line_vals = {
                            # 'name': appointment.accommodation_id.name or '',
                            'name': 'Update Note - Observation' or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': appointment.accommodation_id.lst_price,
                            'product_uom_id': appointment.accommodation_id.uom_id.id,
                            'quantity': appointment.admission_duration or 1,
                            'tax_ids': tax_ids,
                            'product_id': appointment.accommodation_id.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                    for p_line in appointment.appointment_procedure_ids:

                        invoice_line_account_id = False
                        if p_line.product_id.id:
                            invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_line.product_id.name,))

                        tax_ids = []
                        taxes = p_line.product_id.taxes_id.filtered(
                            lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_line.product_id.display_name or '',
                            'name': 'Update Note - Procedures' or '',
                            'move_name': p_line.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_line.product_id.lst_price,
                            'product_uom_id': p_line.product_id.uom_id.id,
                            'quantity': p_line.quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_line.product_id.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                    for p_cons_line in appointment.appointment_consultation_ids:

                        invoice_line_account_id = False
                        if p_cons_line.product_id.id:
                            invoice_line_account_id = p_cons_line.product_id.property_account_income_id.id \
                                                      or p_cons_line.product_id.categ_id.property_account_income_categ_id.id \
                                                      or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                          'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_cons_line.product_id.name,))

                        tax_ids = []
                        taxes = p_cons_line.product_id.taxes_id.filtered(
                            lambda r: not p_cons_line.product_id.company_id or r.company_id == p_cons_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_cons_line.product_id.display_name or '',
                            'name': 'Update Note - Another Consultations' or '',
                            'move_name': p_cons_line.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_cons_line.product_id.lst_price,
                            'product_uom_id': p_cons_line.product_id.uom_id.id,
                            'quantity': p_cons_line.quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_cons_line.product_id.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                    for p_line in appointment.appointment_investigations_ids:

                        invoice_line_account_id = False
                        if p_line.product_id.id:
                            invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_line.product_id.name,))

                        tax_ids = []
                        taxes = p_line.product_id.taxes_id.filtered(lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_line.product_id.display_name or '',
                            'name': 'Update Note - Investigations' or '',
                            'move_name': p_line.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_line.product_id.lst_price,
                            'product_uom_id': p_line.product_id.uom_id.id,
                            'quantity': p_line.quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_line.product_id.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))
                    for p_line in appointment.medication_ids:

                        invoice_line_account_id = False
                        if p_line.medical_medicament_id.product_id.id:
                            invoice_line_account_id = p_line.medical_medicament_id.product_id.property_account_income_id.id or p_line.medical_medicament_id.product_id.categ_id.property_account_income_categ_id.id or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                          'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_line.medical_medicament_id.product_id.name,))

                        tax_ids = []
                        taxes = p_line.medical_medicament_id.product_id.taxes_id.filtered(lambda
                                                                                              r: not p_line.medical_medicament_id.product_id.company_id or r.company_id == p_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_line.medical_medicament_id.product_id.display_name or '',
                            'name': 'Update Note - Medications' or '',
                            'move_name': p_line.medical_medicament_id.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_line.medical_medicament_id.product_id.lst_price,
                            'product_uom_id': p_line.medical_medicament_id.product_id.uom_id.id,
                            'quantity': p_line.medicine_quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_line.medical_medicament_id.product_id.id,
                        }
                        # delete medicines from the invoice
                        #list_of_vals.append((0, 0, invoice_line_vals))

                for inpatient in list_of_inpatient:
                    if inpatient.transportation_service:
                        invoice_line_account_id = inpatient.transportation_service.property_account_income_id.id \
                                                  or inpatient.transportation_service.categ_id.property_account_income_categ_id.id \
                                                  or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (inpatient.transportation_service.name,))

                        tax_ids = []
                        taxes = inpatient.transportation_service.taxes_id.filtered(
                            lambda r: not inpatient.transportation_service.company_id or r.company_id == inpatient.transportation_service.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            'name': 'Inpatient - Transportation Service' or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': inpatient.transportation_service.lst_price,
                            'product_uom_id': inpatient.transportation_service.uom_id.id,
                            'quantity': 1,
                            'tax_ids': tax_ids,
                            'product_id': inpatient.transportation_service.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                    if inpatient.transportation_service2:
                        invoice_line_account_id = inpatient.transportation_service2.property_account_income_id.id \
                                                  or inpatient.transportation_service2.categ_id.property_account_income_categ_id.id \
                                                  or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (inpatient.transportation_service2.name,))

                        tax_ids = []
                        taxes = inpatient.transportation_service2.taxes_id.filtered(
                            lambda r: not inpatient.transportation_service2.company_id or r.company_id == inpatient.transportation_service2.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            'name': 'Inpatient - Transportation Service' or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': inpatient.transportation_service2.lst_price,
                            'product_uom_id': inpatient.transportation_service2.uom_id.id,
                            'quantity': 1,
                            'tax_ids': tax_ids,
                            'product_id': inpatient.transportation_service2.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                    for p_line in inpatient.discharge_medication_ids:

                        invoice_line_account_id = False
                        if p_line.medical_medicament_id.product_id.id:
                            invoice_line_account_id = p_line.medical_medicament_id.product_id.property_account_income_id.id or p_line.medical_medicament_id.product_id.categ_id.property_account_income_categ_id.id or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                          'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_line.medical_medicament_id.product_id.name,))

                        tax_ids = []
                        taxes = p_line.medical_medicament_id.product_id.taxes_id.filtered(lambda
                                                                                              r: not p_line.medical_medicament_id.product_id.company_id or r.company_id == p_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_line.medical_medicament_id.product_id.display_name or '',
                            'name': 'Inpatient Discharge Medications' or '',
                            'move_name': p_line.medical_medicament_id.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_line.medical_medicament_id.product_id.lst_price,
                            'product_uom_id': p_line.medical_medicament_id.product_id.uom_id.id,
                            'quantity': p_line.medicine_quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_line.medical_medicament_id.product_id.id,
                        }

                        # delete medicines from the invoice
                        #list_of_vals.append((0, 0, invoice_line_vals))

                    for inp_acc in inpatient.bed_transfers_ids:
                        for p_bed in inp_acc.acc_service_ids:

                            invoice_line_account_id = False
                            if p_bed.accommodation_service.id:
                                invoice_line_account_id = p_bed.accommodation_service.property_account_income_id.id \
                                                          or p_bed.accommodation_service.categ_id.property_account_income_categ_id.id \
                                                          or False
                            if not invoice_line_account_id:
                                invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                            if not invoice_line_account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                    (p_bed.accommodation_service.name,))

                            tax_ids = []
                            taxes = p_bed.accommodation_service.taxes_id.filtered(
                                lambda r: not p_bed.accommodation_service.company_id or r.company_id == p_bed.accommodation_service.company_id)
                            tax_ids = taxes.ids

                            invoice_line_vals = {
                                # 'name': p_bed.accommodation_service.display_name or '',
                                'name': 'Inpatient Bed Transfer Accommodation' or '',
                                'move_name': p_bed.accommodation_service.display_name or '',
                                'account_id': invoice_line_account_id,
                                'price_unit': p_bed.accommodation_service.lst_price,
                                'product_uom_id': p_bed.accommodation_service.uom_id.id,
                                'quantity': p_bed.accommodation_qty,
                                'tax_ids': tax_ids,
                                'product_id': p_bed.accommodation_service.id,
                            }
                            list_of_vals.append((0, 0, invoice_line_vals))

                    for appointment in inpatient.inpatient_update_note_ids:

                        for p_line in appointment.inp_update_note_procedure_ids:

                            invoice_line_account_id = False
                            if p_line.product_id.id:
                                invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                            if not invoice_line_account_id:
                                invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                              'product.category')
                            if not invoice_line_account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                    (p_line.product_id.name,))

                            tax_ids = []
                            taxes = p_line.product_id.taxes_id.filtered(
                                lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                            tax_ids = taxes.ids

                            invoice_line_vals = {
                                # 'name': p_line.product_id.display_name or '',
                                'name': 'IP Update Note - Procedures' or '',
                                'move_name': p_line.product_id.display_name or '',
                                'account_id': invoice_line_account_id,
                                'price_unit': p_line.product_id.lst_price,
                                'product_uom_id': p_line.product_id.uom_id.id,
                                'quantity': p_line.quantity,
                                'tax_ids': tax_ids,
                                'product_id': p_line.product_id.id,
                            }
                            list_of_vals.append((0, 0, invoice_line_vals))

                        for p_cons_line in appointment.inp_update_note_consultation_ids:

                            invoice_line_account_id = False
                            if p_cons_line.product_id.id:
                                invoice_line_account_id = p_cons_line.product_id.property_account_income_id.id \
                                                          or p_cons_line.product_id.categ_id.property_account_income_categ_id.id \
                                                          or False
                            if not invoice_line_account_id:
                                invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                              'product.category')
                            if not invoice_line_account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                    (p_cons_line.product_id.name,))

                            tax_ids = []
                            taxes = p_cons_line.product_id.taxes_id.filtered(
                                lambda
                                    r: not p_cons_line.product_id.company_id or r.company_id == p_cons_line.product_id.company_id)
                            tax_ids = taxes.ids

                            invoice_line_vals = {
                                # 'name': p_cons_line.product_id.display_name or '',
                                'name': 'Update Note - Another Consultations' or '',
                                'move_name': p_cons_line.product_id.display_name or '',
                                'account_id': invoice_line_account_id,
                                'price_unit': p_cons_line.product_id.lst_price,
                                'product_uom_id': p_cons_line.product_id.uom_id.id,
                                'quantity': p_cons_line.quantity,
                                'tax_ids': tax_ids,
                                'product_id': p_cons_line.product_id.id,
                            }
                            list_of_vals.append((0, 0, invoice_line_vals))

                        for p_line in appointment.inp_update_note_investigations_ids:

                            invoice_line_account_id = False
                            if p_line.product_id.id:
                                invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                            if not invoice_line_account_id:
                                invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                              'product.category')
                            if not invoice_line_account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                    (p_line.product_id.name,))

                            tax_ids = []
                            taxes = p_line.product_id.taxes_id.filtered(
                                lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                            tax_ids = taxes.ids

                            invoice_line_vals = {
                                # 'name': p_line.product_id.display_name or '',
                                'name': 'Update Note - Investigations' or '',
                                'move_name': p_line.product_id.display_name or '',
                                'account_id': invoice_line_account_id,
                                'price_unit': p_line.product_id.lst_price,
                                'product_uom_id': p_line.product_id.uom_id.id,
                                'quantity': p_line.quantity,
                                'tax_ids': tax_ids,
                                'product_id': p_line.product_id.id,
                            }
                            list_of_vals.append((0, 0, invoice_line_vals))

                        for p_line in appointment.medication_ids:

                            invoice_line_account_id = False
                            if p_line.medical_medicament_id.product_id.id:
                                invoice_line_account_id = p_line.medical_medicament_id.product_id.property_account_income_id.id or p_line.medical_medicament_id.product_id.categ_id.property_account_income_categ_id.id or False
                            if not invoice_line_account_id:
                                invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id',
                                                                              'product.category')
                            if not invoice_line_account_id:
                                raise UserError(
                                    _(
                                        'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                    (p_line.medical_medicament_id.product_id.name,))

                            tax_ids = []
                            taxes = p_line.medical_medicament_id.product_id.taxes_id.filtered(lambda
                                                                                                  r: not p_line.medical_medicament_id.product_id.company_id or r.company_id == p_line.product_id.company_id)
                            tax_ids = taxes.ids

                            invoice_line_vals = {
                                # 'name': p_line.medical_medicament_id.product_id.display_name or '',
                                'name': 'Update Note - Medications' or '',
                                'move_name': p_line.medical_medicament_id.product_id.display_name or '',
                                'account_id': invoice_line_account_id,
                                'price_unit': p_line.medical_medicament_id.product_id.lst_price,
                                'product_uom_id': p_line.medical_medicament_id.product_id.uom_id.id,
                                'quantity': p_line.medicine_quantity,
                                'tax_ids': tax_ids,
                                'product_id': p_line.medical_medicament_id.product_id.id,
                            }
                            # delete medicines from the invoice
                            #list_of_vals.append((0, 0, invoice_line_vals))

                for operation in list_of_operation:
                    for p_line in operation.operation_line_ids:

                        invoice_line_account_id = False
                        if p_line.product_id.id:
                            invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                        if not invoice_line_account_id:
                            invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                        if not invoice_line_account_id:
                            raise UserError(
                                _(
                                    'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                                (p_line.product_id.name,))

                        tax_ids = []
                        taxes = p_line.product_id.taxes_id.filtered(
                            lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                        tax_ids = taxes.ids

                        invoice_line_vals = {
                            # 'name': p_line.product_id.display_name or '',
                            'name': 'Post Operative Investigations' or '',
                            'move_name': p_line.product_id.display_name or '',
                            'account_id': invoice_line_account_id,
                            'price_unit': p_line.product_id.lst_price,
                            'product_uom_id': p_line.product_id.uom_id.id,
                            'quantity': p_line.quantity,
                            'tax_ids': tax_ids,
                            'product_id': p_line.product_id.id,
                        }
                        list_of_vals.append((0, 0, invoice_line_vals))

                for p_line in medical_patient_obj.disposable_ids:

                    invoice_line_account_id = False
                    if p_line.product_id.id:
                        invoice_line_account_id = p_line.product_id.property_account_income_id.id or p_line.product_id.categ_id.property_account_income_categ_id.id or False
                    if not invoice_line_account_id:
                        invoice_line_account_id = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                    if not invoice_line_account_id:
                        raise UserError(
                            _(
                                'There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                            (p_line.product_id.name,))

                    tax_ids = []
                    taxes = p_line.product_id.taxes_id.filtered(
                        lambda r: not p_line.product_id.company_id or r.company_id == p_line.product_id.company_id)
                    tax_ids = taxes.ids

                    invoice_line_vals = {
                        # 'name': p_line.product_id.display_name or '',
                        'name': 'Disposables and Supplies' or '',
                        'move_name': p_line.product_id.display_name or '',
                        'account_id': invoice_line_account_id,
                        'price_unit': p_line.product_id.lst_price,
                        'product_uom_id': p_line.product_id.uom_id.id,
                        'quantity': p_line.quantity,
                        'tax_ids': tax_ids,
                        'product_id': p_line.product_id.id,
                    }
                    list_of_vals.append((0, 0, invoice_line_vals))

                res1 = res.write({'invoice_line_ids': list_of_vals})

                medical_patient_obj.invoice_id = res
                medical_patient_obj.with_context({'come_from_invoice': True}).is_opened_visit = False

                list_of_ids.append(res.id)
                if list_of_ids:
                        imd = self.env['ir.model.data']
                        lab_req_obj_brw = medical_patient_env.browse(self._context.get('active_id'))
                        action = imd.sudo().xmlid_to_object('account.action_move_out_invoice_type')
                        list_view_id = imd.sudo().xmlid_to_res_id('account.view_invoice_tree')
                        form_view_id = imd.sudo().xmlid_to_res_id('account.view_move_form')
                        result = {
                                    'name': action.name,
                                    'help': action.help,
                                    'type': action.type,
                                    'views': [ [list_view_id, 'tree'], [form_view_id, 'form']],
                                    'target': action.target,
                                    'context': action.context,
                                    'res_model': action.res_model,

                                    }
                        if list_of_ids:
                            result['domain'] = "[('id','in',%s)]" % list_of_ids
            else:
                raise UserError(_(' The Patient is not invoiced, clear Invoice ID   '))
            return result

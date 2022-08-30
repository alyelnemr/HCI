# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from datetime import date,datetime


class MedicalPatientSaleOrderWizard(models.TransientModel):
    _name = "medical.patient.sale.order.wizard"
    _description = 'Medical Patient Sale Order Wizard'

    def create_invoice(self):
        active_ids = self._context.get('active_ids')
        list_of_ids = []
        medical_patient_env = self.env['medical.patient']
        medical_appointment_env = self.env['medical.appointment']
        medical_inpatient_env = self.env['medical.inpatient.registration']
        medical_operation_env = self.env['medical.operation']
        account_invoice_obj = self.env['sale.order']
        account_invoice_line_obj = self.env['sale.order.line']
        for active_id in active_ids:
            medical_patient_obj = medical_patient_env.browse(active_id)
            has_insurance_group = self.env.user.has_group('aly_basic_hms.aly_group_insurance')
            has_inpatient_group = self.env.user.has_group('aly_basic_hms.aly_group_inpatient')
            if medical_patient_obj.is_insurance and not has_insurance_group:
                raise UserError(_('You don''t have permission to create invoice for insurance patients!'))
            if not medical_patient_obj.is_opened_visit:
                raise UserError(_('This patient has no open visit'))
            if medical_patient_obj.invoice_id.state == 'posted' or medical_patient_obj.order_id.state == 'sale' or medical_patient_obj.order_id.state == 'done':
                raise UserError(_('This patient''s invoice is posted, you can unpost or cancel the previous invoice and then create invoice'))

            if medical_patient_obj.invoice_id:
                medical_patient_obj.invoice_id.sudo().unlink()
            if medical_patient_obj.order_id:
                medical_patient_obj.order_id.sudo().unlink()
            medical_patient_obj.invoice_id = False
            medical_patient_obj.order_id = False
            list_of_update_notes = medical_appointment_env.search([('patient_id', '=', medical_patient_obj.id)])
            list_of_inpatient = []
            if has_inpatient_group:
                list_of_inpatient = medical_inpatient_env.search([('patient_id', '=', medical_patient_obj.id)])
                list_of_operation = medical_operation_env.search([('patient_id', '=', medical_patient_obj.id)])
                # for inpatient in list_of_inpatient:
                #     if not inpatient.is_discharged:
                #         inpatient.discharge_date = datetime.today().date()
                        # raise UserError(_('This patient is not discharged, Discharge the patient and then Create Invoice.'))

            partner_id = medical_patient_obj.insurance_company_id.id if medical_patient_obj.is_insurance else medical_patient_obj.partner_id.id or False
            customer_ref = medical_patient_obj.id
            price_list_id = medical_patient_obj.insurance_company_id.property_product_pricelist.id if medical_patient_obj.is_insurance else medical_patient_obj.partner_id.property_product_pricelist.id or False
            warehouse_id = self.env['stock.warehouse'].search([('company_id','in',[medical_patient_obj.company_id.id, False])])[0].id

            if medical_patient_obj.is_insurance:
                partner_id = medical_patient_obj.insurance_company_id.id
                partner_shipping_id = medical_patient_obj.insurance_company_id.id

            if not medical_patient_obj.invoice_id.state == 'posted':
                # delete all invoices related to this patient
                all_old_inv = account_invoice_obj.search([('partner_id', '=', partner_id)])
                for inv in all_old_inv:
                        inv.state = 'cancel'
                for inv in all_old_inv.invoice_ids:
                        inv.state = 'cancel'

                invoice_vals = {
                    'name': self.env['ir.sequence'].next_by_code('medical_patient_inv_seq'),
                    'partner_id': partner_id or False,
                    'partner_invoice_id': partner_id or False,
                    'partner_shipping_id': partner_id or False,
                    'picking_policy': 'direct',
                    'warehouse_id': warehouse_id,
                    'pricelist_id': price_list_id,
                    'date_order': date.today(),
                    'company_id': medical_patient_obj.company_id.id or False,
                    'is_insurance': medical_patient_obj.is_insurance,
                    'patient_id': customer_ref
                }
                res = account_invoice_obj.create(invoice_vals)

                list_of_vals = []

                for appointment in list_of_update_notes:
                    invoice_line_vals = {
                        'name': 'Update Note - Consultation' or '',
                        'product_uom_qty': 1,
                        'price_unit': appointment.consultations_id.lst_price,
                        'product_uom': appointment.consultations_id.uom_id.id,
                        'product_id': appointment.consultations_id.id,
                        'order_id': res.id
                    }
                    res1 = account_invoice_line_obj.create(invoice_line_vals)

                    # accommodation of update note (management tab)
                    if appointment.accommodation_id:
                        invoice_line_vals = {
                            'name': 'Update Note - Observation' or '',
                            'product_uom_qty': appointment.admission_duration or 1,
                            'product_uom': appointment.accommodation_id.uom_id.id,
                            'price_unit': appointment.accommodation_id.lst_price,
                            'product_id': appointment.accommodation_id.id,
                            'order_id': res.id
                        }
                        res1 = account_invoice_line_obj.create(invoice_line_vals)

                    for p_line in appointment.appointment_procedure_ids:
                        invoice_line_vals = {
                            'name': 'Update Note - Procedures' or '',
                            'product_uom_qty': p_line.quantity,
                            'product_uom': p_line.product_id.uom_id.id,
                            'price_unit': p_line.product_id.lst_price,
                            'product_id': p_line.product_id.id,
                            'order_id': res.id
                        }
                        res1 = account_invoice_line_obj.create(invoice_line_vals)

                    for p_cons_line in appointment.appointment_consultation_ids:
                        invoice_line_vals = {
                            'name': 'Update Note - Another Consultations' or '',
                            'product_uom_qty': p_cons_line.quantity,
                            'product_uom': p_cons_line.product_id.uom_id.id,
                            'price_unit': p_cons_line.product_id.lst_price,
                            'product_id': p_cons_line.product_id.id,
                            'order_id': res.id
                        }
                        res1 = account_invoice_line_obj.create(invoice_line_vals)

                    for p_line in appointment.appointment_investigations_ids:
                        invoice_line_vals = {
                            'name': 'Update Note - Investigations' or '',
                            'product_uom_qty': p_line.quantity,
                            'product_uom': p_line.product_id.uom_id.id,
                            'price_unit': p_line.product_id.lst_price,
                            'product_id': p_line.product_id.id,
                            'order_id': res.id
                        }
                        res1 = account_invoice_line_obj.create(invoice_line_vals)

                    for p_line in appointment.medication_ids:
                        invoice_line_vals = {
                            'name': 'Update Note - Medications' or '',
                            'product_uom_qty': p_line.medicine_quantity,
                            'product_uom': p_line.product_id.uom_id.id,
                            'price_unit': 0,
                            'product_id': p_line.product_id.id,
                            'order_id': res.id
                        }
                        res1 = account_invoice_line_obj.create(invoice_line_vals)

                if has_inpatient_group:
                    for inpatient in list_of_inpatient:
                        if inpatient.transportation_service:
                            invoice_line_vals = {
                                'name': 'Inpatient - Transportation Service' or '',
                                'product_uom_qty': 1,
                                'product_uom': inpatient.transportation_service.uom_id.id,
                                'price_unit': inpatient.transportation_service.lst_price,
                                'product_id': inpatient.transportation_service.id,
                                'order_id': res.id
                            }
                            res1 = account_invoice_line_obj.create(invoice_line_vals)

                        if inpatient.transportation_service2:
                            invoice_line_vals = {
                                'name': 'Inpatient - Transportation Service' or '',
                                'product_uom_qty': 1,
                                'product_uom': inpatient.transportation_service2.uom_id.id,
                                'price_unit': inpatient.transportation_service2.lst_price,
                                'product_id': inpatient.transportation_service2.id,
                                'order_id': res.id
                            }
                            res1 = account_invoice_line_obj.create(invoice_line_vals)

                        for p_line in inpatient.discharge_medication_ids:
                            invoice_line_vals = {
                                'name': 'Inpatient Discharge Medications' or '',
                                'product_uom_qty': p_line.medicine_quantity,
                                'product_uom': p_line.product_id.uom_id.id,
                                'price_unit': 0,
                                'product_id': p_line.product_id.id,
                                'order_id': res.id
                            }
                            res1 = account_invoice_line_obj.create(invoice_line_vals)

                        for inp_acc in inpatient.bed_transfers_ids:
                            for p_bed in inp_acc.acc_service_ids:
                                invoice_line_vals = {
                                    'name': 'Inpatient Bed Transfer Accommodation' or '',
                                    'product_uom_qty': p_bed.accommodation_qty,
                                    'product_uom': p_bed.accommodation_service.uom_id.id,
                                    'price_unit': p_bed.accommodation_service.lst_price,
                                    'product_id': p_bed.accommodation_service.id,
                                    'order_id': res.id
                                }
                                res1 = account_invoice_line_obj.create(invoice_line_vals)

                        for appointment in inpatient.inpatient_update_note_ids:

                            for p_line in appointment.inp_update_note_procedure_ids:
                                invoice_line_vals = {
                                    'name': 'IP Update Note - Procedures' or '',
                                    'product_uom_qty': p_line.quantity,
                                    'product_uom': p_line.product_id.uom_id.id,
                                    'price_unit': p_line.product_id.lst_price,
                                    'product_id': p_line.product_id.id,
                                    'order_id': res.id
                                }
                                res1 = account_invoice_line_obj.create(invoice_line_vals)

                            for p_cons_line in appointment.inp_update_note_consultation_ids:
                                invoice_line_vals = {
                                    'name': 'Update Note - Another Consultations' or '',
                                    'product_uom_qty': p_cons_line.quantity,
                                    'product_uom': p_cons_line.product_id.uom_id.id,
                                    'price_unit': p_cons_line.product_id.lst_price,
                                    'product_id': p_cons_line.product_id.id,
                                    'order_id': res.id
                                }
                                res1 = account_invoice_line_obj.create(invoice_line_vals)

                            for p_line in appointment.inp_update_note_investigations_ids:
                                invoice_line_vals = {
                                    'name': 'Update Note - Investigations' or '',
                                    'product_uom_qty': p_line.quantity,
                                    'product_uom': p_line.product_id.uom_id.id,
                                    'price_unit': p_line.product_id.lst_price,
                                    'product_id': p_line.product_id.id,
                                    'order_id': res.id
                                }
                                res1 = account_invoice_line_obj.create(invoice_line_vals)

                            for p_line in appointment.medication_ids:
                                invoice_line_vals = {
                                    'name': 'Update Note - Medications' or '',
                                    'product_uom_qty': p_line.medicine_quantity,
                                    'product_uom': p_line.product_id.uom_id.id,
                                    'price_unit': 0,
                                    'product_id': p_line.product_id.id,
                                    'order_id': res.id
                                }
                                res1 = account_invoice_line_obj.create(invoice_line_vals)

                    for operation in list_of_operation:
                        for p_line in operation.operation_line_ids:
                            invoice_line_vals = {
                                'name': 'Post Operative Investigations' or '',
                                'product_uom_qty': p_line.quantity,
                                'product_uom': p_line.product_id.uom_id.id,
                                'price_unit': p_line.product_id.lst_price,
                                'product_id': p_line.product_id.id,
                                'order_id': res.id
                            }
                            res1 = account_invoice_line_obj.create(invoice_line_vals)

                for p_line in medical_patient_obj.disposable_ids:
                    invoice_line_vals = {
                        'name': 'Disposables and Supplies' or '',
                        'product_uom_qty': p_line.quantity,
                        'product_uom': p_line.product_id.uom_id.id,
                        'price_unit': p_line.product_id.lst_price,
                        'product_id': p_line.product_id.id,
                        'order_id': res.id
                    }
                    res1 = account_invoice_line_obj.create(invoice_line_vals)

                aly_enable_service_charge = medical_patient_obj.company_id.aly_enable_service_charge
                if aly_enable_service_charge:
                    aly_service_product_id = int(medical_patient_obj.company_id.aly_service_product_id)
                    invoice_line_vals = {
                        'name': 'Service Charges' or '',
                        'product_uom_qty': 1,
                        'price_unit': 0,
                        'product_id': aly_service_product_id,
                        'order_id': res.id
                    }
                    res1 = account_invoice_line_obj.create(invoice_line_vals)

                # res1 = account_invoice_line_obj.create({'order_line': list_of_vals})

                res.update_prices()
                for item in res.order_line:
                    if item.product_id.categ_id and item.product_id.categ_id.name == 'Medicines':
                        item.price_unit = 0
                medical_patient_obj.order_id = res
                medical_patient_obj.order_id = res
                medical_patient_obj.with_context({'come_from_invoice': True}).is_opened_visit = False

                list_of_ids.append(res.id)
                if list_of_ids:
                    imd = self.env['ir.model.data']
                    lab_req_obj_brw = medical_patient_env.browse(self._context.get('active_id'))
                    action = imd.sudo().xmlid_to_object('sale.view_quotation_tree')
                    list_view_id = imd.sudo().xmlid_to_res_id('sale.view_quotation_tree')
                    form_view_id = imd.sudo().xmlid_to_res_id('account.view_quotation_form')
                    result = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                                'title': _(
                                    "Invoice Created Successfully for Patient [%s] with Invoice Number [%s]" % (medical_patient_obj.name, res.name)
                                ),
                                'type': 'success',
                                'sticky': True,
                                'next': {'type': 'ir.actions.act_window_close'},
                            },
                    }
            else:
                raise UserError(_(' The Patient is not invoiced, clear Invoice ID   '))
            return result

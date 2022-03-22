
from odoo import api, models


class MedicalInvoiceTemplate(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_invoice_template'
    _description = 'description'

    def get_sorting(self, record):
        my_list = []
        i = 0
        for app in record.update_note_ids:
            my_list.append(
                {
                    'date': app.appointment_date.date(),
                    'obj_type': 'app',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
        i = 0
        # inpatient_update_note_ids
        for app in record.inpatient_ids:
            my_list.append(
                {
                    'date': app.admission_date,
                    'obj_type': 'inp',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
            for inp in app.inpatient_update_note_ids:
                my_list.append(
                    {
                        'date': inp.update_note_date.date(),
                        'obj_type': 'inp_up',
                        'order_in_list': i,
                        'obj_id': inp
                    })
                i += 1
            i = 0
        i = 0
        for app in record.operation_ids:
            my_list.append(
                {
                    'date': app.time_in.date(),
                    'obj_type': 'op',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
        i = 0
        my_list_sorted = sorted(my_list, key=lambda a: (a['date']))

        return my_list_sorted

    @api.model
    def _get_report_values(self, docids, data=None):
        model = 'account.move'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].browse(docids)
        # sorted_data = self.get_sorting(docs.partner_id.patient_id)
        is_draft = docs.state == 'draft'
        sorted_inpatient_ids = sorted(docs.patient_id.inpatient_ids, key=lambda a: a.admission_date)
        min_admission_date = sorted_inpatient_ids[0].admission_date if len(sorted_inpatient_ids) > 0 else False
        min_discharge_date = sorted_inpatient_ids[0].discharge_datetime.date() if len(sorted_inpatient_ids) > 0 else False
        is_discharged = docs.patient_id.inpatient_ids[0].is_discharged if len(sorted_inpatient_ids) > 0 else False
        var_discount = 0
        var_disposable = 0
        var_prosthetics = 0
        for line in docs.invoice_line_ids:
            if line.product_id.categ_id.name == 'Prosthetics':
                var_prosthetics += line.price_subtotal
            if line.product_id.categ_id.name == 'Disposables':
                var_disposable += line.price_subtotal
        var_subtotal = docs.amount_untaxed - (var_disposable + var_prosthetics) if (docs.amount_untaxed - (var_disposable + var_prosthetics)) >= 1 else 0
        var_discount_percent = docs.discount_total if docs.discount_total and var_subtotal > 0 else 0
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'min_admission_date': min_admission_date,
            'min_discharge_date': min_discharge_date,
            'is_discharged': is_discharged,
            'report_title': 'Primary Medical Report',
            'is_draft': is_draft,
            'var_prosthetics': var_prosthetics,
            'var_disposable': var_disposable,
            'var_subtotal': var_subtotal,
            'var_discount': var_discount,
            'var_discount_percent': var_discount_percent
        }

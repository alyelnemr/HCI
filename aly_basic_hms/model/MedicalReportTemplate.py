
from odoo import api, models
from datetime import date

class MedicalReportTemplate(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report'

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
        model = 'medical.patient'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].browse(docids)
        sorted_data = self.get_sorting(docs)
        sorted_update_note = sorted(docs.update_note_ids, key=lambda a: a.appointment_date)
        min_update_note_date = sorted_update_note[0].appointment_date.date() if len(sorted_update_note) > 0 else date.today()
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged
        }


class MedicalReportTemplateUpdate(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report_update'

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
        model = 'medical.patient'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].browse(docids)
        sorted_data = self.get_sorting(docs)
        sorted_update_note = sorted(docs.update_note_ids, key=lambda a: a.appointment_date)
        min_update_note_date = sorted_update_note[0].appointment_date.date() if len(sorted_update_note) > 0 else date.today()
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged
        }


class MedicalReportTemplatePrimary(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report_primary'

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
        model = 'medical.patient'
        active_id = self.env.context.get('active_id')
        docs = self.env[model].browse(docids)
        sorted_data = self.get_sorting(docs)
        sorted_update_note = sorted(docs.update_note_ids, key=lambda a: a.appointment_date)
        min_update_note_date = sorted_update_note[0].appointment_date.date() if len(sorted_update_note) > 0 else date.today()
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged
        }


from odoo import api, models
from datetime import date, datetime, timezone
import pytz


class MedicalReportTemplate(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report'
    _description = 'description'

    def get_sorting(self, record):
        my_list = []
        i = 0
        for app in record.update_note_ids:
            my_list.append(
                {
                    'date': app.appointment_date,
                    'obj_type': 'app',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
        i = 0
        # inpatient_update_note_ids
        for app in record.inpatient_ids:
            admission_date = datetime.combine(app.admission_date, datetime.min.time())
            # my_list.append(
            #     {
            #         'date': admission_date,
            #         'obj_type': 'inp',
            #         'order_in_list': i,
            #         'obj_id': app
            #     })
            # i += 1
            for inp in app.inpatient_update_note_ids:
                my_list.append(
                    {
                        'date': inp.update_note_date,
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
                    'date': app.time_in,
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
        docs = self.env[model].sudo().browse(docids)
        sorted_data = self.get_sorting(docs)
        user_tz = self.env.user.tz or pytz.utc

        local = pytz.timezone(user_tz)
        min_date_str = ''
        if sorted_data:
            if sorted_data[0]['obj_type'] == 'app':
                min_date_str = sorted_data[0]['obj_id'].appointment_date
            if sorted_data[0]['obj_type'] == 'inp_up':
                min_date_str = sorted_data[0]['obj_id'].update_note_date
            if sorted_data[0]['obj_type'] == 'op':
                min_date_str = sorted_data[0]['obj_id'].time_in
        min_date = pytz.utc.localize(min_date_str).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if isinstance(min_date_str, datetime) else min_date_str.strftime("%d/%m/%Y %H:%M:%S")
        var_room_number = str(docs.room_number)
        today_now = datetime.now()
        min_update_note_date = min_date if min_date else today_now.strftime("%d/%m/%Y %H:%M:%S")
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        discharge_datetime = pytz.utc.localize(docs.inpatient_ids[0].discharge_datetime).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if len(docs.inpatient_ids) > 0 and is_discharged else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'var_room_number': var_room_number,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged,
            'discharge_datetime': discharge_datetime,
            'report_title': 'Final Medical Report'
        }


class MedicalReportTemplateUpdate(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report_update'
    _description = 'description'

    def get_sorting(self, record):
        my_list = []
        i = 0
        for app in record.update_note_ids:
            my_list.append(
                {
                    'date': app.appointment_date,
                    'obj_type': 'app',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
        i = 0
        # inpatient_update_note_ids
        for app in record.inpatient_ids:
            admission_date = datetime.combine(app.admission_date, datetime.min.time())
            # my_list.append(
            #     {
            #         'date': admission_date,
            #         'obj_type': 'inp',
            #         'order_in_list': i,
            #         'obj_id': app
            #     })
            # i += 1
            for inp in app.inpatient_update_note_ids:
                my_list.append(
                    {
                        'date': inp.update_note_date,
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
                    'date': app.time_in,
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
        docs = self.env[model].sudo().browse(docids)
        sorted_data = self.get_sorting(docs)
        user_tz = self.env.user.tz or pytz.utc

        local = pytz.timezone(user_tz)
        min_date_str = ''
        if sorted_data:
            if sorted_data[0]['obj_type'] == 'app':
                min_date_str = sorted_data[0]['obj_id'].appointment_date
            if sorted_data[0]['obj_type'] == 'inp_up':
                min_date_str = sorted_data[0]['obj_id'].update_note_date
            if sorted_data[0]['obj_type'] == 'op':
                min_date_str = sorted_data[0]['obj_id'].time_in
        min_date = pytz.utc.localize(min_date_str).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if isinstance(min_date_str, datetime) else min_date_str.strftime("%d/%m/%Y %H:%M:%S")
        var_room_number = str(docs.room_number)
        today_now = datetime.now()
        min_update_note_date = min_date if min_date else today_now.strftime("%d/%m/%Y %H:%M:%S")
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        discharge_datetime = pytz.utc.localize(docs.inpatient_ids[0].discharge_datetime).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if len(docs.inpatient_ids) > 0 and is_discharged else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'var_room_number': var_room_number,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged,
            'discharge_datetime': discharge_datetime,
            'report_title': 'Update Medical Report'
        }


class MedicalReportTemplatePrimary(models.AbstractModel):
    _name = 'report.aly_basic_hms.medical_record_report_primary'
    _description = 'description'

    def get_sorting(self, record):
        my_list = []
        i = 0
        for app in record.update_note_ids:
            my_list.append(
                {
                    'date': app.appointment_date,
                    'obj_type': 'app',
                    'order_in_list': i,
                    'obj_id': app
                })
            i += 1
        i = 0
        # inpatient_update_note_ids
        for app in record.inpatient_ids:
            admission_date = datetime.combine(app.admission_date, datetime.min.time())
            # my_list.append(
            #     {
            #         'date': admission_date,
            #         'obj_type': 'inp',
            #         'order_in_list': i,
            #         'obj_id': app
            #     })
            # i += 1
            for inp in app.inpatient_update_note_ids:
                my_list.append(
                    {
                        'date': inp.update_note_date,
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
                    'date': app.time_in,
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
        docs = self.env[model].sudo().browse(docids)
        sorted_data = self.get_sorting(docs)
        user_tz = self.env.user.tz or pytz.utc

        local = pytz.timezone(user_tz)
        min_date_str = ''
        if sorted_data:
            if sorted_data[0]['obj_type'] == 'app':
                min_date_str = sorted_data[0]['obj_id'].appointment_date
            if sorted_data[0]['obj_type'] == 'inp_up':
                min_date_str = sorted_data[0]['obj_id'].update_note_date
            if sorted_data[0]['obj_type'] == 'op':
                min_date_str = sorted_data[0]['obj_id'].time_in
        min_date = pytz.utc.localize(min_date_str).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if isinstance(min_date_str, datetime) else min_date_str.strftime("%d/%m/%Y %H:%M:%S")
        var_room_number = str(docs.room_number)
        today_now = datetime.now()
        min_update_note_date = min_date if min_date else today_now.strftime("%d/%m/%Y %H:%M:%S")
        is_discharged = docs.inpatient_ids[0].is_discharged if len(docs.inpatient_ids) > 0 else False
        discharge_datetime = pytz.utc.localize(docs.inpatient_ids[0].discharge_datetime).astimezone(local).strftime("%d/%m/%Y %H:%M:%S") if len(docs.inpatient_ids) > 0 and is_discharged else False
        return {
            'data': data,
            'doc_ids': docids,
            'doc_model': model,
            'docs': docs,
            'sorted_data': sorted_data,
            'var_room_number': var_room_number,
            'min_update_note_date': min_update_note_date,
            'is_discharged': is_discharged,
            'discharge_datetime': discharge_datetime,
            'report_title': 'Primary Medical Report'
        }

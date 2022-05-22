# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{

    "name": "HCI Group",
    "version": "14.0.0.3",
    "currency": 'EGP',
    "summary": "Healthcare International Group",
    "description": """
    'Aly El Nemr' upgraded a module developed by BrowseInfo, was deployed on Odoo 14 third-party apps.
""",

    "depends": ["base", "sale_management", "stock", "account"],
    # "depends": ["base", "sale_management", "stock", "account_accountant"],
    "data": [
        'security/hospital_groups.xml',
        'security/product_categories_data.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml', 'views/assets.xml',
        'wizard/medical_patient_invoice_wizard.xml',
        'wizard/medical_patient_sale_order_wizard.xml',
        'wizard/medical_inpatient_discharge_wizard.xml',
        'views/medical_clinic.xml',
        'views/medical_medicament.xml',
        'views/medical_drug_route.xml',
        'views/medical_dose_unit.xml',
        'views/medical_inpatient_acc.xml',
        'views/medical_inpatient_accommodation.xml',
        'views/medical_inpatient_registration.xml',
        'views/medical_inp_update_note.xml',
        'views/medical_inpatient_medication.xml',
        'views/medical_inpatient_medication_transient.xml',
        'views/medical_appointment.xml',
        'views/medical_appointment_procedure.xml',
        'views/medical_inpatient_procedure.xml',
        'views/medical_appointment_investigation.xml',
        'views/medical_inpatient_investigation.xml',
        'views/medical_patient_line.xml',
        'views/medical_patient_attachment.xml',
        'views/medical_appointment_consultation_line.xml',
        'views/medical_inp_update_note_consultation_line.xml',
        'views/medical_operation.xml',
        'views/medical_operation_line.xml',
        'views/medical_insurance.xml',
        'views/bed_transfer.xml',
        'views/medical_patient_medication.xml',
        'views/medical_patient_medication1.xml',
        'views/medical_patient.xml',
        'views/medical_physician.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'views/res_user.xml',
        'report/report_view.xml',
        'report/medical_invoice_template.xml',
        'report/medical_record_report_primary.xml',
        'report/medical_record_report_update.xml',
        'report/medical_record_report_template.xml',
        'views/main_menu_file.xml',
    ],
    "author": "Aly El Nemr & BrowseInfo",
    "website": "",
    "installable": True,
    "application": True,
    "auto_install": False,
    "images": ["static/description/Banner.png"],
    "live_test_url": '',

}
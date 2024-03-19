import base64
import logging

from odoo.exceptions import ValidationError

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition
import ast

_logger = logging.getLogger(__name__)


class Binary(http.Controller):
    def isBase64_decodestring(s):
        try:
            return base64.decodestring(s)
        except Exception as e:
            raise ValidationError('Error: ' + str(e))

    @http.route('/web/binary/download_document', type='http', auth="public")
    def download_document(self, tab_id, **kw):
        new_tab = ast.literal_eval(tab_id)
        patient_id = request.env['medical.patient'].search([('id', 'in', new_tab)], limit=1)
        attachment_ids = request.env['medical.patient.attachment'].search([('patient_id', 'in', new_tab)])
        zip_filename = patient_id.name  # datetime.now()
        zip_filename = "%s.zip" % zip_filename
        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
        for file_info in attachment_ids:
            object_name = file_info.name
            object_handle = open(object_name, "wb")
            # writing binary data into file handle
            object_handle.write(base64.b64decode(file_info.att_document))
            object_handle.close()
            zip_file.write(object_name)
        zip_file.close()
        return request.make_response(bitIO.getvalue(),
                                     headers=[('Content-Type', 'application/x-zip-compressed'),
                                              ('Content-Disposition', content_disposition(zip_filename))])

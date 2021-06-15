from odoo import models


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_report_values(self, docids, data=None):
        if docids is None and data.get('docids', False):
            docids = data.get('docids')
        return super(ReportBomStructure, self)._get_report_values(docids, data)

from odoo import models


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    def action_print_bom(self):
        data = dict(quantity=self.product_qty, docids=[
                    self.bom_id.id], no_price=True, report_type='bom_structure')
        report = self.env.ref('mrp.action_report_bom_structure').with_context(
            discard_logo_check=True)
        report.name = 'Estructura de materiales - {}'.format(self.name)
        return report.report_action(self.bom_id, data)

from odoo import models


class ReportItParcMaintenanceHistory(models.AbstractModel):
    _name = 'report.it_parc.report_it_parc_maintenance_history_document'
    _description = 'Rapport historique maintenances'

    def _get_report_values(self, docids, data=None):
        docs = self.env['it.parc.intervention'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'it.parc.intervention',
            'docs': docs,
            'data': data or {},
        }

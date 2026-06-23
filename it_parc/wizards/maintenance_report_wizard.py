from datetime import datetime, time

from odoo import fields, models


class ItParcMaintenanceReportWizard(models.TransientModel):
    _name = 'it.parc.maintenance.report.wizard'
    _description = 'Rapport historique maintenances par période'

    date_from = fields.Date(string='Date début', required=True)
    date_to = fields.Date(string='Date fin', required=True)
    equipment_id = fields.Many2one('it.parc.equipment', string='Équipement')

    def action_print_report(self):
        self.ensure_one()
        dt_from = datetime.combine(self.date_from, time.min)
        dt_to = datetime.combine(self.date_to, time.max)
        domain = [('status', '=', 'done')]
        if self.equipment_id:
            domain.append(('equipment_id', '=', self.equipment_id.id))
        interventions = self.env['it.parc.intervention'].search(domain, order='date_start')
        filtered = interventions.filtered(lambda i: (
            (ref := (i.date_end or i.date_done or i.scheduled_date))
            and dt_from <= fields.Datetime.to_datetime(ref) <= dt_to
        ))
        return self.env.ref('it_parc.action_report_it_parc_maintenance_history').report_action(
            filtered,
            data={
                'date_from': str(self.date_from),
                'date_to': str(self.date_to),
            },
        )

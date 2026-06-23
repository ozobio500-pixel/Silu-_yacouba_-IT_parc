from odoo import fields, models, _


class ItParcAlertScanWizard(models.TransientModel):
    _name = 'it.parc.alert.scan.wizard'
    _description = 'Wizard de scan manuel des alertes'

    alert_days_before = fields.Integer(
        string='Délai d\'alerte (jours)',
        default=lambda self: int(self.env['ir.config_parameter'].sudo().get_param(
            'it_parc.alert_days_before', '30',
        )),
    )
    result_message = fields.Text(string='Résultat', readonly=True)

    def action_scan(self):
        self.ensure_one()
        self.env['ir.config_parameter'].sudo().set_param(
            'it_parc.alert_days_before', str(self.alert_days_before),
        )
        created = self.env['it.alerte']._scan_alerts()
        active_count = self.env['it.alerte'].search_count([('state', '=', 'active')])
        self.result_message = _(
            'Scan terminé : %s nouvelle(s) alerte(s) créée(s). '
            'Total alertes actives : %s.'
        ) % (created, active_count)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.parc.alert.scan.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

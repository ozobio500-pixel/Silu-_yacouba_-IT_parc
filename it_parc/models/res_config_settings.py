from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    it_parc_alert_days_before = fields.Integer(
        string='Délai d\'alerte (jours)',
        config_parameter='it_parc.alert_days_before',
        default=30,
        help='Nombre de jours avant expiration pour générer une alerte garantie ou contrat.',
    )

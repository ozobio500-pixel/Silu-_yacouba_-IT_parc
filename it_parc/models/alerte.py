from odoo import api, fields, models, _


class ItAlerte(models.Model):
    _name = 'it.alerte'
    _description = 'Alerte IT Parc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc'

    name = fields.Char(string='Référence', required=True)
    alert_type = fields.Selection([
        ('warranty', 'Garantie'),
        ('contract', 'Contrat'),
    ], string='Type', required=True)
    equipment_id = fields.Many2one('it.parc.equipment', string='Équipement', ondelete='cascade')
    contract_id = fields.Many2one('it.parc.contract', string='Contrat', ondelete='cascade')
    expiry_date = fields.Date(string='Date d\'échéance', required=True)
    days_remaining = fields.Integer(string='Jours restants', compute='_compute_days_remaining', store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('dismissed', 'Traitée'),
    ], string='Statut', default='active', tracking=True)
    message = fields.Text(string='Message')

    @api.depends('expiry_date')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                record.days_remaining = (record.expiry_date - today).days
            else:
                record.days_remaining = 0

    def action_dismiss(self):
        self.write({'state': 'dismissed'})

    @api.model
    def _get_alert_days_before(self):
        param = self.env['ir.config_parameter'].sudo().get_param('it_parc.alert_days_before', '30')
        try:
            return int(param)
        except (TypeError, ValueError):
            return 30

    @api.model
    def _scan_alerts(self):
        """Scan warranties and contracts and create/update alert records."""
        days_before = self._get_alert_days_before()
        today = fields.Date.today()
        threshold = fields.Date.add(today, days=days_before)
        created = 0

        equipments = self.env['it.parc.equipment'].search([
            ('warranty_end_date', '!=', False),
            ('warranty_end_date', '<=', threshold),
        ])
        for equipment in equipments:
            existing = self.search([
                ('alert_type', '=', 'warranty'),
                ('equipment_id', '=', equipment.id),
                ('state', '=', 'active'),
            ], limit=1)
            if not existing:
                self.sudo().create({
                    'name': _('Alerte garantie - %s') % equipment.name,
                    'alert_type': 'warranty',
                    'equipment_id': equipment.id,
                    'expiry_date': equipment.warranty_end_date,
                    'message': _('La garantie de %s expire le %s.') % (
                        equipment.name, equipment.warranty_end_date,
                    ),
                })
                created += 1
                equipment.message_post(body=_('Alerte : garantie expirant bientôt.'))

        contracts = self.env['it.parc.contract'].search([
            ('end_date', '!=', False),
            ('end_date', '<=', threshold),
            ('state', '=', 'active'),
        ])
        for contract in contracts:
            existing = self.search([
                ('alert_type', '=', 'contract'),
                ('contract_id', '=', contract.id),
                ('state', '=', 'active'),
            ], limit=1)
            if not existing:
                self.sudo().create({
                    'name': _('Alerte contrat - %s') % contract.name,
                    'alert_type': 'contract',
                    'contract_id': contract.id,
                    'expiry_date': contract.end_date,
                    'message': _('Le contrat %s expire le %s.') % (
                        contract.name, contract.end_date,
                    ),
                })
                created += 1
                contract.message_post(body=_('Alerte : contrat expirant bientôt.'))
        return created

from odoo import api, fields, models, _


class ItParcDashboard(models.TransientModel):
    _name = 'it.parc.dashboard'
    _description = 'Dashboard IT Parc'

    total_equipment = fields.Integer(string='Équipements totaux', compute='_compute_stats')
    assigned_equipment = fields.Integer(string='Affectés', compute='_compute_stats')
    maintenance_equipment = fields.Integer(string='En maintenance', compute='_compute_stats')
    retired_equipment = fields.Integer(string='Retirés', compute='_compute_stats')
    expiring_contracts = fields.Integer(string='Contrats expirants', compute='_compute_stats')
    service_requests = fields.Integer(string='Interventions planifiées', compute='_compute_stats')
    active_alerts = fields.Integer(string='Alertes actives', compute='_compute_stats')

    @api.depends()
    def _compute_stats(self):
        equipment = self.env['it.parc.equipment']
        contract = self.env['it.parc.contract']
        intervention = self.env['it.parc.intervention']
        alerte = self.env['it.alerte']
        today = fields.Date.today()
        limit = fields.Date.add(today, days=60)
        for record in self:
            record.total_equipment = equipment.search_count([])
            record.assigned_equipment = equipment.search_count([('state', '=', 'assigned')])
            record.maintenance_equipment = equipment.search_count([('state', '=', 'maintenance')])
            record.retired_equipment = equipment.search_count([('state', '=', 'retired')])
            record.expiring_contracts = contract.search_count([
                ('end_date', '<=', limit), ('state', 'in', ['active', 'renewed']),
            ])
            record.service_requests = intervention.search_count([('status', '=', 'planned')])
            record.active_alerts = alerte.search_count([('state', '=', 'active')])

    @api.model
    def get_dashboard_data(self):
        equipment = self.env['it.parc.equipment']
        contract = self.env['it.parc.contract']
        intervention = self.env['it.parc.intervention']
        alerte = self.env['it.alerte']
        today = fields.Date.today()
        limit = fields.Date.add(today, days=60)
        by_category = {}
        for cat_key, cat_label in equipment._fields['category'].selection:
            by_category[cat_label] = equipment.search_count([('category', '=', cat_key)])
        return {
            'total_equipment': equipment.search_count([]),
            'assigned_equipment': equipment.search_count([('state', '=', 'assigned')]),
            'maintenance_equipment': equipment.search_count([('state', '=', 'maintenance')]),
            'retired_equipment': equipment.search_count([('state', '=', 'retired')]),
            'expiring_contracts': contract.search_count([
                ('end_date', '<=', limit), ('state', 'in', ['active', 'renewed']),
            ]),
            'service_requests': intervention.search_count([('status', '=', 'planned')]),
            'active_alerts': alerte.search_count([('state', '=', 'active')]),
            'by_category': by_category,
        }

from odoo import fields, models


class ItParcAssignmentHistory(models.Model):
    _name = 'it.parc.assignment.history'
    _description = 'Historique des affectations'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    equipment_id = fields.Many2one(
        'it.parc.equipment', string='Équipement', required=True, ondelete='cascade',
    )
    employee_id = fields.Many2one('hr.employee', string='Employé', required=True)
    department_id = fields.Many2one('hr.department', string='Département')
    date_from = fields.Datetime(string='Date de début', required=True, default=fields.Datetime.now)
    date_to = fields.Datetime(string='Date de fin')
    note = fields.Text(string='Note / Motif')
    active = fields.Boolean(string='Actif', default=True)

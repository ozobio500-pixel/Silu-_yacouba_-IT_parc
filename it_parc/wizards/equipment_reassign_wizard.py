from odoo import api, fields, models, _


class ItParcEquipmentReassignWizard(models.TransientModel):
    _name = 'it.parc.equipment.reassign.wizard'
    _description = 'Wizard de réaffectation d\'équipement'

    equipment_id = fields.Many2one('it.parc.equipment', string='Équipement', required=True)
    new_employee_id = fields.Many2one('hr.employee', string='Nouvel employé', required=True)
    new_department_id = fields.Many2one('hr.department', string='Nouveau département', required=True)
    reason = fields.Text(string='Motif de réaffectation')
    date = fields.Datetime(string='Date de réaffectation', default=fields.Datetime.now)

    @api.onchange('new_employee_id')
    def _onchange_new_employee_id(self):
        if self.new_employee_id and self.new_employee_id.department_id:
            self.new_department_id = self.new_employee_id.department_id

    def action_reassign(self):
        self.ensure_one()
        equipment = self.equipment_id
        active_history = equipment.assignment_history_ids.filtered(
            lambda h: h.active and not h.date_to,
        )
        active_history.write({'date_to': self.date, 'active': False})
        equipment.write({
            'employee_id': self.new_employee_id.id,
            'department_id': self.new_department_id.id,
            'state': 'assigned',
        })
        self.env['it.parc.assignment.history'].create({
            'equipment_id': equipment.id,
            'employee_id': self.new_employee_id.id,
            'department_id': self.new_department_id.id,
            'date_from': self.date,
            'note': self.reason,
        })
        equipment.message_post(body=_(
            'Équipement réaffecté à %s (%s). Motif : %s'
        ) % (
            self.new_employee_id.name,
            self.new_department_id.name,
            self.reason or _('Non précisé'),
        ))
        return {'type': 'ir.actions.act_window_close'}

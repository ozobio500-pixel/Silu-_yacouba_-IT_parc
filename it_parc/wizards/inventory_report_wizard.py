from odoo import fields, models


class ItParcInventoryReportWizard(models.TransientModel):
    _name = 'it.parc.inventory.report.wizard'
    _description = 'Rapport inventaire filtrable'

    department_id = fields.Many2one('hr.department', string='Département')
    category = fields.Selection([
        ('ordinateur', 'Ordinateur'),
        ('serveur', 'Serveur'),
        ('réseau', 'Réseau'),
        ('périphérique', 'Périphérique'),
        ('autre', 'Autre'),
    ], string='Catégorie')

    def action_print_report(self):
        self.ensure_one()
        domain = []
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.category:
            domain.append(('category', '=', self.category))
        equipments = self.env['it.parc.equipment'].search(domain, order='name')
        return self.env.ref('it_parc.action_report_it_parc_inventory').report_action(equipments)

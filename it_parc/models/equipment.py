from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ItParcEquipment(models.Model):
    _name = 'it.parc.equipment'
    _description = 'Équipement IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    serial_no = fields.Char(string='Numéro de série', required=True, tracking=True)
    model = fields.Char(string='Modèle')
    category = fields.Selection([
        ('ordinateur', 'Ordinateur'),
        ('serveur', 'Serveur'),
        ('réseau', 'Réseau'),
        ('périphérique', 'Périphérique'),
        ('autre', 'Autre'),
    ], string='Catégorie', default='ordinateur')
    site = fields.Char(string='Site / Localisation')
    employee_id = fields.Many2one('hr.employee', string='Employé', tracking=True)
    department_id = fields.Many2one('hr.department', string='Département', tracking=True)
    assigned_to = fields.Many2one(
        'res.users', string='Assigné à', related='employee_id.user_id', store=True, readonly=False,
    )
    assignment_history_ids = fields.One2many(
        'it.parc.assignment.history', 'equipment_id', string='Historique des affectations',
    )
    intervention_ids = fields.One2many('it.parc.intervention', 'equipment_id', string='Interventions')
    contract_id = fields.Many2one('it.parc.contract', string='Contrat fournisseur')
    purchase_date = fields.Date(string='Date d\'achat')
    purchase_value = fields.Monetary(string='Valeur d\'achat', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Devise', default=lambda self: self.env.company.currency_id,
    )
    warranty_end_date = fields.Date(string='Fin de garantie')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('assigned', 'Affecté'),
        ('maintenance', 'En maintenance'),
        ('retired', 'Retiré'),
    ], string='Statut', default='draft', tracking=True)
    warranty_alert = fields.Boolean(string='Alerte garantie', compute='_compute_warranty_alert', store=True)
    contract_alert = fields.Boolean(string='Alerte contrat', compute='_compute_contract_alert', store=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id

    @api.depends('warranty_end_date')
    def _compute_warranty_alert(self):
        today = fields.Date.today()
        days_before = int(self.env['ir.config_parameter'].sudo().get_param('it_parc.alert_days_before', '30'))
        threshold = fields.Date.add(today, days=days_before)
        for record in self:
            record.warranty_alert = bool(
                record.warranty_end_date and record.warranty_end_date <= threshold
            )

    @api.depends('contract_id', 'contract_id.end_date')
    def _compute_contract_alert(self):
        today = fields.Date.today()
        days_before = int(self.env['ir.config_parameter'].sudo().get_param('it_parc.alert_days_before', '30'))
        threshold = fields.Date.add(today, days=days_before)
        for record in self:
            record.contract_alert = bool(
                record.contract_id and record.contract_id.end_date
                and record.contract_id.end_date <= threshold
            )

    @api.model
    def _cron_check_warranty(self):
        self.env['it.alerte']._scan_alerts()
        return True

    def action_assign(self):
        for record in self:
            if not record.employee_id:
                raise UserError(_('Veuillez sélectionner un employé avant d\'affecter cet équipement.'))
            record.state = 'assigned'
            record.assignment_history_ids = [(0, 0, {
                'employee_id': record.employee_id.id,
                'department_id': record.department_id.id,
                'date_from': fields.Datetime.now(),
            })]
            record.message_post(body=_('Équipement affecté à %s (%s)') % (
                record.employee_id.name, record.department_id.name or _('N/A'),
            ))

    def action_maintenance(self):
        self.write({'state': 'maintenance'})
        self.message_post(body=_('Équipement basculé en maintenance.'))

    def action_retire(self):
        self.write({'state': 'retired'})
        self.message_post(body=_('Équipement retiré du parc.'))

    def open_reassign_wizard(self):
        self.ensure_one()
        return {
            'name': _('Réaffecter équipement'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.parc.equipment.reassign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_equipment_id': self.id},
        }

    def _xlsx_attachment(self, data, filename):
        import base64
        return self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(data).decode('ascii'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

    def _xlsx_download_action(self, attachment):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    @api.model
    def export_inventory_xlsx(self):
        """Export inventaire complet avec toutes les colonnes."""
        import xlsxwriter
        from io import BytesIO
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Inventaire')
        header = [
            'Nom', 'N° série', 'Modèle', 'Catégorie', 'Site', 'Employé', 'Département',
            'Contrat', 'Date achat', 'Valeur achat', 'Fin garantie', 'Statut',
        ]
        cell_fmt = workbook.add_format({'border': 1})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1})
        for col, title in enumerate(header):
            worksheet.write(0, col, title, header_fmt)
        equipments = self.search([])
        for row, equip in enumerate(equipments, start=1):
            worksheet.write(row, 0, equip.name or '', cell_fmt)
            worksheet.write(row, 1, equip.serial_no or '', cell_fmt)
            worksheet.write(row, 2, equip.model or '', cell_fmt)
            worksheet.write(row, 3, dict(equip._fields['category'].selection).get(equip.category, ''), cell_fmt)
            worksheet.write(row, 4, equip.site or '', cell_fmt)
            worksheet.write(row, 5, equip.employee_id.name or '', cell_fmt)
            worksheet.write(row, 6, equip.department_id.name or '', cell_fmt)
            worksheet.write(row, 7, equip.contract_id.name or '', cell_fmt)
            worksheet.write(row, 8, str(equip.purchase_date or ''), cell_fmt)
            worksheet.write(row, 9, float(equip.purchase_value or 0.0), cell_fmt)
            worksheet.write(row, 10, str(equip.warranty_end_date or ''), cell_fmt)
            worksheet.write(row, 11, dict(equip._fields['state'].selection).get(equip.state, ''), cell_fmt)
        workbook.close()
        output.seek(0)
        attachment = self._xlsx_attachment(output.getvalue(), 'inventaire_complet_it_parc.xlsx')
        return self._xlsx_download_action(attachment)

    def export_equipment_xlsx(self):
        return self.env['it.parc.equipment'].export_inventory_xlsx()

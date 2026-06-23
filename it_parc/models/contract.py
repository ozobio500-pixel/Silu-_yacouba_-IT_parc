from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ItParcContract(models.Model):
    _name = 'it.parc.contract'
    _description = 'Contrat fournisseur IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom du contrat', required=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', domain=[('supplier_rank', '>', 0)])
    start_date = fields.Date(string='Début', required=True)
    end_date = fields.Date(string='Fin', required=True)
    renewal_date = fields.Date(string='Date de renouvellement')
    days_remaining = fields.Integer(
        string='Jours restants', compute='_compute_days_remaining', store=True,
    )
    amount = fields.Monetary(string='Montant', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Devise', required=True,
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection([
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('renewed', 'Renouvelé'),
    ], string='Statut', default='active', tracking=True)
    equipment_ids = fields.One2many('it.parc.equipment', 'contract_id', string='Équipements liés')
    notes = fields.Text(string='Notes')
    expiring = fields.Boolean(string='Expirant', compute='_compute_expiring', store=True)

    @api.depends('end_date')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.end_date:
                record.days_remaining = (record.end_date - today).days
            else:
                record.days_remaining = 0

    @api.depends('end_date')
    def _compute_expiring(self):
        today = fields.Date.today()
        for record in self:
            record.expiring = bool(record.end_date and record.end_date <= today)

    @api.model
    def _cron_check_contracts(self):
        self.env['it.alerte']._scan_alerts()
        today = fields.Date.today()
        contracts = self.search([('end_date', '<', today), ('state', '=', 'active')])
        contracts.write({'state': 'expired'})
        return True

    def action_renew(self):
        for contract in self:
            if not contract.renewal_date:
                raise UserError(_('Veuillez définir une date de renouvellement.'))
            contract.state = 'renewed'
            contract.message_post(body=_('Contrat renouvelé jusqu\'au %s') % contract.end_date)

    def action_open_renew_wizard(self):
        self.ensure_one()
        return {
            'name': _('Renouveler contrat'),
            'type': 'ir.actions.act_window',
            'res_model': 'it.parc.contract.renewal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id},
        }

    def _xlsx_attachment(self, data, filename):
        import base64
        return self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(data).decode('ascii'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

    @api.model
    def export_expiring_contracts_xlsx(self):
        """Liste des contrats expirant dans les 60 jours avec mise en couleur conditionnelle."""
        import xlsxwriter
        from io import BytesIO

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Contrats expirants')
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white'})
        red_fmt = workbook.add_format({'bg_color': '#FFC7CE'})
        orange_fmt = workbook.add_format({'bg_color': '#FFEB9C'})
        green_fmt = workbook.add_format({'bg_color': '#C6EFCE'})

        header = ['Contrat', 'Fournisseur', 'Début', 'Fin', 'Jours restants', 'Montant', 'Statut']
        for col, title in enumerate(header):
            worksheet.write(0, col, title, header_fmt)

        today = fields.Date.today()
        limit = fields.Date.add(today, days=60)
        contracts = self.search([
            ('end_date', '<=', limit),
            ('state', 'in', ['active', 'renewed']),
        ], order='end_date asc')

        for row, contract in enumerate(contracts, start=1):
            days = contract.days_remaining
            if days <= 15:
                fmt = red_fmt
            elif days <= 30:
                fmt = orange_fmt
            else:
                fmt = green_fmt
            worksheet.write(row, 0, contract.name or '', fmt)
            worksheet.write(row, 1, contract.supplier_id.name or '', fmt)
            worksheet.write(row, 2, str(contract.start_date or ''), fmt)
            worksheet.write(row, 3, str(contract.end_date or ''), fmt)
            worksheet.write(row, 4, days, fmt)
            worksheet.write(row, 5, float(contract.amount or 0.0), fmt)
            worksheet.write(row, 6, dict(contract._fields['state'].selection).get(contract.state, ''), fmt)

        workbook.close()
        output.seek(0)
        attachment = self._xlsx_attachment(output.getvalue(), 'contrats_expirants_60j_it_parc.xlsx')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def export_contracts_xlsx(self):
        return self.env['it.parc.contract'].export_expiring_contracts_xlsx()

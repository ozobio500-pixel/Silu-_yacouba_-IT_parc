from odoo import api, fields, models, _


class ItParcIntervention(models.Model):
    _name = 'it.parc.intervention'
    _description = 'Intervention IT'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Référence', required=True, default='New')
    equipment_id = fields.Many2one('it.parc.equipment', string='Équipement', required=True)
    intervention_type = fields.Selection([
        ('corrective', 'Corrective'),
        ('preventive', 'Préventive'),
    ], string='Type', default='corrective', required=True)
    scheduled_date = fields.Datetime(string='Date planifiée', required=True, default=fields.Datetime.now)
    date_start = fields.Datetime(string='Date de début')
    date_end = fields.Datetime(string='Date de fin')
    date_done = fields.Datetime(string='Date réalisée')
    duration_hours = fields.Float(
        string='Durée (heures)', compute='_compute_duration_hours', store=True,
    )
    cost = fields.Monetary(string='Coût', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Devise', default=lambda self: self.env.company.currency_id,
    )
    technician_id = fields.Many2one('res.users', string='Technicien')
    status = fields.Selection([
        ('draft', 'Brouillon'),
        ('planned', 'Planifiée'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée'),
    ], string='Statut', default='draft', tracking=True)
    description = fields.Text(string='Description de l\'intervention')
    report = fields.Html(string='Rapport d\'intervention')

    @api.depends('date_start', 'date_end', 'date_done')
    def _compute_duration_hours(self):
        for record in self:
            end = record.date_end or record.date_done
            if record.date_start and end:
                delta = end - record.date_start
                record.duration_hours = round(delta.total_seconds() / 3600.0, 2)
            else:
                record.duration_hours = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('it.parc.intervention') or 'INT/0001'
        return super().create(vals)

    def action_mark_done(self):
        now = fields.Datetime.now()
        for record in self:
            vals = {'status': 'done', 'date_done': now, 'date_end': now}
            if not record.date_start:
                vals['date_start'] = record.scheduled_date or now
            record.write(vals)

    def action_plan(self):
        self.write({'status': 'planned'})

    def action_start(self):
        self.write({'status': 'planned', 'date_start': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'status': 'cancelled'})

    def _xlsx_attachment(self, data, filename):
        import base64
        return self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(data).decode('ascii'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

    @api.model
    def export_maintenance_costs_xlsx(self):
        """Synthèse des coûts de maintenance par équipement et par mois."""
        import xlsxwriter
        from io import BytesIO
        from collections import defaultdict

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Coûts maintenance')
        cell_fmt = workbook.add_format({'border': 1})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        header = ['Équipement', 'N° série', 'Mois', 'Nb interventions', 'Coût total', 'Durée totale (h)']
        for col, title in enumerate(header):
            worksheet.write(0, col, title, header_fmt)

        interventions = self.search([('status', '=', 'done')])
        summary = defaultdict(lambda: {'count': 0, 'cost': 0.0, 'duration': 0.0})
        for inter in interventions:
            month_key = (inter.date_end or inter.date_done or inter.scheduled_date).strftime('%Y-%m')
            key = (inter.equipment_id.id, month_key)
            summary[key]['equipment'] = inter.equipment_id
            summary[key]['month'] = month_key
            summary[key]['count'] += 1
            summary[key]['cost'] += inter.cost or 0.0
            summary[key]['duration'] += inter.duration_hours or 0.0

        row = 1
        for key in sorted(summary.keys(), key=lambda k: (summary[k]['equipment'].name, summary[k]['month'])):
            data = summary[key]
            equip = data['equipment']
            worksheet.write(row, 0, equip.name or '', cell_fmt)
            worksheet.write(row, 1, equip.serial_no or '', cell_fmt)
            worksheet.write(row, 2, data['month'], cell_fmt)
            worksheet.write(row, 3, data['count'], cell_fmt)
            worksheet.write(row, 4, data['cost'], money_fmt)
            worksheet.write(row, 5, data['duration'], cell_fmt)
            row += 1

        workbook.close()
        output.seek(0)
        attachment = self._xlsx_attachment(output.getvalue(), 'couts_maintenance_it_parc.xlsx')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def export_interventions_xlsx(self):
        import base64
        import xlsxwriter
        from io import BytesIO
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Interventions')
        header = [
            'Référence', 'Équipement', 'Type', 'Date planifiée', 'Début', 'Fin',
            'Durée (h)', 'Coût', 'Technicien', 'Statut',
        ]
        for col, title in enumerate(header):
            worksheet.write(0, col, title)
        for row, intervention in enumerate(self.search([]), start=1):
            worksheet.write(row, 0, intervention.name)
            worksheet.write(row, 1, intervention.equipment_id.name or '')
            worksheet.write(row, 2, dict(intervention._fields['intervention_type'].selection).get(
                intervention.intervention_type,
            ))
            worksheet.write(row, 3, str(intervention.scheduled_date or ''))
            worksheet.write(row, 4, str(intervention.date_start or ''))
            worksheet.write(row, 5, str(intervention.date_end or ''))
            worksheet.write(row, 6, intervention.duration_hours)
            worksheet.write(row, 7, float(intervention.cost or 0.0))
            worksheet.write(row, 8, intervention.technician_id.name or '')
            worksheet.write(row, 9, dict(intervention._fields['status'].selection).get(intervention.status))
        workbook.close()
        output.seek(0)
        attachment = self._xlsx_attachment(output.getvalue(), 'interventions_it_parc.xlsx')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

import base64
import csv
from io import StringIO

from odoo import fields, models, _
from odoo.exceptions import UserError


class ItParcImportEquipmentWizard(models.TransientModel):
    _name = 'it.parc.import.equipment.wizard'
    _description = 'Import en masse d\'équipements'

    file_data = fields.Binary(string='Fichier CSV', required=True)
    filename = fields.Char(string='Nom du fichier')
    report = fields.Text(string='Rapport d\'import', readonly=True)
    created_count = fields.Integer(string='Créés', readonly=True)
    duplicate_count = fields.Integer(string='Doublons', readonly=True)
    error_count = fields.Integer(string='Erreurs', readonly=True)

    def action_import(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_('Veuillez télécharger un fichier CSV.'))
        try:
            csv_content = base64.b64decode(self.file_data).decode('utf-8-sig')
        except UnicodeDecodeError:
            csv_content = base64.b64decode(self.file_data).decode('latin-1')

        reader = csv.DictReader(StringIO('\n'.join(csv_content.splitlines())))
        created = 0
        duplicates = 0
        errors = []
        lines_created = []
        lines_ignored = []
        Equipment = self.env['it.parc.equipment']

        for line_num, row in enumerate(reader, start=2):
            serial_no = (row.get('serial_no') or row.get('Numéro de série') or '').strip()
            if not serial_no:
                errors.append(_('Ligne %s : numéro de série manquant.') % line_num)
                continue
            existing = Equipment.search([('serial_no', '=', serial_no)], limit=1)
            if existing:
                duplicates += 1
                lines_ignored.append(_('Ligne %s : doublon (%s).') % (line_num, serial_no))
                continue
            try:
                category = row.get('category') or row.get('Catégorie') or 'autre'
                valid_categories = dict(Equipment._fields['category'].selection)
                if category not in valid_categories:
                    category = 'autre'
                values = {
                    'name': row.get('name') or row.get('Nom') or _('Équipement %s') % serial_no,
                    'serial_no': serial_no,
                    'model': row.get('model') or row.get('Modèle'),
                    'category': category,
                    'site': row.get('site') or row.get('Site'),
                    'purchase_date': row.get('purchase_date') or row.get('Date d\'achat') or False,
                    'warranty_end_date': row.get('warranty_end_date') or row.get('Fin de garantie') or False,
                }
                purchase_value = row.get('purchase_value') or row.get('Valeur d\'achat')
                if purchase_value:
                    values['purchase_value'] = float(str(purchase_value).replace(',', '.').replace(' ', ''))
                Equipment.create(values)
                created += 1
                lines_created.append(_('Ligne %s : %s créé.') % (line_num, serial_no))
            except Exception as e:
                errors.append(_('Ligne %s : erreur - %s') % (line_num, str(e)))

        report_lines = [
            _('=== RAPPORT D\'IMPORT ==='),
            _('Lignes créées : %s') % created,
            _('Doublons ignorés : %s') % duplicates,
            _('Erreurs : %s') % len(errors),
            '',
            _('--- Créées ---'),
        ] + lines_created + ['', _('--- Doublons ignorés ---')] + lines_ignored + [
            '', _('--- Erreurs ---'),
        ] + errors

        self.write({
            'created_count': created,
            'duplicate_count': duplicates,
            'error_count': len(errors),
            'report': '\n'.join(report_lines),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'it.parc.import.equipment.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

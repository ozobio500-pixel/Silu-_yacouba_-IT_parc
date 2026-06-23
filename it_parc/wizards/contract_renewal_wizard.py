from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ItParcContractRenewalWizard(models.TransientModel):
    _name = 'it.parc.contract.renewal.wizard'
    _description = 'Wizard de renouvellement de contrat'

    contract_id = fields.Many2one('it.parc.contract', string='Contrat', required=True)
    new_end_date = fields.Date(string='Nouvelle date de fin', required=True)
    new_amount = fields.Monetary(string='Nouveau montant', currency_field='currency_id')
    currency_id = fields.Many2one(related='contract_id.currency_id')

    def action_renew_contract(self):
        self.ensure_one()
        contract = self.contract_id
        if self.new_end_date <= contract.end_date:
            raise UserError(_('La nouvelle date de fin doit être postérieure à la date actuelle du contrat.'))
        contract.write({
            'end_date': self.new_end_date,
            'amount': self.new_amount or contract.amount,
            'state': 'renewed',
        })
        contract.message_post(body=_('Contrat renouvelé jusqu’au %s.') % self.new_end_date)
        return {'type': 'ir.actions.act_window_close'}

from odoo import fields, models


class LedgerImportWizard(models.TransientModel):
    _name = 'ps.ledger.import.wizard'
    _description = 'Veresiye İçe Aktar'

    data_file = fields.Binary(string='Dosya')
    filename = fields.Char(string='Dosya Adı')

    def action_import(self):
        # Placeholder for import logic
        return {'type': 'ir.actions.act_window_close'}

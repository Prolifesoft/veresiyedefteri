from odoo import fields, models


class MassCollectionWizard(models.TransientModel):
    _name = 'ps.ledger.mass.collection.wizard'
    _description = 'Toplu Tahsilat Sihirbazı'

    partner_ids = fields.Many2many('res.partner', string='Müşteriler')
    amount = fields.Monetary(string='Tahsilat Tutarı')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    payment_method = fields.Selection(
        [
            ('cash', 'Nakit'),
            ('card', 'Kart'),
            ('transfer', 'Havale/EFT'),
            ('pos', 'POS'),
            ('other', 'Diğer'),
        ],
        string='Ödeme Tipi',
        default='cash',
    )

    def action_confirm(self):
        # Placeholder for mass collection logic
        return {'type': 'ir.actions.act_window_close'}

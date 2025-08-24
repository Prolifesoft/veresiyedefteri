from odoo import fields, models


class LedgerPaymentWizard(models.TransientModel):
    _name = 'ps.ledger.payment.wizard'
    _description = 'Veresiye Ödeme Sihirbazı'

    partner_id = fields.Many2one(
        'res.partner', string='Müşteri', required=True
    )
    amount = fields.Monetary(string='Tutar', required=True)
    payment_method = fields.Selection(
        [
            ('cash', 'Nakit'),
            ('card', 'Kart'),
            ('transfer', 'Havale/EFT'),
            ('pos', 'POS'),
            ('other', 'Diğer'),
        ],
        string='Ödeme Tipi',
        required=True,
        default='cash',
    )
    date = fields.Date(string='Tarih', default=fields.Date.context_today)
    note = fields.Char(string='Not')
    currency_id = fields.Many2one(
        'res.currency', related='partner_id.currency_id', readonly=True
    )

    def action_confirm(self):
        self.ensure_one()
        description = self.note or (
            'Kısmi Ödeme'
            if self.amount < self.partner_id.x_ledger_balance
            else 'Ödeme'
        )
        self.env['ps.ledger.entry'].create(
            {
                'partner_id': self.partner_id.id,
                'date': self.date,
                'type': 'payment',
                'quantity': 1.0,
                'price_unit': self.amount,
                'description': description,
                'payment_method': self.payment_method,
            }
        )
        return {'type': 'ir.actions.act_window_close'}

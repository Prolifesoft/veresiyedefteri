from odoo import fields, models


class VeresiyePaymentWizard(models.TransientModel):
    _name = 'veresiye.payment.wizard'
    _description = 'Ödeme Yap'

    ledger_id = fields.Many2one(
        'veresiye.defteri', string='Defter', required=True
    )
    amount = fields.Monetary(string='Ödeme Tutarı', required=True)
    payment_date = fields.Date(
        string='Ödeme Tarihi',
        default=fields.Date.context_today,
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='ledger_id.currency_id', readonly=True
    )
    remaining_amount = fields.Monetary(
        related='ledger_id.remaining_amount',
        readonly=True,
        string='Toplam Borç',
        currency_field='currency_id',
    )

    def action_confirm(self):
        self.ensure_one()
        ledger = self.ledger_id
        ledger.last_payment_date = self.payment_date
        line_name = 'Ödeme'
        if self.amount < ledger.remaining_amount:
            line_name = 'Kısmi Ödeme'
        self.env['veresiye.defteri.line'].create({
            'ledger_id': ledger.id,
            'name': line_name,
            'quantity': 0,
            'price_unit': 0,
            'paid_amount': self.amount,
            'date': self.payment_date,
        })
        return {'type': 'ir.actions.act_window_close'}

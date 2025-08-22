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

    def action_confirm(self):
        self.ensure_one()
        ledger = self.ledger_id
        ledger.paid_amount += self.amount
        ledger.last_payment_date = self.payment_date
        return {'type': 'ir.actions.act_window_close'}

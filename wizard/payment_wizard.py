from odoo import models, fields


class VeresiyePaymentWizard(models.TransientModel):
    """Ödeme Sihirbazı"""
    _name = 'veresiye.payment.wizard'
    _description = 'Veresiye Ödeme Sihirbazı'

    ledger_id = fields.Many2one(
        'veresiye.ledger',
        string='Fiş',
        required=True,
        help='Ödeme yapılacak fiş'
    )

    amount = fields.Monetary(
        string='Ödeme Tutarı',
        required=True,
        help='Ödenecek tutar'
    )

    date = fields.Date(
        string='Ödeme Tarihi',
        required=True,
        default=fields.Date.today,
        help='Ödeme tarihi'
    )

    note = fields.Char(
        string='Not',
        help='Ödeme notu'
    )

    currency_id = fields.Many2one(
        related='ledger_id.currency_id',
        string='Para Birimi'
    )

    def action_confirm_payment(self):
        """Ödeme kaydını oluştur"""
        self.env['veresiye.payment'].create({
            'ledger_id': self.ledger_id.id,
            'date': self.date,
            'amount': self.amount,
            'note': self.note or '',
        })
        return {'type': 'ir.actions.act_window_close'}

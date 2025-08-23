from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True
    )
    x_ledger_total_debt = fields.Monetary(
        string='Borç', currency_field='currency_id', store=True, default=0.0
    )
    x_ledger_total_paid = fields.Monetary(
        string='Ödenen', currency_field='currency_id', store=True, default=0.0
    )
    x_ledger_balance = fields.Monetary(
        string='Kalan', currency_field='currency_id', store=True, default=0.0
    )
    x_last_payment_date = fields.Date(
        string='Ödeme Tarihi',
        compute='_compute_last_payment_date',
        store=True,
    )
    x_phone_display = fields.Char(
        string='Telefon', compute='_compute_phone_display', store=True
    )
    ledger_entry_ids = fields.One2many(
        'ps.ledger.entry',
        'partner_id',
        string='Veresiye Satırları',
    )

    @api.depends('phone', 'mobile')
    def _compute_phone_display(self):
        for partner in self:
            partner.x_phone_display = partner.phone or partner.mobile or ''

    def recompute_ledger_totals(self):
        data = self.env['ps.ledger.entry'].read_group(
            [('partner_id', 'in', self.ids)],
            ['total:sum'],
            ['partner_id', 'type'],
            lazy=False,
        )
        mapping = {pid: {'debt': 0.0, 'payment': 0.0} for pid in self.ids}
        for res in data:
            pid = res['partner_id'][0]
            entry_type = res.get('type')
            total = res.get('total_sum', res.get('total', 0.0))
            if entry_type in mapping[pid]:
                mapping[pid][entry_type] = total

        for partner in self:
            debt = mapping[partner.id]['debt']
            paid = mapping[partner.id]['payment']
            partner.write({
                'x_ledger_total_debt': debt,
                'x_ledger_total_paid': paid,
                'x_ledger_balance': debt - paid,
            })

    @api.depends('ledger_entry_ids.date', 'ledger_entry_ids.type')
    def _compute_last_payment_date(self):
        payment_dates = self.env['ps.ledger.entry'].read_group(
            [('partner_id', 'in', self.ids), ('type', '=', 'payment')],
            ['date:max'], ['partner_id'], lazy=False,
        )
        date_map = {
            res['partner_id'][0]: res['date_max']
            for res in payment_dates
        }
        for partner in self:
            partner.x_last_payment_date = date_map.get(partner.id)

    def action_add_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ödeme Yap',
            'res_model': 'ps.ledger.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }

    def action_pay_full(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tümünü Öde',
            'res_model': 'ps.ledger.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_amount': self.x_ledger_balance,
            },
        }

    def action_print_ledger(self):
        self.ensure_one()
        entries = self.env['ps.ledger.entry'].search([
            ('partner_id', '=', self.id)
        ])
        action = self.env.ref(
            'veresiyedefteri.action_report_veresiye_receipt', False
        )
        if not action:
            raise UserError('Fiş raporu bulunamadı, modülü güncelleyin.')
        return action.report_action(entries)

    def action_save(self):
        self.ensure_one()
        action = self.env.ref('veresiyedefteri.action_ps_ledger_partner')
        return action.read()[0]

    def action_delete(self):
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

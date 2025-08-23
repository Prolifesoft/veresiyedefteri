from odoo import api, fields, models


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
            if entry_type in mapping[pid]:
                mapping[pid][entry_type] = res['total_sum']
        for partner in self:
            debt = mapping[partner.id]['debt']
            paid = mapping[partner.id]['payment']
            partner.write({
                'x_ledger_total_debt': debt,
                'x_ledger_total_paid': paid,
                'x_ledger_balance': debt - paid,
            })

    def action_add_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ödeme Yap',
            'res_model': 'ps.ledger.entry',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_type': 'payment',
            },
        }

    def action_print_ledger(self):
        self.ensure_one()
        entries = self.env['ps.ledger.entry'].search([
            ('partner_id', '=', self.id)
        ])
        return self.env.ref(
            'veresiyedefteri.action_report_ledger_receipt'
        ).report_action(entries)

    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_delete(self):
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}

from odoo import api, fields, models


class LedgerEntry(models.Model):
    _name = 'ps.ledger.entry'
    _description = 'Veresiye Kaydı'
    _order = 'date, id'

    name = fields.Char(
        string='Fiş', required=True, copy=False, readonly=True, default='/'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Müşteri',
        required=True,
        ondelete='cascade',
        index=True,
    )
    date = fields.Date(string='Tarih', default=fields.Date.context_today)
    type = fields.Selection(
        [('debt', 'Borç'), ('payment', 'Ödeme')],
        string='Tür',
        default='debt',
        required=True,
    )

    product_id = fields.Many2one('product.product', string='Ürün')
    description = fields.Char(string='Açıklama')
    quantity = fields.Float(string='Miktar', default=1.0)
    price_unit = fields.Monetary(
        string='Birim Fiyat',
        default=0.0,
        currency_field='currency_id',
    )
    tax_percent = fields.Float(string='KDV %', default=0.0)
    subtotal = fields.Monetary(
        string='Ara Toplam',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    tax_amount = fields.Monetary(
        string='KDV',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    total = fields.Monetary(
        string='Toplam',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    signed_total = fields.Monetary(
        string='İmzalı Toplam',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    paid_amount = fields.Monetary(
        string='Ödenen',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company
    )

    state = fields.Selection(
        [('draft', 'Taslak'), ('posted', 'Onaylanmış')],
        string='Durum',
        default='draft',
    )

    note = fields.Text(string='Not')

    payment_method = fields.Selection(
        [
            ('cash', 'Nakit'),
            ('card', 'Kart'),
            ('transfer', 'Havale/EFT'),
            ('pos', 'POS'),
            ('other', 'Diğer'),
        ],
        string='Ödeme Tipi',
    )
    pos_ref = fields.Char(string='POS Ref')
    installment_count = fields.Integer(string='Taksit', default=1)
    due_date = fields.Date(string='Vade Tarihi')
    grace_days = fields.Integer(string='Günlük Tolerans', default=0)
    interest_rate_daily = fields.Float(string='Günlük Faiz %')
    interest_compound = fields.Boolean(string='Bileşik Faiz')
    auto_interest_created = fields.Boolean(
        string='Faiz Otomatik', readonly=True
    )
    allocation_key = fields.Char(string='Dağıtım Notu', readonly=True)

    @api.depends('quantity', 'price_unit', 'tax_percent', 'type')
    def _compute_amounts(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit
            rec.tax_amount = rec.subtotal * rec.tax_percent / 100.0
            rec.total = rec.subtotal + rec.tax_amount
            rec.signed_total = (
                rec.total if rec.type == 'debt' else -abs(rec.total)
            )
            rec.paid_amount = rec.total if rec.type == 'payment' else 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price
            self.description = self.product_id.display_name

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == '/':
                rec.name = self.env['ir.sequence'].next_by_code(
                    'ps.ledger.entry'
                )
            rec.partner_id.recompute_ledger_totals()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.mapped('partner_id').recompute_ledger_totals()
        return res

    def unlink(self):
        partners = self.mapped('partner_id')
        res = super().unlink()
        partners.recompute_ledger_totals()
        return res

    def action_post(self):
        self.write({'state': 'posted'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def print_receipt(self):
        return self.env.ref(
            'veresiyedefteri.action_report_veresiye_receipt'
        ).report_action(self)

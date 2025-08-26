from odoo import models, fields, api
from odoo.tools import float_round


class VeresiyeLedger(models.Model):
    """Veresiye Fiş (Header)"""
    _name = 'veresiye.ledger'
    _description = 'Veresiye Defteri Fişi'
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Fiş Numarası',
        readonly=True,
        default='/',
        copy=False,
        help='Otomatik oluşturulan fiş numarası'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Müşteri',
        required=True,
        index=True,
        help='Veresiye borcu olan müşteri'
    )

    date = fields.Date(
        string='Tarih',
        required=True,
        default=fields.Date.today,
        index=True,
        help='Fiş tarihi'
    )

    state = fields.Selection([
        ('draft', 'Taslak'),
        ('posted', 'Onaylandı'),
        ('cancelled', 'İptal Edildi'),
    ], string='Durum', default='draft', help='Fiş durumu (sadece görsel)')

    line_ids = fields.One2many(
        'veresiye.ledger.line',
        'ledger_id',
        string='Satırlar',
        copy=True,
        help='Ürün satırları'
    )

    payment_ids = fields.One2many(
        'veresiye.payment',
        'ledger_id',
        string='Ödemeler',
        help='Bu fişe yapılan ödemeler'
    )

    amount_total = fields.Monetary(
        string='Toplam Tutar',
        compute='_compute_amounts',
        store=True,
        help='Fiş toplam tutarı'
    )

    amount_paid = fields.Monetary(
        string='Ödenen Tutar',
        compute='_compute_amounts',
        store=True,
        help='Yapılan toplam ödeme'
    )

    amount_due = fields.Monetary(
        string='Kalan Borç',
        compute='_compute_amounts',
        store=True,
        help='Kalan borç tutarı'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Para Birimi',
        default=lambda self: self.env.company.currency_id,
        help='Para birimi'
    )

    notes = fields.Text(
        string='Notlar',
        help='Ek açıklamalar'
    )

    def action_save_close(self):
        """Kaydedip partner formuna dön"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
        }

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('veresiye.ledger') or '/'
        return super().create(vals)

    @api.depends('line_ids.subtotal', 'payment_ids.amount')
    def _compute_amounts(self):
        for record in self:
            amount_total = sum(record.line_ids.mapped('subtotal'))
            amount_paid = sum(record.payment_ids.mapped('amount'))
            record.amount_total = amount_total
            record.amount_paid = amount_paid
            record.amount_due = max(0.0, amount_total - amount_paid)

    def action_confirm(self):
        self.write({'state': 'posted'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_add_payment(self):
        return {
            'name': 'Ödeme Yap',
            'type': 'ir.actions.act_window',
            'res_model': 'veresiye.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ledger_id': self.id,
                'default_amount': self.amount_due,
            }
        }

    def action_pay_all(self):
        if self.amount_due > 0:
            self.env['veresiye.payment'].create({
                'ledger_id': self.id,
                'date': fields.Date.today(),
                'amount': self.amount_due,
                'note': 'Tam ödeme'
            })
        return True


class VeresiyeLedgerLine(models.Model):
    """Veresiye Fiş Satırı"""
    _name = 'veresiye.ledger.line'
    _description = 'Veresiye Defteri Fiş Satırı'

    ledger_id = fields.Many2one(
        'veresiye.ledger',
        string='Fiş',
        required=True,
        ondelete='cascade',
        help='Bağlı olduğu fiş'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Ürün',
        index=True,
        help='Satılan ürün'
    )

    name = fields.Char(
        string='Açıklama',
        help='Ürün açıklaması'
    )

    quantity = fields.Float(
        string='Adet',
        default=1.0,
        required=True,
        help='Ürün adedi'
    )

    price_unit = fields.Monetary(
        string='Birim Fiyat',
        default=0.0,
        required=True,
        help='Birim satış fiyatı'
    )

    subtotal = fields.Monetary(
        string='Ara Toplam',
        compute='_compute_subtotal',
        store=True,
        help='Satır toplam tutarı'
    )

    currency_id = fields.Many2one(
        related='ledger_id.currency_id',
        string='Para Birimi',
        store=True
    )

    date = fields.Date(
        related='ledger_id.date',
        string='Tarih',
        store=True
    )

    partner_id = fields.Many2one(
        related='ledger_id.partner_id',
        string='Müşteri',
        store=True,
        index=True,
        readonly=True
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = float_round(
                line.quantity * line.price_unit,
                precision_rounding=line.currency_id.rounding or 0.01
            )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.list_price


class VeresiyePayment(models.Model):
    """Ödeme Kaydı"""
    _name = 'veresiye.payment'
    _description = 'Veresiye Ödeme Kaydı'
    _order = 'date desc, id desc'

    ledger_id = fields.Many2one(
        'veresiye.ledger',
        string='Fiş',
        required=True,
        ondelete='cascade',
        help='Ödemenin yapıldığı fiş'
    )

    date = fields.Date(
        string='Ödeme Tarihi',
        required=True,
        default=fields.Date.today,
        help='Ödeme tarihi'
    )

    amount = fields.Monetary(
        string='Ödeme Tutarı',
        required=True,
        help='Ödenen tutar'
    )

    note = fields.Char(
        string='Not',
        help='Ödeme notu'
    )

    currency_id = fields.Many2one(
        related='ledger_id.currency_id',
        string='Para Birimi',
        store=True
    )

    partner_id = fields.Many2one(
        related='ledger_id.partner_id',
        string='Müşteri',
        store=True,
        index=True,
        readonly=True
    )

    @api.constrains('amount')
    def _check_amount_positive(self):
        for payment in self:
            if payment.amount <= 0:
                payment.amount = abs(payment.amount) or 0.01


class ResPartner(models.Model):
    _inherit = 'res.partner'

    currency_id = fields.Many2one('res.currency', string='Para Birimi', related='company_id.currency_id', readonly=True)

    veresiye_count = fields.Integer(
        string='Veresiye Fiş Sayısı',
        compute='_compute_veresiye_stats'
    )

    veresiye_total = fields.Monetary(
        string='Toplam Borç',
        compute='_compute_veresiye_stats',
        currency_field='currency_id'
    )

    veresiye_paid = fields.Monetary(
        string='Ödenen',
        compute='_compute_veresiye_stats',
        currency_field='currency_id'
    )

    veresiye_due = fields.Monetary(
        string='Kalan Borç',
        compute='_compute_veresiye_stats',
        currency_field='currency_id'
    )

    ledger_ids = fields.One2many('veresiye.ledger', 'partner_id', string='Veresiye Fişleri')
    ledger_line_ids = fields.One2many('veresiye.ledger.line', 'partner_id', string='Veresiye Satırları')
    ledger_payment_ids = fields.One2many('veresiye.payment', 'partner_id', string='Veresiye Ödemeleri')

    def _compute_veresiye_stats(self):
        ledger_data = self.env['veresiye.ledger'].read_group(
            domain=[('partner_id', 'in', self.ids)],
            fields=['partner_id', 'amount_total', 'amount_paid', 'amount_due'],
            groupby=['partner_id']
        )
        partner_stats = {
            item['partner_id'][0]: {
                'count': item['partner_id_count'],
                'total': item['amount_total'],
                'paid': item['amount_paid'],
                'due': item['amount_due'],
            } for item in ledger_data
        }
        for partner in self:
            stats = partner_stats.get(partner.id, {})
            partner.veresiye_count = stats.get('count', 0)
            partner.veresiye_total = stats.get('total', 0.0)
            partner.veresiye_paid = stats.get('paid', 0.0)
            partner.veresiye_due = stats.get('due', 0.0)

    def action_view_veresiye(self):
        action = self.env.ref('prolifesoft_veresiye_defteri.action_veresiye_ledger').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_print_veresiye_list(self):
        return self.env.ref('prolifesoft_veresiye_defteri.action_report_veresiye_partner_list').report_action(self)

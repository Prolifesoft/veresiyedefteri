from odoo import api, fields, models
from odoo.exceptions import UserError


class VeresiyeDefteri(models.Model):
    _name = 'veresiye.defteri'
    _description = 'Veresiye Defteri'

    partner_id = fields.Many2one(
        'res.partner', string='Müşteri', required=True
    )
    phone = fields.Char(
        related='partner_id.phone', store=True, string='Telefon'
    )
    date = fields.Date(
        default=fields.Date.context_today, string='Tarih'
    )
    line_ids = fields.One2many(
        'veresiye.defteri.line', 'ledger_id', string='Satırlar'
    )
    total_amount = fields.Monetary(
        compute='_compute_totals',
        store=True,
        string='Borç Tutarı',
        currency_field='currency_id',
    )
    paid_amount = fields.Monetary(
        string='Ödenen',
        default=0.0,
        currency_field='currency_id',
    )
    last_payment_date = fields.Date(string='Ödeme Tarihi')
    remaining_amount = fields.Monetary(
        compute='_compute_remaining',
        store=True,
        string='Kalan',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id
    )
    last_entry_date = fields.Date(
        compute='_compute_last_entry', store=True, string='En Son Tarih'
    )

    @api.depends('line_ids.subtotal')
    def _compute_totals(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('subtotal'))

    @api.depends('total_amount', 'paid_amount')
    def _compute_remaining(self):
        for record in self:
            record.remaining_amount = record.total_amount - record.paid_amount

    @api.depends('line_ids.date')
    def _compute_last_entry(self):
        for record in self:
            dates = record.line_ids.mapped('date')
            record.last_entry_date = max(dates) if dates else False

    def print_receipt(self):
        action = self.env.ref(
            "veresiyedefteri.action_report_veresiye_receipt",
            raise_if_not_found=False,
        )
        if not action:
            raise UserError(
                "'veresiyedefteri.action_report_veresiye_receipt' not found"
            )
        return action.report_action(self)

    def action_open_payment_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ödeme Yap',
            'res_model': 'veresiye.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ledger_id': self.id},
        }

    def action_save_and_close(self):
        """Save the record and return to the tree view."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'veresiye.defteri',
            'view_mode': 'tree,form',
            'target': 'current',
        }


class VeresiyeDefteriLine(models.Model):
    _name = 'veresiye.defteri.line'
    _description = 'Veresiye Defteri Satırı'

    ledger_id = fields.Many2one(
        'veresiye.defteri', string='Defter', required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Ürün', required=True
    )
    quantity = fields.Float(string='Adet', default=1.0)
    name = fields.Char(string='Açıklama')
    price_unit = fields.Monetary(
        string='Fiyat',
        required=True,
        group_operator='sum',
        currency_field='currency_id',
    )
    subtotal = fields.Monetary(
        compute='_compute_subtotal',
        store=True,
        string='Ara Toplam',
        group_operator='sum',
        currency_field='currency_id',
    )
    date = fields.Date(
        default=fields.Date.context_today, string='Tarih'
    )
    currency_id = fields.Many2one(
        'res.currency', related='ledger_id.currency_id', store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the unit price when a product is selected."""
        for line in self:
            if line.product_id:
                line.price_unit = line.product_id.list_price

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

from odoo import api, fields, models
from odoo.exceptions import UserError


class VeresiyeDefteri(models.Model):
    _name = 'veresiye.defteri'
    _description = 'Veresiye Defteri'

    _sql_constraints = [
        (
            'partner_unique',
            'unique(partner_id)',
            'Her müşteri için yalnızca bir defter bulunabilir.',
        ),
    ]

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
        compute='_compute_paid',
        store=True,
        string='Ödenen',
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

    @api.depends('line_ids.paid_amount')
    def _compute_paid(self):
        for record in self:
            record.paid_amount = sum(record.line_ids.mapped('paid_amount'))

    @api.depends('line_ids.date')
    def _compute_last_entry(self):
        for record in self:
            dates = record.line_ids.mapped('date')
            record.last_entry_date = max(dates) if dates else False

    def print_receipt(self):
        """Print the ledger using the module's receipt report."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'veresiyedefteri.report_receipt'
        )
        if not report:
            raise UserError(
                "'veresiyedefteri.report_receipt' report not found",
            )
        return report.report_action(self)

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

    def action_pay_all(self):
        """Open payment wizard prefilled with remaining amount."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tümünü Öde',
            'res_model': 'veresiye.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ledger_id': self.id,
                'default_amount': self.remaining_amount,
            },
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
        'product.product', string='Ürün'
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
    paid_amount = fields.Monetary(
        string='Ödenen',
        group_operator='sum',
        currency_field='currency_id',
    )
    remaining_amount = fields.Monetary(
        compute='_compute_remaining_line',
        store=True,
        string='Kalan',
        group_operator='sum',
        currency_field='currency_id',
    )
    partner_id = fields.Many2one(
        'res.partner',
        related='ledger_id.partner_id',
        store=True,
        string='Müşteri',
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

    @api.depends('subtotal', 'paid_amount')
    def _compute_remaining_line(self):
        for line in self:
            line.remaining_amount = line.subtotal - line.paid_amount

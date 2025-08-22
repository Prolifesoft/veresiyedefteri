from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    veresiye_ledger_ids = fields.One2many(
        'veresiye.defteri', 'partner_id', string='Veresiye Defteri'
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True
    )
    veresiye_total_amount = fields.Monetary(
        compute='_compute_veresiye_amounts',
        currency_field='currency_id',
        string='Borç',
    )
    veresiye_paid_amount = fields.Monetary(
        compute='_compute_veresiye_amounts',
        currency_field='currency_id',
        string='Ödenen',
    )
    veresiye_remaining_amount = fields.Monetary(
        compute='_compute_veresiye_amounts',
        currency_field='currency_id',
        string='Kalan',
    )

    @api.depends(
        'veresiye_ledger_ids.total_amount',
        'veresiye_ledger_ids.paid_amount',
    )
    def _compute_veresiye_amounts(self):
        for partner in self:
            total = sum(partner.veresiye_ledger_ids.mapped('total_amount'))
            paid = sum(partner.veresiye_ledger_ids.mapped('paid_amount'))
            partner.veresiye_total_amount = total
            partner.veresiye_paid_amount = paid
            partner.veresiye_remaining_amount = total - paid

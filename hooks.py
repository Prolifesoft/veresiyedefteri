from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Create an alias for the legacy report ID after module installation."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        action = env.ref('veresiyedefteri.action_report_veresiye_receipt')
    except ValueError:
        return
    imd = env['ir.model.data']
    alias = imd.search([
        ('module', '=', 'veresiyedefteri'),
        ('name', '=', 'report_veresiye_receipt'),
    ], limit=1)
    vals = {
        'module': 'veresiyedefteri',
        'name': 'report_veresiye_receipt',
        'model': 'ir.actions.report',
        'res_id': action.id,
        'noupdate': True,
    }
    if alias:
        alias.write({'res_id': action.id})
    else:
        imd.create(vals)

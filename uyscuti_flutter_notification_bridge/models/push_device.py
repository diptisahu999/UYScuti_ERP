from odoo import models, fields, api

# register FCM token in this table
class PushDevice(models.Model):
    _name = 'push.device'
    _description = 'Push Notification Device'
    _order = 'id desc'

    name = fields.Char(string='Device Name', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade', index=True)
    fcm_token = fields.Char(string='FCM Token', required=True, index=True)
    platform = fields.Selection(
        [('android', 'Android'), ('ios', 'iOS')],
        required=True
    )
    active = fields.Boolean(default=True)

    @api.depends('user_id.name', 'platform')
    def _compute_name(self):
        for record in self:
            user_name = record.user_id.name if record.user_id else 'Unknown'
            record.name = f"{user_name} ({record.platform or 'device'})"

    _sql_constraints = [
        ('uniq_user_token', 'unique(user_id, fcm_token)', 'FCM token must be unique per user!')
    ]
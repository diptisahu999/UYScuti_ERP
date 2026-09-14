from odoo import models, fields

# register FCM token in this table
class PushDevice(models.Model):
    _name = 'push.device'
    _description = 'Push Notification Device'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade', index=True)
    fcm_token = fields.Char(string='FCM Token', required=True, index=True)
    platform = fields.Selection(
        [('android', 'Android'), ('ios', 'iOS')],
        required=True
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('uniq_user_token', 'unique(user_id, fcm_token)', 'FCM token must be unique per user!')
    ]
 
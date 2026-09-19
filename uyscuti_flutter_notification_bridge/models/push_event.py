from odoo import models, fields


class PushEvent(models.Model):
    _name = 'push.event'
    _description = 'Push Notification Event'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Event Name', required=True)
    code = fields.Char(string='Event Code', index=True)
    team_member_ids = fields.Many2many(
        'res.users',
        'push_event_team_member_rel',
        'event_id',
        'user_id',
        string='Team Members'
    )
    supervisor_ids = fields.Many2many(
        'res.users',
        'push_event_supervisor_rel',
        'event_id',
        'user_id',
        string='Supervisors'
    )
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

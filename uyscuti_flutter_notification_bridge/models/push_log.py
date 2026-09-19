from odoo import models, fields, api


class PushLog(models.Model):
    _name = 'push.log'
    _description = 'Push Notification Log'
    _order = 'date_sent desc, id desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        index=True
    )
    date_sent = fields.Datetime(
        string='Sent On',
        default=fields.Datetime.now,
        readonly=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        readonly=True,
        index=True
    )
    device_id = fields.Many2one(
        'push.device',
        string='Device',
        readonly=True
    )
    title = fields.Char(
        string='Title',
        required=True,
        readonly=True
    )
    body = fields.Text(
        string='Body',
        readonly=True
    )
    status = fields.Selection(
        [
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        string='Status',
        required=True,
        default='success',
        readonly=True,
        index=True
    )
    message_id = fields.Char(
        string='Firebase Message ID',
        readonly=True
    )
    error_message = fields.Text(
        string='Error Details',
        readonly=True
    )
    data_payload = fields.Text(
        string='Data Payload',
        readonly=True
    )

    @api.depends('title', 'user_id.name')
    def _compute_name(self):
        for record in self:
            user_name = record.user_id.name if record.user_id else 'Unknown'
            record.name = f"{record.title or 'Notification'} - {user_name}"

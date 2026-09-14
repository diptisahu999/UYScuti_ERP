from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    uyscuti_consumer_name = fields.Char(string='Consumer Name')
    uyscuti_consumer_id = fields.Char(string='Consumer Number')

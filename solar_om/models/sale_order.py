# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    solar_plant_id = fields.Many2one('solar.plant', string='Solar Plant', tracking=True)

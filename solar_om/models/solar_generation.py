# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SolarDailyGeneration(models.Model):
    _name = 'solar.daily.generation'
    _description = 'Daily Power Generation'
    _order = 'date desc, plant_id'

    plant_id = fields.Many2one('solar.plant', string='Solar Plant', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    energy_kwh = fields.Float(string='Energy KWH/ Day', required=True, digits=(16, 2))
    price_per_unit = fields.Float(string='Price /Unit (Rs.)', digits=(10, 2))
    discom_name = fields.Char(string='Discom Name')
    capacity_str = fields.Char(string='Capacity (MW)', compute='_compute_capacity_str', store=True)
    revenue = fields.Float(string='Revenue (Rs.)', compute='_compute_revenue', store=True, digits=(16, 2))

    _sql_constraints = [
        ('plant_date_unique', 'unique(plant_id, date)', 'Daily generation entry already exists for this plant on this date!')
    ]

    @api.onchange('plant_id')
    def _onchange_plant_id(self):
        if self.plant_id:
            self.price_per_unit = self.plant_id.price_per_unit
            self.discom_name = self.plant_id.discom_name

    @api.depends('energy_kwh', 'price_per_unit')
    def _compute_revenue(self):
        for record in self:
            record.revenue = record.energy_kwh * record.price_per_unit

    @api.depends('plant_id', 'plant_id.capacity')
    def _compute_capacity_str(self):
        for record in self:
            if record.plant_id:
                # Capacity in MW (capacity is stored in kW in the plant model)
                mw_capacity = record.plant_id.capacity / 1000.0
                record.capacity_str = _("%s MW") % round(mw_capacity, 2)
            else:
                record.capacity_str = ""
